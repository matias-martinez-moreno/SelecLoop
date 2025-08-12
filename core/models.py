# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    location = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    short_description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    USER_ROLES = [
        ('candidate', 'Candidato'),
        ('company_rep', 'Representante de Empresa'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=15, choices=USER_ROLES, default='candidate')

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='representatives'
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class Review(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reviews')
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='submitted_reviews')

    job_title = models.CharField(max_length=150)
    MODALITY_CHOICES = [
        ('remote', 'Remoto'),
        ('onsite', 'Presencial'),
        ('hybrid', 'Híbrido'),
    ]
    modality = models.CharField(max_length=10, choices=MODALITY_CHOICES)

    communication_rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    difficulty_rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    response_time_rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    overall_rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])

    pros = models.TextField()
    cons = models.TextField()
    interview_questions = models.TextField(blank=True, null=True)

    submission_date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Reseña de {self.user_profile.user.username} para {self.company.name} ({self.job_title})"

    class Meta:
        ordering = ['-submission_date']