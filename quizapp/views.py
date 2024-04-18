from django.shortcuts import render
from django.views import View
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json
from django.urls import reverse
from quiz.models import Question, Mark, Category, Audit, UserAuditProgress
@method_decorator(login_required, name='dispatch')
class Index(View):
    def get(self, request):
        results = Mark.objects.filter(user=request.user).order_by('-created_at')
        category_risk_count = {}
        latest_incorrect_risk_levels = {'High': 0, 'Medium': 0, 'Low': 0}
        category_completion_data = {}
        categories = Category.objects.all()
        user_audit_progresses = UserAuditProgress.objects.filter(user=request.user).select_related('category', 'audit').order_by('started_on')
        audit_category_progress = {}
        for progress in user_audit_progresses:
            audit_name = progress.audit.name
            if audit_name not in audit_category_progress:
                audit_category_progress[audit_name] = {}

            category_name = progress.category.name
            if category_name not in audit_category_progress[audit_name]:
                audit_category_progress[audit_name][category_name] = []

            audit_category_progress[audit_name][category_name].append({
                'progress': progress.progress,
                'started_on': progress.started_on.strftime("%Y-%m-%d %H:%M")  # Tarih formatını ayarlayın
            })

        # Denetim bilgilerini toplama
        audits = Audit.objects.prefetch_related('categories').all()

        if results.exists():
            latest_result = results.first()
            if latest_result.wrong_answers:
                for wa in latest_result.wrong_answers:
                    risk_level = wa['risk_level']
                    latest_incorrect_risk_levels[risk_level] += 1
        for result in results:
            if result.wrong_answers:
                questions = Question.objects.in_bulk(list(map(int, [wa['question_id'] for wa in result.wrong_answers])))
                result.wrong_answers_details = []
                for wa in result.wrong_answers:
                    question_id = int(wa['question_id'])
                    if question_id in questions:
                        question = questions[question_id]
                        question_details = {
                            "question": question.question,
                            "risk_level": wa['risk_level'],
                        }
                        if 'solution' in wa:
                            question_details["solution"] = wa['solution']
                        category = question.category.name
                        risk_level = wa['risk_level']
                        if category not in category_risk_count:
                            category_risk_count[category] = {'High': 0, 'Medium': 0, 'Low': 0}
                        category_risk_count[category][risk_level] += 1
                        result.wrong_answers_details.append(question_details)
                # Her bir result için wrong_answers_details listesini en fazla 8 öğe ile sınırla
                result.wrong_answers_details = result.wrong_answers_details[:4]
            else:
                result.wrong_answers_details = []
        for category in categories:
            total_quizzes_in_category = Question.objects.filter(category=category).count()
            completed_quizzes = 0
            for result in results:
                # Here we count how many quizzes in this category have been fully answered without wrong answers
                if not result.answered_questions.filter(category=category, marks__in=[result]).exists():
                    continue  # If no questions from this category were answered in this result, skip to the next
                # If there are answered questions from this category, check if all of them were answered correctly
                answered_questions_ids = [qa['question_id'] for qa in result.wrong_answers] if result.wrong_answers else []
                if all(q.id not in answered_questions_ids for q in result.answered_questions.filter(category=category)):
                    completed_quizzes += 1
            completion_rate = (completed_quizzes / total_quizzes_in_category) * 100 if total_quizzes_in_category > 0 else 0
            category_completion_data[category.name] = {
                'total': total_quizzes_in_category,
                'completed': completed_quizzes,
                'completion_rate': completion_rate
            }
        category_completion_data_json = mark_safe(json.dumps(category_completion_data))
        category_risk_count_json = mark_safe(json.dumps(category_risk_count))
        latest_incorrect_risk_levels_json = mark_safe(json.dumps(latest_incorrect_risk_levels))
        context = {
            "results": results,
            "category_risk_count_json": category_risk_count_json,
            "latest_incorrect_risk_levels_json": latest_incorrect_risk_levels_json,
            "category_completion_data_json": category_completion_data_json,
            "audit_category_progress": audit_category_progress,  # JSON'a dönüştürmeye gerek yok
           " audits": audits,
        }
        return render(request, "index.html", context)


   