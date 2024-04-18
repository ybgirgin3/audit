from django.urls import path
from . import views

urlpatterns = [
    path("", views.Manage.as_view(), name="manage"),
    path("results/", views.Results.as_view(), name="results"),
    path("upload_questions", views.UploadQuestion.as_view(), name="upload_question"),
    path("verifiy_questions/", views.VerifyQuestion.as_view(), name="verify_question"),
    path("add_questions/", views.AddQuestion.as_view(), name="add_questions"),
    path("add_category_and_topic", views.AddCategoryAndTopic.as_view(), name='add_category_and_topic'),
    path("delete_questions/", views.QuizDelete.as_view(), name="delete_questions"),
    path("setting/", views.Setting.as_view(), name="setting"),
]
