from django.urls import path
from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.Quiz.as_view(), name="quiz"),
    path("result/", views.Result.as_view(), name="result"),
    path("", views.UserAuditProgressView.as_view(), name="index"),
    path("leaderboard/", views.Leaderboard.as_view(), name="leaderboard"),
    path("audits/", views.AuditView.as_view(), name="audits_list"),
    path(
        "audits/start/<int:audit_id>/", views.StartAudit.as_view(), name="start_audit"
    ),
]
