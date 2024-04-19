from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import (
    Question,
    Mark,
    Category,
    Audit,
    UserAuditProgress,
    UserResponse,
    AdminComment,
    Result,
)
from django.conf import settings
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
import json
from django.urls import reverse
from django.http import HttpResponse


# Create your views here.
@method_decorator(login_required, name="dispatch")
class Quiz(View):
    def get(self, request):
        selected_category_id = request.GET.get("category")
        if selected_category_id and selected_category_id != 0:
            questions = Question.objects.filter(category__id=selected_category_id)
        else:
            questions = Question.objects.filter(verified=True)
        categories = Category.objects.all()
        return render(
            request,
            "quiz/quiz.html",
            {
                "questions": questions,
                "categories": categories,
                "selected_category": selected_category_id,
            },
        )

    def post(self, request):
        total_questions = Question.objects.filter(verified=True).count()
        wrong_answers = []  # Yanlış cevaplanan soruların detaylarını saklayacak liste

        mark = Mark(user=request.user, total=total_questions)

        for i in range(1, total_questions + 1):
            q = Question.objects.filter(
                pk=request.POST.get(f"q{i}", 0), verified=True
            ).first()
            if q and request.POST.get(f"q{i}o", "") != q.correct_option:
                wrong_answer_detail = {
                    "question_id": q.id,
                    "risk_level": q.get_risk_level_display(),
                    "solution": q.solution,  # Bu satır sorunun çözümünü ekler
                }
                wrong_answers.append(wrong_answer_detail)
            elif q:
                mark.got += 1

        mark.wrong_answers = wrong_answers
        mark.save()

        # Kullanıcıya bilgi mesajı
        if wrong_answers:
            messages_str = "<br>".join(
                [
                    f"Soru: {item['question_id']}, Risk Seviyesi: {item['risk_level']}"
                    for item in wrong_answers
                ]
            )
            messages.error(
                request,
                mark_safe(
                    f"Yanlış cevaplanan sorular ve risk seviyeleri:<br>{messages_str}"
                ),
            )
        else:
            messages.success(request, "Tüm sorular doğru cevaplandı.")

        return redirect("quiz:result")


@method_decorator(login_required, name="dispatch")
class Result(View):
    def get(self, request):
        marks = Mark.objects.filter(user=request.user).order_by("-created_at")
        comments = AdminComment.objects.all()
        category_risk_count = {}
        latest_incorrect_risk_levels = {"High": 0, "Medium": 0, "Low": 0}
        category_completion_data = {}
        categories = Category.objects.all()

        if marks.exists():
            latest_result = marks.first()
            if latest_result.wrong_answers:
                for wa in latest_result.wrong_answers:
                    risk_level = wa["risk_level"]
                    latest_incorrect_risk_levels[risk_level] += 1

        for mark in marks:
            if mark.wrong_answers:
                questions = Question.objects.in_bulk(
                    list(map(int, [wa["question_id"] for wa in result.wrong_answers]))
                )
                mark.wrong_answers_details = []

                for wa in mark.wrong_answers:
                    question_id = int(wa["question_id"])
                    if question_id in questions:
                        question = questions[question_id]
                        question_details = {
                            "question": question.question,
                            "risk_level": wa["risk_level"],
                        }
                        if "solution" in wa:
                            question_details["solution"] = wa["solution"]

                        category = question.category.name
                        risk_level = wa["risk_level"]
                        if category not in category_risk_count:
                            category_risk_count[category] = {
                                "High": 0,
                                "Medium": 0,
                                "Low": 0,
                            }
                        category_risk_count[category][risk_level] += 1

                        mark.wrong_answers_details.append(question_details)
            else:
                mark.wrong_answers_details = []

        for category in categories:
            total_quizzes_in_category = Question.objects.filter(
                category=category
            ).count()
            completed_quizzes = 0
            for mark in marks:
                # Here we count how many quizzes in this category have been fully answered without wrong answers
                if not mark.answered_questions.filter(
                    category=category, marks__in=[mark]
                ).exists():
                    continue  # If no questions from this category were answered in this mark, skip to the next
                # If there are answered questions from this category, check if all of them were answered correctly
                answered_questions_ids = (
                    [qa["question_id"] for qa in mark.wrong_answers]
                    if mark.wrong_answers
                    else []
                )
                if all(
                    q.id not in answered_questions_ids
                    for q in mark.answered_questions.filter(category=category)
                ):
                    completed_quizzes += 1

            completion_rate = (
                (completed_quizzes / total_quizzes_in_category) * 100
                if total_quizzes_in_category > 0
                else 0
            )
            category_completion_data[category.name] = {
                "total": total_quizzes_in_category,
                "completed": completed_quizzes,
                "completion_rate": completion_rate,
            }

        category_completion_data_json = mark_safe(json.dumps(category_completion_data))
        category_risk_count_json = mark_safe(json.dumps(category_risk_count))
        latest_incorrect_risk_levels_json = mark_safe(
            json.dumps(latest_incorrect_risk_levels)
        )

        context = {
            "comments": comments,
            "marks": marks,
            "category_risk_count_json": category_risk_count_json,
            "latest_incorrect_risk_levels_json": latest_incorrect_risk_levels_json,
            "category_completion_data_json": category_completion_data_json,
        }
        return render(request, "quiz/result.html", context)


class Leaderboard(View):
    def get(self, request):
        return render(
            request,
            "quiz/leaderboard.html",
            {"results": Mark.objects.all().order_by("-got")[:10]},
        )


@method_decorator(login_required, name="dispatch")
class AuditView(View):
    def get(self, request):
        audits = Audit.objects.prefetch_related("categories").all()
        user_progress = UserAuditProgress.objects.filter(
            user=request.user
        ).select_related("audit")
        progress_dict = {progress.audit.id: progress for progress in user_progress}

        for audit in audits:
            audit.progress = progress_dict.get(audit.id)

        return render(
            request,
            "quiz/audits_list.html",
            {
                "audits": audits,
            },
        )


class StartAudit(View):
    def get(self, request, audit_id):
        audit = get_object_or_404(Audit, pk=audit_id)
        categories = audit.categories.all()
        if categories:
            # Eğer denetime ait kategoriler varsa, ilk kategoriyi seçerek quiz sayfasına yönlendir
            category_id = categories[0].id
            # Kategori ID'sini bir query parametresi olarak quiz URL'ine ekleyin
            url = reverse("quiz:quiz") + f"?category={category_id}"
            return redirect(url)
        else:
            # Eğer denetime ait kategori yoksa, denetimler listesine geri dön
            return redirect(reverse("quiz:audits_list"))


@method_decorator(login_required, name="dispatch")
class UserAuditProgressView(View):
    def get(self, request):
        # Kullanıcının tüm denetim ilerlemelerini getir ve gerekli ilişkileri önceden yükle (prefetch)
        user_audit_progresses = (
            UserAuditProgress.objects.filter(user=request.user)
            .select_related("category", "audit")
            .order_by("started_on")
        )

        # Denetime ve kategoriye göre gruplandırılmış denetim ilerlemelerini hazırla
        audit_category_progress = {}
        for progress in user_audit_progresses:
            audit_name = progress.audit.name
            if audit_name not in audit_category_progress:
                audit_category_progress[audit_name] = {}

            category_name = progress.category.name
            if category_name not in audit_category_progress[audit_name]:
                audit_category_progress[audit_name][category_name] = []

            audit_category_progress[audit_name][category_name].append(
                {"progress": progress.progress, "started_on": progress.started_on}
            )

        context = {
            "audit_category_progress": audit_category_progress,
        }
        return render(request, "index.html", context)


from django.db.models import Exists, OuterRef


def denetim_view(request):
    # Yönetici yorumlarını getirir ve kullanıcının yanıtladığı yorumları belirtir
    admin_comments = (
        AdminComment.objects.select_related("result")
        .annotate(
            has_responded=Exists(
                UserResponse.objects.filter(comment=OuterRef("pk"), user=request.user)
            )
        )
        .all()
    )

    if request.method == "POST":
        comment_id = request.POST.get("comment_id")
        response_text = request.POST.get("response")
        comment = AdminComment.objects.get(id=comment_id)

        # Kullanıcının daha önce yanıt verip vermediğini kontrol eder
        if not comment.userresponse_set.filter(user=request.user).exists():
            if comment.result.comments_allowed:
                # Yeni bir kullanıcı yanıtı oluşturur ve kaydeder
                UserResponse.objects.create(
                    comment=comment, response=response_text, user=request.user
                )
                # Denetim sayfasına yönlendirme yapar
                return redirect("quiz:audits_list")
            else:
                # Yorumlar kapalıysa hata mesajı verir
                return HttpResponse(
                    "Comments are closed for this question.", status=403
                )

    # 'denetim.html' şablonunu yönetici yorumları ile birlikte render eder
    return render(request, "quiz:audits_list", {"comments": admin_comments})
