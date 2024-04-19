from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Topic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Create your models here.
class Question(models.Model):
    question = models.TextField(blank=False, unique=True)
    option1 = models.CharField(blank=False, max_length=150)
    option2 = models.CharField(blank=False, max_length=150)
    option3 = models.CharField(blank=False, max_length=150)
    option4 = models.CharField(blank=False, max_length=150)
    correct_option = models.CharField(max_length=1, blank=False)
    image = models.ImageField(
        upload_to="question_images/", null=True, blank=True
    )  # Soru için resim (opsiyonel)
    creator = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    RISK_LEVELS = [
        ("L", "Low"),
        ("M", "Medium"),
        ("H", "High"),
    ]
    risk_level = models.CharField(max_length=1, choices=RISK_LEVELS, default="L")
    info = models.TextField(blank=True)  # Bilgilendirme metni
    solution = models.TextField(blank=True)  # Çözüm önerisİ
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Question({self.question}, {self.creator})"
    
    @property
    def content(self):
        return self.__str__


class Mark(models.Model):
    total = models.IntegerField(blank=False)
    got = models.IntegerField(blank=False, default=0)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    wrong_answers = JSONField(
        blank=True, null=True
    )  # Yanlış cevaplanan sorular ve risk seviyeleri
    created_at = models.DateTimeField(default=timezone.now)
    answered_questions = models.ManyToManyField(
        Question, related_name="marks", blank=True
    )

    def __str__(self):
        return f"Mark({self.got}/{self.total}, {self.user})"


class Result(models.Model):             #TODO: Change this Result name to QuestionResult.
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Sonucu olan kullanıcı
    question = models.ForeignKey(Question, on_delete=models.CASCADE)  # İlgili soru
    correct_option = models.BooleanField(default=False)  # Cevabın doğruluğu
    RISK_LEVELS = models.CharField(
        max_length=10, choices=Question.RISK_LEVELS
    )  # Sorunun zorluk seviyesi
    comments_allowed = models.BooleanField(
        default=True
    )  # Yorum yapılmasına izin verilip verilmediği

    def __str__(self):
        # Nesne string olarak kullanıcı adı, soru içeriği ve doğruluk durumunu döndürür
        return f"{self.user.username} - {self.question.content} - Correct: {self.is_correct}"

    @property
    def is_correct(self):
        return self.correct_option
class AdminComment(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE)  # İlgili sonuç
    admin = models.ForeignKey(User, on_delete=models.CASCADE)  # Yorumu yapan admin
    comment = models.TextField()  # Yorum metni

    def __str__(self):
        # Nesne string olarak yorumun yapıldığı soru içeriği ve admin kullanıcı adını döndürür
        return f"Comment on {self.result.question.content} by {self.admin.username}"


# Kullanıcı yanıtı modeli
class UserResponse(models.Model):
    comment = models.ForeignKey(
        AdminComment, on_delete=models.CASCADE
    )  # İlgili yönetici yorumu
    response = models.TextField()  # Kullanıcının yanıtı
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Yanıtı veren kullanıcı

    def __str__(self):
        # Nesne string olarak yanıt veren kullanıcının adını ve yanıtın yapıldığı yorumun soru içeriğini döndürür
        return f"Response by {self.user.username} on {self.comment.result.question.content}"


class Audit(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    categories = models.ManyToManyField(Category, related_name="audits")

    def __str__(self):
        return self.name


# New UserAuditProgress model
class UserAuditProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    progress = models.PositiveIntegerField(default=0)
    started_on = models.DateTimeField(auto_now_add=True)
    success_rate = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("user", "audit", "category")

    def __str__(self):
        return f"{self.user.username} - {self.audit.name}"
