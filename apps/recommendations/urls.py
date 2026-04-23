from django.urls import path

from apps.recommendations import views as v

urlpatterns = [
    path("recommendations/categories/", v.ContentCategoriesListView.as_view(), name="rec-categories"),
    path("recommendations/interests/", v.UserInterestSummaryView.as_view(), name="rec-interests"),
    path("recommendations/track/", v.TrackInteractionView.as_view(), name="rec-track"),
]
