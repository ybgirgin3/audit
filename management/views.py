from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from quiz.models import Mark, Question, Category
from os.path import join


# Create your views here.
@method_decorator(staff_member_required, name="dispatch")
class Manage(View):
    def get(self, request):
        panel_options = {
            "Upload Questions": {
                "link": reverse("upload_question"),
                "btntxt": "Upload",
            },
            "Verify Questions": {
                "link": reverse("verify_question"),
                "btntxt": "Verify",
            },
            "Get Results": {"link": reverse("results"), "btntxt": "Get"},
            "Delete Questions": {
                "link": reverse("delete_questions"),
                "btntxt": "Delete",
            },
        }
        return render(
            request, "management/manage.html", {"panel_options": panel_options}
        )


@method_decorator(staff_member_required, name="dispatch")
class Results(View):
    def get(self, request):
        return render(
            request, "management/results.html", {"results": Mark.objects.all()}
        )


@method_decorator(staff_member_required, name="dispatch")
class UploadQuestion(View):
    def get(self, request):
        return render(request, "management/upload_question.html")

    def post(self, request):
        qFile = request.FILES["qFile"]
        filepath = join(settings.BASE_DIR, "upload", "questions.csv")
        if not str(qFile).endswith(".csv"):
            messages.warning(request, "Only CSV file allowed")
        else:
            with open(filepath, "wb") as f:
                for chunk in qFile.chunks():
                    f.write(chunk)
            messages.success(request, "CSV file uploaded")
        return redirect("manage")


@method_decorator(staff_member_required, name="dispatch")
class AddQuestion(View):
    def get(self, request):
        categories = Category.objects.all()
        return render(
            request,
            "management/add_questions.html",
            {
                "questions": range(1, settings.GLOBAL_SETTINGS["questions"] + 1),
                "categories": categories,
            },
        )

    def post(self, request):
        count, already_exists = 0, 0
        category_name = request.POST.get("category")
        if category_name:
            category, created = Category.objects.get_or_create(name=category_name)
            for i in range(1, settings.GLOBAL_SETTINGS["questions"] + 1):
                data = request.POST
                q = data.get(f"q{i}", "")
                o1 = data.get(f"q{i}o1", "")
                o2 = data.get(f"q{i}o2", "")
                o3 = data.get(f"q{i}o3", "")
                o4 = data.get(f"q{i}o4", "")
                co = data.get(f"q{i}c", "")
                risk_level = data.get(f"q{i}risk_level", "L")
                if Question.objects.filter(question=q).first():
                    already_exists += 1
                    continue
                question = Question(
                    question=q,
                    option1=o1,
                    option2=o2,
                    option3=o3,
                    option4=o4,
                    correct_option=co,
                    creator=request.user,
                    category=category,
                    risk_level=risk_level,
                )
                question.save()
                count += 1
            if already_exists:
                messages.warning(request, f"{already_exists} questions already exist")
            messages.success(
                request,
                f"{count} questions added to category '{category_name}'. Wait until admin verifies them.",
            )
        else:
            messages.warning(request, "Category name cannot be empty")
        return redirect("quiz")


@method_decorator(staff_member_required, name="dispatch")
class VerifyQuestion(View):
    def get(self, request):
        qs = Question.objects.filter(verified=False)
        return render(request, "management/verify_question.html", {"questions": qs})

    def post(self, request):
        count_added = 0
        count_deleted = 0
        for q, v in request.POST.items():
            if q.startswith("q"):
                id = q[1:]
                if v == "on":
                    question = Question.objects.filter(id=id).first()
                    if question is not None:
                        question.verified = True
                        question.save()
                        count_added += 1
                elif v == "delete":
                    question = Question.objects.filter(id=id).first()
                    if question is not None:
                        question.delete()
                        count_deleted += 1

        messages.success(
            request, f"{count_added} questions added, {count_deleted} questions deleted"
        )
        return redirect("manage")


@method_decorator(staff_member_required, name="dispatch")
class Setting(View):
    def get(self, request):
        info = {"question_limit": settings.GLOBAL_SETTINGS["questions"]}
        return render(request, "management/setting.html", {"info": info})

    def post(self, request):
        qlimit = int(request.POST.get("qlimit", 10))
        if qlimit > 0:
            settings.GLOBAL_SETTINGS["questions"] = qlimit
            messages.success(request, "You preference saved")
        else:
            messages.warning(request, "Question limit can't be 0 or less than 0")
        return redirect("setting")


@method_decorator(staff_member_required, name="dispatch")
class QuizDelete(View):
    def get(self, request):
        questions = Question.objects.filter(verified=True)
        return render(
            request, "management/delete_questions.html", {"questions": questions}
        )

    def post(self, request):
        question_id = request.POST.get("question_id")
        question = Question.objects.filter(pk=question_id, verified=True).first()
        if question:
            question.delete()
            messages.success(request, "Question deleted successfully.")
        else:
            messages.error(request, "Question not found.")
        questions = Question.objects.filter(verified=True)
        return render(
            request, "management/delete_questions.html", {"questions": questions}
        )
