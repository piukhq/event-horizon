from app.admin.model_views import AuthorisedModelView


class CampaignAdmin(AuthorisedModelView):
    column_searchable_list = ("retailerrewards.slug",)
    form_widget_args = {"created_at": {"disabled": True}, "updated_at": {"disabled": True}}
    column_labels = dict(retailerrewards="Retailer")
