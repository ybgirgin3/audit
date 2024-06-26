from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from quiz.models import Mark, Question, Category, Topic
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
        category_id = request.POST.get("category")
        image_data = request.FILES.get("image", "")
        if category_id:
            # category, created = Category.objects.get_or_create(name=category_name)
            category, created = Category.objects.get_or_create(id=category_id)
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

                # if image_data:
                #     format_, imgstr = image_data.split(";base64,")
                #     ext = format_.split('/')[-1]
                #     image_name = f'question{i}.{ext}'
                #     image_data = ContentFile(base64.b64decode(imgstr), name=image_name)
                # else:
                #     image_data = None

                question = Question(
                    question=q,
                    option1=o1,
                    option2=o2,
                    option3=o3,
                    option4=o4,
                    image=image_data,
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
                f"{count} questions added to category '{category}'. Wait until admin verifies them.",
            )
        else:
            messages.warning(request, "Category name cannot be empty")
        return redirect("add_questions")


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
        return redirect("add_questions")


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


@method_decorator(staff_member_required, name="dispatch")
class AddCategoryAndTopic(View):
    def get(self, request):
        categories = Category.objects.all()
        topics = Topic.objects.all()
        return render(
            request=request,
            template_name="management/add_topic_and_category.html",
            context={"categories": categories, "topics": topics},
        )

    def post(self, request):
        count, already_exists = 0, 0
        category_name = request.POST.get("category_name", None)
        topic_name = request.POST.get("topic_name", None)
        if category_name:
            # category, created = Category.objects.get_or_create(name=category_name)
            # category, created = Category.objects.get_or_create(name=category_name)
            # for i in range(1, settings.GLOBAL_SETTINGS["topic"] + 1):
            data = request.POST
            category = data.get("category_name", "")
            co = data.get("co", "")
            # if Question.objects.filter(question=q).first():
            if Category.objects.filter(name=category_name).first():
                messages.warning(request, f"{category_name} category already exist")
                return redirect("add_category_and_topic")

            cat = Category(name=category)
            cat.save()
            messages.success(
                request,
                f"{count} questions added to category '{category_name}'. Wait until admin verifies them.",
            )
        else:
            messages.warning(request, "Category name cannot be empty")

        if topic_name:
            # topic, created = Topic.objects.get_or_create(name=topic_name)
            data = request.POST
            topic = data.get("topic_name", "")
            if Topic.objects.filter(name=topic_name).first():
                messages.warning(request, f"{topic} topic already exist")

            topic_ = Topic(name=topic)

            topic_.save()
            messages.success(
                request,
                f"{count} questions added to category '{topic_name}'. Wait until admin verifies them.",
            )
        else:
            messages.warning(request, "Category name cannot be empty")

        return redirect("add_category_and_topic")


def get_topics(request, category_id):
    topics = Topic.objects.filter(category_id=category_id).values("id", "name")
    return JsonResponse(list(topics), safe=False)
