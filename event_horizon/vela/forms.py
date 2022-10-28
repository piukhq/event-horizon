from flask_wtf import FlaskForm
from wtforms import BooleanField, FloatField, SelectField, validators

from event_horizon.vela.enums import PendingRewardChoices


class EndCampaignActionForm(FlaskForm):
    handle_pending_rewards = SelectField(
        label="Pending Reward", coerce=PendingRewardChoices, render_kw={"class": "form-control"}
    )
    transfer_balance = BooleanField(label="Transfer balance?", render_kw={"class": "form-check-input"})
    convert_rate = FloatField(
        label="Balance conversion rate %",
        validators=[validators.NumberRange(min=0.1)],
        default=100.0,
        render_kw={"class": "form-control"},
        description="Percentage of the current active balance to be transferred to the draft campaign.",
    )
    qualify_threshold = FloatField(
        label="Qualify threshold %",
        validators=[validators.NumberRange(min=0.0)],
        default=0.0,
        render_kw={"class": "form-control"},
        description=(
            "Qualifies for conversion if the current balance is equal or more to the "
            "provided percentage of the target value (active campaign reward_goal)"
        ),
    )
