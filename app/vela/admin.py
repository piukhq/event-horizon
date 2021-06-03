import wtforms

from flask_admin.model import typefmt  # type: ignore

from app.admin.model_views import AuthorisedModelView, BaseModelView
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
        "threshold",
        "campaign.earn_inc_is_tx_value",
        "increment",
        "increment_multiplier",
        "created_at",
        "updated_at",
    )
    column_labels = {
        "campaign.name": "Campaign",
        "campaign.earn_inc_is_tx_value": "Earn Inc. is Trans. Value?",
    }
    form_args = {
        "increment": {
            "validators": [validate_earn_rule_increment, wtforms.validators.NumberRange(min=1)],
        },
        "threshold": {"validators": [wtforms.validators.NumberRange(min=1)]},
        "increment_multiplier": {"validators": [wtforms.validators.NumberRange(min=1)]},
    }
    column_type_formatters = typefmt.BASE_FORMATTERS | {type(None): lambda view, value: "-"}


class RetailerRewardsAdmin(AuthorisedModelView):
    pass


class TransactionAdmin(AuthorisedModelView):
    pass
