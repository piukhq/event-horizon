from typing import TYPE_CHECKING, Type, Union

from flask import Markup, url_for
from flask_admin.model.form import InlineFormAdmin
from retry_tasks_lib.admin.views import (
    RetryTaskAdminBase,
    TaskTypeAdminBase,
    TaskTypeKeyAdminBase,
    TaskTypeKeyValueAdminBase,
)
from wtforms.validators import DataRequired

from app import settings
from app.admin.model_views import BaseModelView

from .db import AccountHolderProfile
from .validators import validate_account_number_prefix, validate_retailer_config

if TYPE_CHECKING:
    from jinja2.runtime import Context

    from .db import AccountHolderCampaignBalance, AccountHolderVoucher


def _account_holder_repr(
    v: Type[BaseModelView],
    c: "Context",
    model: Union[AccountHolderProfile, "AccountHolderVoucher", "AccountHolderCampaignBalance"],
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


class AccountHolderProfileForm(InlineFormAdmin):
    form_label = "Profile"


class AccountHolderAdmin(BaseModelView):
    column_display_pk = True
    column_filters = ("retailerconfig.slug", "retailerconfig.name", "retailerconfig.id", "status")
    column_exclude_list = ("current_balances",)
    column_labels = dict(retailerconfig="Retailer")
    column_searchable_list = ("id", "email", "account_holder_uuid")
    inline_models = (AccountHolderProfileForm(AccountHolderProfile),)
    can_delete = True


class AccountHolderProfileAdmin(BaseModelView):
    column_searchable_list = ("accountholder.id", "accountholder.email", "accountholder.account_holder_uuid")
    column_labels = dict(accountholder="Account Holder")
    column_formatters = dict(accountholder=_account_holder_repr)
    column_default_sort = ("accountholder.created_at", True)


class AccountHolderVoucherAdmin(BaseModelView):
    can_create = False
    column_searchable_list = ("accountholder.id", "accountholder.email", "accountholder.account_holder_uuid")
    column_labels = dict(accountholder="Account Holder")
    column_filters = ("accountholder.retailerconfig.slug", "status", "voucher_type_slug")
    column_formatters = dict(accountholder=_account_holder_repr)
    form_widget_args = {
        "voucher_id": {"readonly": True},
        "voucher_code": {"readonly": True},
        "accountholder": {"disabled": True},
    }


class RetailerConfigAdmin(BaseModelView):
    column_filters = ("created_at",)
    column_searchable_list = ("id", "slug", "name")
    column_exclude_list = ("config",)
    form_create_rules = ("name", "slug", "account_number_prefix", "config")
    form_excluded_columns = ("account_holder_collection",)
    form_widget_args = {
        "account_number_length": {"disabled": True},
        "config": {"rows": 20},
    }
    form_edit_rules = ("name", "config")

    config_placeholder = """
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

    form_args = {
        "config": {
            "label": "Profile Field Configuration",
            "validators": [
                DataRequired(message="Configuration is required"),
                validate_retailer_config,
            ],
            "render_kw": {"placeholder": config_placeholder},
            "description": "Configuration in YAML format",
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


class RetryTaskAdmin(BaseModelView, RetryTaskAdminBase):
    endpoint_prefix = settings.POLARIS_ENDPOINT_PREFIX
    redis = settings.redis


class TaskTypeAdmin(BaseModelView, TaskTypeAdminBase):
    pass


class TaskTypeKeyAdmin(BaseModelView, TaskTypeKeyAdminBase):
    pass


class TaskTypeKeyValueAdmin(BaseModelView, TaskTypeKeyValueAdminBase):
    pass
