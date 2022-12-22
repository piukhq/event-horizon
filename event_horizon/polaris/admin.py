import logging

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Generator, Type

import requests
import wtforms
import yaml

from flask import Markup, flash, redirect, request, session, url_for
from flask_admin import expose
from flask_admin.actions import action
from retry_tasks_lib.admin.views import (
    RetryTaskAdminBase,
    TaskTypeAdminBase,
    TaskTypeKeyAdminBase,
    TaskTypeKeyValueAdminBase,
)
from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from wtforms.validators import DataRequired, InputRequired, Optional

from event_horizon import settings
from event_horizon.activity_utils.enums import ActivityType
from event_horizon.activity_utils.tasks import sync_send_activity
from event_horizon.admin.custom_formatters import format_json_field
from event_horizon.admin.model_views import BaseModelView, CanDeleteModelView
from event_horizon.helpers import check_activate_campaign_for_retailer, sync_activate_retailer, sync_retailer_insert
from event_horizon.hubble.account_activity_rtbf import anonymise_account_activities
from event_horizon.polaris.custom_actions import DeleteRetailerAction
from event_horizon.polaris.db import AccountHolder, RetailerConfig
from event_horizon.polaris.utils import generate_payloads_for_delete_account_holder_activity
from event_horizon.polaris.validators import validate_balance_reset_advanced_warning_days

from .db import AccountHolderCampaignBalance, AccountHolderPendingReward, AccountHolderProfile, AccountHolderReward
from .validators import validate_account_number_prefix, validate_marketing_config, validate_retailer_config

if TYPE_CHECKING:
    from jinja2.runtime import Context
    from werkzeug.wrappers import Response


# pylint: disable=unused-argument
def _account_holder_repr(
    v: Type[BaseModelView],
    c: "Context",
    model: AccountHolderProfile | AccountHolderReward | AccountHolderCampaignBalance,
    p: str,
) -> str:

    return Markup(
        (
            "<strong><a href='{}'>ID:</a></strong>&nbsp;{}<br />"
            "<strong>Email:</strong>&nbsp;{}<br />"
            "<strong>UUID:</strong>&nbsp;{}"
        ).format(
            url_for(f"{settings.POLARIS_ENDPOINT_PREFIX}/account-holders.details_view", id=model.account_holder_id),
            model.account_holder_id,
            model.accountholder.email,
            model.accountholder.account_holder_uuid,
        )
    )


# pylint: disable=unused-argument
def _account_holder_export_repr(
    v: Type[BaseModelView],
    c: "Context",
    model: AccountHolderReward | AccountHolderPendingReward,
    p: str,
) -> str:
    return model.accountholder.account_holder_uuid


class AccountHolderAdmin(BaseModelView):
    can_create = False
    column_filters = (
        "retailerconfig.slug",
        "retailerconfig.name",
        "retailerconfig.id",
        "status",
        "opt_out_token",
        "created_at",
    )
    form_excluded_columns = (
        "created_at",
        "updated_at",
        "status",
        "accountholdercampaignbalance_collection",
        "accountholderprofile_collection",
        "accountholderreward_collection",
        "accountholdermarketingpreference_collection",
        "balance_adjustment_collection",
    )
    column_labels = dict(retailerconfig="Retailer")
    column_searchable_list = ("id", "email", "account_holder_uuid", "account_number")
    form_widget_args = {
        "opt_out_token": {"readonly": True},
    }

    @action(
        "delete-account-holder",
        "Delete",
        "The selected account holders' retailer must be in a TEST state. "
        "This action is not reversible, are you sure you wish to proceed?",
    )
    def delete_account_holder(self, ids: list[str]) -> None:
        activity_payloads: Generator[dict, None, None] | None = None
        account_holders_ids = [int(ah_id) for ah_id in ids]
        account_holders = (
            self.session.execute(
                select(AccountHolder)
                .options(joinedload(AccountHolder.retailerconfig))
                .where(AccountHolder.id.in_(account_holders_ids))
            )
            .scalars()
            .all()
        )
        if any(account_holder.retailerconfig.status != "TEST" for account_holder in account_holders):
            flash("This action is allowed only for account holders that belong to a TEST retailer.", category="error")
            return
        activity_payloads = generate_payloads_for_delete_account_holder_activity(account_holders, self.sso_username)

        # delete() queries make use of the ondelete="CASCADE" param on the ForeignKey.
        # Fetching the object and calling session.delete(obj) makes use of the
        # cascade="all, delete-orphan" param on the relationship.
        # The first type is database side the second orm side.
        # We are reflecting the db so we need to use the first method to ensure CASCADE is respected.
        # By default Flask Admin's delete action uses the second method which would leave orphans in our case.
        res = self.session.execute(AccountHolder.__table__.delete().where(AccountHolder.id.in_(account_holders_ids)))
        sync_send_activity(activity_payloads, routing_key=ActivityType.ACCOUNT_DELETED.value)
        self.session.commit()

        flash(f"Deleted {res.rowcount} Account Holders.")

    @action(
        "anonymise-account-holder",
        "Anonymise account holder (RTBF)",
        "This action is not reversible. Are you sure you wish to proceed?",
    )
    def anonymise_user(self, account_holder_ids: list[str]) -> None:
        if len(account_holder_ids) != 1:
            flash("This action must be completed for account holders one at a time", category="error")
            return
        try:
            res = self.session.execute(
                select(
                    RetailerConfig.slug,
                    AccountHolder,
                )
                .join(RetailerConfig)
                .where(AccountHolder.id == account_holder_ids[0])
            ).first()
            retailer_slug, account_holder = res
            if account_holder.status == "INACTIVE":
                flash("Account holder is INACTIVE", category="error")
            else:
                resp = requests.patch(
                    f"{settings.POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder.account_holder_uuid}/status",
                    headers={"Authorization": f"token {settings.POLARIS_AUTH_TOKEN}"},
                    json={"status": "inactive"},
                    timeout=settings.REQUEST_TIMEOUT,
                )
                if 200 <= resp.status_code <= 204:
                    flash("Account Holder successfully changed to INACTIVE")
                    anonymise_account_activities(
                        retailer_slug=retailer_slug,
                        account_holder_uuid=account_holder.account_holder_uuid,
                        account_holder_email=account_holder.email,
                    )
                else:
                    self._flash_error_response(resp.json())

        except Exception as ex:
            msg = "Error: no response received."
            flash(msg, category="error")
            logging.exception(msg, exc_info=ex)


class AccountHolderProfileAdmin(BaseModelView):
    can_create = False
    column_searchable_list = ("accountholder.id", "accountholder.email", "accountholder.account_holder_uuid")
    column_labels = dict(accountholder="Account Holder")
    column_formatters = dict(accountholder=_account_holder_repr)
    column_default_sort = ("accountholder.created_at", True)


class AccountHolderRewardAdmin(BaseModelView):
    can_create = False
    column_searchable_list = (
        "accountholder.id",
        "accountholder.email",
        "accountholder.account_holder_uuid",
        "code",
    )
    column_labels = dict(accountholder="Account Holder")
    column_filters = ("accountholder.retailerconfig.slug", "status", "reward_slug", "campaign_slug", "issued_date")
    column_formatters = dict(accountholder=_account_holder_repr)
    form_widget_args = {
        "reward_id": {"readonly": True},
        "reward_code": {"readonly": True},
        "accountholder": {"disabled": True},
    }
    column_formatters_export = dict(accountholder=_account_holder_export_repr)
    column_export_exclude_list = ["idempotency_token", "code"]
    can_export = True

    def is_accessible(self) -> bool:
        if not self.is_read_write_user:
            return False

        return super().is_accessible()

    def inaccessible_callback(self, name: str, **kwargs: dict | None) -> "Response":
        if self.is_read_write_user:
            return redirect(url_for(f"{settings.POLARIS_ENDPOINT_PREFIX}/account-holder-rewards.index_view"))

        if self.is_read_only_user:
            return redirect(url_for(f"{settings.POLARIS_ENDPOINT_PREFIX}/ro-account-holder-rewards.index_view"))

        return super().inaccessible_callback(name, **kwargs)


class ReadOnlyAccountHolderRewardAdmin(AccountHolderRewardAdmin):
    column_details_exclude_list = ["code", "associated_url"]
    column_exclude_list = ["code", "associated_url"]
    column_export_exclude_list = AccountHolderRewardAdmin.column_export_exclude_list + ["associated_url"]

    def is_accessible(self) -> bool:
        if self.is_read_write_user:
            return False
        res = super(AccountHolderRewardAdmin, self).is_accessible()
        return res


class AccountHolderPendingRewardAdmin(BaseModelView):
    can_create = False
    column_searchable_list = (
        "accountholder.id",
        "accountholder.email",
        "accountholder.account_holder_uuid",
    )
    column_labels = dict(accountholder="Account Holder", id="Pending Reward id")
    column_filters = ("accountholder.retailerconfig.slug", "campaign_slug", "created_date", "conversion_date")
    column_formatters = dict(accountholder=_account_holder_repr)
    form_widget_args = {"accountholder": {"disabled": True}}
    column_export_exclude_list = ["idempotency_token"]
    column_export_list = [
        "accountholder.account_holder_uuid",
        "created_at",
        "updated_at",
        "id",
        "created_date",
        "conversion_date",
        "value",
        "campaign_slug",
        "reward_slug",
        "retailer_slug",
        "total_cost_to_user",
        "count",
    ]
    can_export = True


class RetailerConfigAdmin(BaseModelView):
    column_filters = ("created_at", "status")
    column_searchable_list = ("id", "slug", "name")
    column_labels = {"profile_config": "Enrolment Config"}
    column_exclude_list = ("profile_config", "marketing_preference_config")
    form_create_rules = (
        "name",
        "slug",
        "account_number_prefix",
        "profile_config",
        "marketing_preference_config",
        "loyalty_name",
        "balance_lifespan",
        "balance_reset_advanced_warning_days",
        "status",
    )
    column_details_list = ("created_at", "updated_at") + form_create_rules
    form_excluded_columns = ("account_holder_collection",)
    form_widget_args = {
        "account_number_length": {"disabled": True},
        "profile_config": {"rows": 20},
        "marketing_preference_config": {"rows": 10},
        "status": {"disabled": True},
    }
    form_edit_rules = (
        "name",
        "profile_config",
        "marketing_preference_config",
        "loyalty_name",
        "balance_lifespan",
        "balance_reset_advanced_warning_days",
    )

    profile_config_placeholder = """
email:
  required: true
  label: Email address
first_name:
  required: true
  label: Forename
last_name:
  required: true
  label: Surname
""".strip()

    marketing_config_placeholder = """
marketing_pref:
  type: boolean
  label: Would you like to receive marketing?
""".strip()

    form_args = {
        "profile_config": {
            "label": "Enrolment Field Configuration",
            "validators": [
                DataRequired(message="Configuration is required"),
                validate_retailer_config,
            ],
            "render_kw": {"placeholder": profile_config_placeholder},
            "description": "Configuration in YAML format",
        },
        "marketing_preference_config": {
            "label": "Marketing Preferences Configuration",
            "validators": [validate_marketing_config],
            "render_kw": {"placeholder": marketing_config_placeholder},
            "description": "Optional configuration in YAML format",
        },
        "name": {"validators": [DataRequired(message="Name is required")]},
        "slug": {"validators": [DataRequired(message="Slug is required")]},
        "account_number_prefix": {
            "validators": [
                DataRequired("Account number prefix is required"),
                validate_account_number_prefix,
            ]
        },
        "status": {"default": "TEST", "validators": [Optional()]},
        "balance_lifespan": {
            "description": "Provide a value >0 (in days) if balances are to be periodically reset based on "
            "this value. 0 implies balances will not be reset.",
            "validators": [wtforms.validators.NumberRange(min=0), InputRequired()],
        },
        "balance_reset_advanced_warning_days": {
            "description": "Number of days ahead of account holder balance reset "
            "date that a balance reset nudge should be sent.",
            "validators": [wtforms.validators.NumberRange(min=0), InputRequired()],
        },
    }
    column_formatters = dict(
        profile_config=lambda v, c, model, p: Markup("<pre>") + Markup.escape(model.profile_config) + Markup("</pre>"),
        marketing_preference_config=lambda v, c, model, p: Markup("<pre>")
        + Markup.escape(model.marketing_preference_config)
        + Markup("</pre>"),
    )

    def after_model_change(self, form: wtforms.Form, model: "RetailerConfig", is_created: bool) -> None:
        if is_created:
            try:
                sync_retailer_insert(model.slug, model.status)
            except Exception as ex:
                msg = "Failed to create retailer in Vela or Carina table"
                flash(msg, category="error")
                logging.exception(msg, exc_info=ex)
            else:
                # Synchronously send activity for retailer creation after successful creation
                # across polaris, vela and carina db
                sync_send_activity(
                    ActivityType.get_retailer_created_activity_data(
                        sso_username=self.sso_username,
                        activity_datetime=model.created_at,
                        status=model.status,
                        retailer_name=model.name,
                        retailer_slug=model.slug,
                        account_number_prefix=model.account_number_prefix,
                        enrolment_config=yaml.safe_load(model.profile_config),
                        marketing_preferences=yaml.safe_load(model.marketing_preference_config),
                        loyalty_name=model.loyalty_name,
                        balance_lifespan=model.balance_lifespan,
                        balance_reset_advanced_warning_days=model.balance_reset_advanced_warning_days,
                    ),
                    routing_key=ActivityType.RETAILER_CREATED.value,
                )
        else:
            new_values: dict = {}
            original_values: dict = {}

            for field in form:
                if (new_val := getattr(model, field.name)) != field.object_data:
                    new_values[field.name] = new_val
                    original_values[field.name] = field.object_data
            if new_values:
                sync_send_activity(
                    ActivityType.get_retailer_update_activity_data(
                        sso_username=self.sso_username,
                        activity_datetime=datetime.now(tz=timezone.utc),
                        retailer_name=model.name,
                        retailer_slug=model.slug,
                        new_values=new_values,
                        original_values=original_values,
                    ),
                    routing_key=ActivityType.RETAILER_CHANGED.value,
                )

    def on_model_change(self, form: wtforms.Form, model: "RetailerConfig", is_created: bool) -> None:
        validate_balance_reset_advanced_warning_days(form, retailer_status=model.status)
        if not is_created and form.balance_lifespan.object_data == 0 and form.balance_lifespan.data > 0:
            reset_date = (datetime.now(tz=timezone.utc) + timedelta(days=model.balance_lifespan)).date()
            stmt = (
                update(AccountHolderCampaignBalance)
                .where(
                    AccountHolderCampaignBalance.account_holder_id == AccountHolder.id,
                    AccountHolder.retailer_id == model.id,
                )
                .values(reset_date=reset_date)
                .execution_options(synchronize_session=False)
            )
            self.session.execute(stmt)

        return super().on_model_change(form, model, is_created)

    def _get_retailer_by_id(self, retailer_id: int) -> RetailerConfig:
        return self.session.execute(select(RetailerConfig).where(RetailerConfig.id == retailer_id)).scalar_one()

    @action(
        "activate retailer",
        "Activate",
        "Selected test retailer must have an activate campaign. Are you sure you want to proceed?",
    )
    def activate_retailer(self, ids: list[str]) -> None:
        if len(ids) > 1:
            flash("Cannot activate more than one retailer at once", category="error")
        else:
            retailer_id = int(ids[0])
            retailer = self._get_retailer_by_id(retailer_id)
            original_status = retailer.status
            if original_status == "TEST":
                if check_activate_campaign_for_retailer(retailer.slug):
                    try:
                        # Vela and carina retailer update
                        sync_activate_retailer(retailer_id)
                        # Polaris retailer update
                        retailer.status = "ACTIVE"
                        self.session.commit()
                        flash("Update retailer status successfully")
                    except Exception:
                        self.session.rollback()
                        flash("Failed to update retailer", category="error")
                    else:
                        self.session.refresh(retailer)
                        sync_send_activity(
                            ActivityType.get_retailer_status_update_activity_data(
                                sso_username=self.sso_username,
                                activity_datetime=retailer.updated_at,
                                new_status=retailer.status,
                                original_status=original_status,
                                retailer_name=retailer.name,
                                retailer_slug=retailer.slug,
                            ),
                            routing_key=ActivityType.RETAILER_STATUS.value,
                        )
                else:
                    flash("Retailer has no active campaign", category="error")
            else:
                flash("Retailer in incorrect state for activation", category="error")

    @expose("/custom-actions/delete-retailer", methods=["GET", "POST"])
    def delete_retailer(self) -> "Response":
        if not self.user_info or self.user_session_expired:
            return redirect(url_for("auth_views.login"))

        retailers_index_uri = url_for("polaris/retailers-config.index_view")
        if not self.can_edit:
            return redirect(retailers_index_uri)

        del_ret_action = DeleteRetailerAction()

        if "action_context" in session and request.method == "POST":
            del_ret_action.session_data = session["action_context"]

        else:
            if error_msg := del_ret_action.validate_selected_ids(request.args.to_dict(flat=False).get("ids", [])):
                flash(error_msg, category="error")
                return redirect(retailers_index_uri)

            session["action_context"] = del_ret_action.session_data.to_base64_str()

        if del_ret_action.form.validate_on_submit():
            del session["action_context"]
            del_ret_action.delete_retailer()

            original_values: dict = {
                "status": del_ret_action.session_data.retailer_status,
                "name": del_ret_action.session_data.retailer_name,
                "slug": del_ret_action.session_data.retailer_slug,
                "loyalty_name": del_ret_action.session_data.loyalty_name,
            }

            sync_send_activity(
                ActivityType.get_retailer_deletion_activity_data(
                    sso_username=self.sso_username,
                    activity_datetime=datetime.now(tz=timezone.utc),
                    retailer_name=del_ret_action.session_data.retailer_name,
                    retailer_slug=del_ret_action.session_data.retailer_slug,
                    original_values=original_values,
                ),
                routing_key=ActivityType.RETAILER_DELETED.value,
            )
            return redirect(retailers_index_uri)

        return self.render(
            "eh_delete_retailer_action.html",
            retailer_name=del_ret_action.session_data.retailer_name,
            account_holders_count=del_ret_action.affected_account_holders_count(),
            rewards_count=del_ret_action.affected_rewards_count(),
            campaign_slugs=del_ret_action.affected_campaigns_slugs(),
            form=del_ret_action.form,
        )

    @action(
        "delete-retailer",
        "Delete",
        "Only one non active retailer allowed for this action. This action is unreversible, Proceed?",
    )
    def delete_retailer_action(self, ids: list[str]) -> "Response":
        return redirect(url_for("polaris/retailers-config.delete_retailer", ids=ids))


class AccountHolderCampaignBalanceAdmin(BaseModelView):
    can_create = False
    column_searchable_list = ("accountholder.id", "accountholder.email", "accountholder.account_holder_uuid")
    column_labels = dict(accountholder="Account Holder")
    column_filters = ("accountholder.retailerconfig.slug", "campaign_slug")
    column_formatters = dict(accountholder=_account_holder_repr)
    form_widget_args = {"accountholder": {"disabled": True}}


class AccountHolderMarketingPreferenceAdmin(BaseModelView):
    column_searchable_list = ("accountholder.id", "accountholder.email", "accountholder.account_holder_uuid")
    column_filters = ("key_name", "value_type")
    column_labels = {"accountholder": "Account Holder"}
    column_formatters = {"accountholder": _account_holder_repr}
    column_default_sort = ("accountholder.created_at", True)


class RetryTaskAdmin(BaseModelView, RetryTaskAdminBase):
    endpoint_prefix = settings.POLARIS_ENDPOINT_PREFIX
    redis = settings.redis


class TaskTypeAdmin(BaseModelView, TaskTypeAdminBase):
    pass


class TaskTypeKeyAdmin(BaseModelView, TaskTypeKeyAdminBase):
    pass


class TaskTypeKeyValueAdmin(BaseModelView, TaskTypeKeyValueAdminBase):
    pass


class EmailTemplateAdmin(CanDeleteModelView):
    column_list = ("template_id", "type", "emailtemplatekey_collection", "retailerconfig", "created_at", "updated_at")
    column_searchable_list = ("template_id",)
    column_filters = (
        "type",
        "emailtemplatekey_collection.name",
        "retailerconfig.slug",
        "retailerconfig.name",
        "retailerconfig.id",
    )
    column_details_list = ("template_id", "type", "emailtemplatekey_collection", "retailerconfig")
    form_excluded_columns = (
        "emailtemplaterequiredkey_collection",
        "created_at",
        "updated_at",
    )
    column_labels = dict(emailtemplatekey_collection="Template Key", retailerconfig="Retailer")


class EmailTemplateKeyAdmin(BaseModelView):
    can_view_details = True
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("name", "display_name", "description")
    form_excluded_columns = (
        "template",
        "emailtemplaterequiredkey_collection",
        "emailtemplate_collection",
        "created_at",
        "updated_at",
    )
    column_labels = dict(display_name="Display Name")


class AccountHolderTransactionHistoryAdmin(BaseModelView):
    can_create = False
    can_edit = False
    column_searchable_list = (
        "accountholder.id",
        "accountholder.email",
        "accountholder.account_holder_uuid",
        "transaction_id",
    )
    column_filters = ("datetime", "location_name")
    column_labels = {"accountholder": "Account Holder"}
    column_formatters = {
        "accountholder": _account_holder_repr,
        "earned": format_json_field,
    }
