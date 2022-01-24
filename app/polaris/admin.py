from typing import TYPE_CHECKING, Type, Union

from flask import Markup, url_for
from retry_tasks_lib.admin.views import (
    RetryTaskAdminBase,
    TaskTypeAdminBase,
    TaskTypeKeyAdminBase,
    TaskTypeKeyValueAdminBase,
)
from wtforms.validators import DataRequired

from app import settings
from app.admin.model_views import BaseModelView

from .validators import validate_account_number_prefix, validate_marketing_config, validate_retailer_config

if TYPE_CHECKING:
    from jinja2.runtime import Context

    from .db import AccountHolderCampaignBalance, AccountHolderProfile, AccountHolderReward


def _account_holder_repr(
    v: Type[BaseModelView],
    c: "Context",
    model: Union["AccountHolderProfile", "AccountHolderReward", "AccountHolderCampaignBalance"],
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


class AccountHolderAdmin(BaseModelView):
    can_delete = True
    column_filters = ("retailerconfig.slug", "retailerconfig.name", "retailerconfig.id", "status", "opt_out_token")
    form_excluded_columns = (
        "created_at",
        "updated_at",
        "accountholdercampaignbalance_collection",
        "accountholderprofile_collection",
        "accountholderreward_collection",
        "accountholdermarketingpreference_collection",
        "balance_adjustment_collection",
    )
    column_labels = dict(retailerconfig="Retailer")
    column_searchable_list = ("id", "email", "account_holder_uuid")
    form_widget_args = {
        "opt_out_token": {"readonly": True},
    }


class AccountHolderProfileAdmin(BaseModelView):
    column_searchable_list = ("accountholder.id", "accountholder.email", "accountholder.account_holder_uuid")
    column_labels = dict(accountholder="Account Holder")
    column_formatters = dict(accountholder=_account_holder_repr)
    column_default_sort = ("accountholder.created_at", True)


class AccountHolderRewardAdmin(BaseModelView):
    can_create = False
    column_searchable_list = ("accountholder.id", "accountholder.email", "accountholder.account_holder_uuid")
    column_labels = dict(accountholder="Account Holder")
    column_filters = ("accountholder.retailerconfig.slug", "status", "reward_slug")
    column_formatters = dict(accountholder=_account_holder_repr)
    form_widget_args = {
        "reward_id": {"readonly": True},
        "reward_code": {"readonly": True},
        "accountholder": {"disabled": True},
    }


class RetailerConfigAdmin(BaseModelView):
    column_filters = ("created_at",)
    column_searchable_list = ("id", "slug", "name")
    column_exclude_list = ("profile_config", "marketing_preference_config")
    form_create_rules = ("name", "slug", "account_number_prefix", "profile_config", "marketing_preference_config")
    form_excluded_columns = ("account_holder_collection",)
    form_widget_args = {
        "account_number_length": {"disabled": True},
        "profile_config": {"rows": 20},
        "marketing_preference_config": {"rows": 10},
    }
    form_edit_rules = ("name", "profile_config", "marketing_preference_config")

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
            "label": "Profile Field Configuration",
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
    }
    column_formatters = dict(
        config=lambda v, c, model, p: Markup("<pre>") + Markup.escape(model.config) + Markup("</pre>")
    )


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
