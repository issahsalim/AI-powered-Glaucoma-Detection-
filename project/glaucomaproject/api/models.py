from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('DOCTOR', 'Doctor'),
        ('SPECIALIST', 'Specialist'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='DOCTOR')
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Profile for {self.user.username} ({self.role}) - {'Available' if self.is_available else 'Busy'}"

class Diagnosis(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_diagnoses', null=True, blank=True)
    specialist = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_cases', null=True, blank=True)
    
    patient_name = models.CharField(max_length=255, blank=True, default="Unknown Patient")
    patient_phone = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(upload_to='diagnoses/')
    prediction = models.CharField(max_length=50)
    confidence = models.FloatField()
    glaucoma_prob = models.FloatField(default=0.0)
    normal_prob = models.FloatField(default=0.0)
    doctor_notes = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    is_referred = models.BooleanField(default=False)
    referral_notes = models.TextField(blank=True)
    
    model_used = models.CharField(max_length=50, default='ViT')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis {self.id} - {self.patient_name} ({self.prediction}) [{self.model_used}]"

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

# Proxy Models for cleaner Admin Organization
class Doctor(User):
    class Meta:
        proxy = True
        app_label = 'api'
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'

class Specialist(User):
    class Meta:
        proxy = True
        app_label = 'api'
        verbose_name = 'Specialist'
        verbose_name_plural = 'Specialists'
