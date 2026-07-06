from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Diagnosis, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role']

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    is_available = serializers.BooleanField(source='profile.is_available', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_available']

class DiagnosisSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.username', read_only=True)
    specialist_name = serializers.CharField(source='specialist.username', read_only=True)

    class Meta:
        model = Diagnosis
        fields = ['id', 'patient_name', 'patient_phone', 'prediction', 'confidence', 'glaucoma_prob', 
                  'normal_prob', 'doctor_notes', 'recommendations', 'is_referred', 
                  'referral_notes', 'created_at', 'doctor_name', 'specialist_name', 'image', 'model_used']
