import json

from flask import Markup
from flask_admin.model.form import InlineFormAdmin
from wtforms.validators import DataRequired

from app.admin.model_views import BaseModelView

from .db import AccountHolderProfile
from .validators import validate_account_number_prefix, validate_retailer_config


class AccountHolderProfileForm(InlineFormAdmin):
    form_label = "Profile"


class AccountHolderAdmin(BaseModelView):
    column_display_pk = True
    column_filters = ("retailerconfig.slug", "retailerconfig.name", "retailerconfig.id", "status")
    column_exclude_list = ("current_balances",)
    column_labels = dict(retailerconfig="Retailer")
    column_searchable_list = ("email", "id")
    inline_models = (AccountHolderProfileForm(AccountHolderProfile),)
    can_delete = True


class AccountHolderProfileAdmin(BaseModelView):
    column_searchable_list = ("accountholder.id", "accountholder.email")
    column_labels = dict(accountholder="Account Holder")
    column_formatters = dict(
        accountholder=lambda v, c, model, p: Markup.escape(model.accountholder.email)
        + Markup("<br />" + f"({model.accountholder.id})")
    )
    column_default_sort = ("accountholder.created_at", True)


class AccountHolderActivationAdmin(BaseModelView):
    column_searchable_list = ("accountholder.id", "accountholder.email")
    column_labels = dict(accountholder="Account Holder", url="URL")
    column_filters = ("status", "next_attempt_time", "updated_at", "accountholder.retailerconfig.slug")
    column_exclude_list = ("callback_url", "response_data")
    column_formatters = dict(
        accountholder=lambda v, c, model, p: Markup.escape(model.accountholder.email)
        + Markup("<br />" + f"({model.accountholder.id})"),
        response_data=lambda v, c, model, p: Markup("<pre>")
        + Markup.escape(json.dumps(model.response_data, indent=4, sort_keys=True))
        + Markup("</pre>"),
    )
    form_edit_rules = ("callback_url",)


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
