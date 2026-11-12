from django.urls import path

from .views import MemberAttendanceView, MemberMembershipsView, MemberProfileView

urlpatterns = [
    path("profile/", MemberProfileView.as_view(), name="portal-profile"),
    path("memberships/", MemberMembershipsView.as_view(), name="portal-memberships"),
    path("attendance/", MemberAttendanceView.as_view(), name="portal-attendance"),
]
