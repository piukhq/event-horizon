from flask_wtf import FlaskForm
from wtforms import BooleanField, FloatField, SelectField, validators


class EndCampaignActionForm(FlaskForm):
    convert_pending_rewards = BooleanField(label="Convert pending rewards?", render_kw={"class": "form-check-input"})
    transfer_balance = BooleanField(label="Transfer balance?", render_kw={"class": "form-check-input"})
    transfer_balance_from = SelectField(label="Transfer balance from", coerce=int, render_kw={"class": "form-control"})
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
