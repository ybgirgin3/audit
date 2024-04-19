from django.contrib import admin
from .models import (
    Category,
    Question,
    Mark,
    Audit,
    UserAuditProgress,
    AdminComment,
    Result,
)


class ResultAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "question",
        "correct_option",
        "RISK_LEVELS",
        "comments_allowed",
    ]
    search_fields = ["user", "question", "correct_option"]
    list_filter = ("user", "question", "correct_option")


admin.site.register(Result, ResultAdmin)


class AdminCommentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "result",
        "admin",
        "comment",
    ]
    search_fields = ["result", "admin", "comment"]
    list_filter = ("result", "admin", "comment")


admin.site.register(AdminComment, AdminCommentAdmin)


class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "question",
        "creator",
        "category",
        "risk_level",
        "info",
        "solution",
    ]
    search_fields = ["question", "info", "solution"]
    list_filter = ("verified", "risk_level", "category")


admin.site.register(Question, QuestionAdmin)


class MarkAdmin(admin.ModelAdmin):
    list_display = ["id", "got", "total", "user", "created_at"]
    list_filter = ["user", "created_at"]
    search_fields = ["user__username"]


admin.site.register(Mark, MarkAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


admin.site.register(Category, CategoryAdmin)


class AuditAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description"]
    search_fields = ["name", "description"]
    filter_horizontal = [
        "categories"
    ]  # This provides a more user-friendly interface for selecting categories


admin.site.register(Audit, AuditAdmin)


class UserAuditProgressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "audit",
        "category",
        "progress",
        "started_on",
        "success_rate",
    ]
    list_filter = ["audit", "user", "category"]
    search_fields = ["audit__name", "user__username"]


admin.site.register(UserAuditProgress, UserAuditProgressAdmin)
