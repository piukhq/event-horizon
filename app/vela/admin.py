import wtforms

from flask_admin.model import typefmt  # type: ignore
from wtforms.validators import DataRequired

from app.admin.model_views import BaseModelView
from app.vela.validators import validate_campaign_earn_inc_is_tx_value, validate_earn_rule_increment


class CampaignAdmin(BaseModelView):
    column_auto_select_related = True
    column_filters = ("retailerrewards.slug", "status")
    column_searchable_list = ("slug", "name")
    column_labels = dict(retailerrewards="Retailer")
    form_args = {
        "earn_inc_is_tx_value": {"validators": [validate_campaign_earn_inc_is_tx_value]},
    }
    # Be careful adding "inline_models = (EarnRule,)" here - the validate_earn_rule_increment
    # validator seemed to be bypassed in that view


class EarnRuleAdmin(BaseModelView):
    column_auto_select_related = True
    column_filters = ("campaign.name", "campaign.earn_inc_is_tx_value", "campaign.retailerrewards.slug")
    column_searchable_list = ("campaign.name",)
    column_list = (
        "campaign.name",
        "campaign.retailerrewards",
        "threshold",
        "campaign.earn_inc_is_tx_value",
        "increment",
        "increment_multiplier",
        "created_at",
        "updated_at",
    )
    column_labels = {
        "campaign.name": "Campaign",
        "campaign.retailerrewards": "Retailer",
        "campaign.earn_inc_is_tx_value": "Earn Inc. is Trans. Value?",
    }
    form_args = {
        "increment": {
            "validators": [validate_earn_rule_increment, wtforms.validators.NumberRange(min=1)],
            "description": (
                "How much the balance increases when an earn is triggered. Please enter the value "
                'multiplied by 100, e.g. for one stamp please enter "100" or for 15 points '
                'please enter "1500". Leave blank if the campaign is set to increment earns by the '
                "transaction value."
            ),
        },
        "threshold": {
            "validators": [wtforms.validators.NumberRange(min=1)],
            "description": (
                "Monetary value of a transaction required to trigger an earn. Please enter money value "
                'multiplied by 100, e.g. for £10.50, please enter "1050".'
            ),
        },
        "increment_multiplier": {"validators": [wtforms.validators.NumberRange(min=0)]},
    }
    column_type_formatters = typefmt.BASE_FORMATTERS | {type(None): lambda view, value: "-"}


class RewardRuleAdmin(BaseModelView):
    column_auto_select_related = True
    column_filters = ("campaign.name", "campaign.retailerrewards.slug")
    column_searchable_list = ("campaign.name",)
    column_list = (
        "campaign.name",
        "campaign.retailerrewards",
        "reward_goal",
        "voucher_type_slug",
        "created_at",
        "updated_at",
    )
    column_labels = {
        "campaign.name": "Campaign",
        "campaign.retailerrewards": "Retailer",
    }
    form_args = {
        "reward_goal": {
            "validators": [wtforms.validators.NumberRange(min=1)],
            "description": (
                "Balance goal used to calculate if a voucher should be issued. "
                "This is a money value * 100, e.g. a reward goal of £10.50 should be 1050, "
                "and a reward goal of 8 stamps would be 800."
            ),
        },
        "voucher_type_slug": {
            "validators": [DataRequired(message="Slug is required"), wtforms.validators.Length(min=1, max=32)],
            "description": ("Used to determine what voucher on the till the Account holder will be allocated."),
        },
    }
    column_type_formatters = typefmt.BASE_FORMATTERS | {type(None): lambda view, value: "-"}


class RetailerRewardsAdmin(BaseModelView):
    pass


class TransactionAdmin(BaseModelView):
    column_filters = ("retailerrewards.slug",)
    column_searchable_list = ("transaction_id",)


class ProcessedTransactionAdmin(BaseModelView):
    column_filters = ("retailerrewards.slug",)
    column_searchable_list = ("transaction_id",)


class RewardAdjustmentAdmin(BaseModelView):
    column_exclude_list = ("response_data",)
    column_filters = ("campaign_slug", "status")
    column_searchable_list = ("processed_transaction_id",)
    column_labels = dict(processedtransaction="Processed Transaction")
