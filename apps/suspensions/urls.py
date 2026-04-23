from django.urls import path

from apps.suspensions import views as v

urlpatterns = [
    path("suspensions/my-status/", v.MySuspensionStatusView.as_view(), name="suspensions-my-status"),
    path("admin/suspensions/", v.AdminSuspensionListCreateView.as_view(), name="admin-suspensions"),
    path("admin/suspensions/<uuid:suspension_id>/lift/", v.AdminSuspensionLiftView.as_view(), name="admin-suspensions-lift"),
]
