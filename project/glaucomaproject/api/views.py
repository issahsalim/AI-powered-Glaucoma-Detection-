import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.mail import send_mail
import numpy as np
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from .models import Diagnosis, AuditLog, UserProfile
from .serializers import DiagnosisSerializer, UserSerializer
from .pdf_utils import generate_glaucoma_report

def log_activity(user, action, details=""):
    if user and user.is_authenticated:
        AuditLog.objects.create(user=user, action=action, details=details)

# Load models globally
RESNET_MODEL_PATH = os.path.join(settings.BASE_DIR, 'ml_model', 'glaucoma_mobile_model.pt')
VIT_MODEL_PATH = os.path.join(settings.BASE_DIR, 'ml_model', 'glaucoma_vit_mobile_model.pt')
device = torch.device('cpu')

RESNET_MODEL = None
VIT_MODEL = None
RESNET_LOADED = False
VIT_LOADED = False

try:
    if os.path.exists(VIT_MODEL_PATH):
        VIT_MODEL = torch.jit.load(VIT_MODEL_PATH, map_location=device)
        VIT_MODEL.eval()
        VIT_LOADED = True
        print("Vision Transformer (ViT) model loaded successfully globally.")
except Exception as e:
    print(f"Error loading ViT model: {e}")

try:
    if os.path.exists(RESNET_MODEL_PATH):
        RESNET_MODEL = torch.jit.load(RESNET_MODEL_PATH, map_location=device)
        RESNET_MODEL.eval()
        RESNET_LOADED = True
        print("ResNet CNN model loaded successfully globally.")
except Exception as e:
    print(f"Error loading ResNet model: {e}")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
classes = ["glaucoma", "normal"]

def is_fundus_image(pil_img):
    img_small = pil_img.resize((64, 64))
    img_data = np.array(img_small)
    avg_red = np.mean(img_data[:, :, 0])
    avg_blue = np.mean(img_data[:, :, 2])
    if avg_red < 10: return False, "Image is too dark."
    if avg_red < (avg_blue * 1.5): return False, "Not a retinal fundus scan."
    return True, "Valid"

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            log_activity(user, 'LOGIN', f"User logged in via API")
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not request.user.check_password(old_password):
            return Response({'error': 'Incorrect old password'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not new_password or len(new_password) < 6:
            return Response({'error': 'New password too short'}, status=status.HTTP_400_BAD_REQUEST)
            
        request.user.set_password(new_password)
        request.user.save()
        log_activity(request.user, 'UPDATE', "Password changed by user")
        return Response({'message': 'Password updated successfully'})

class PredictView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if not VIT_LOADED and not RESNET_LOADED:
            return Response({"error": "No ML Models are currently loaded on the server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if 'image' not in request.FILES:
            return Response({"error": "No image provided."}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']
        try:
            image = Image.open(image_file).convert('RGB')
            is_valid, message = is_fundus_image(image)
            if not is_valid:
                return Response({"error": message, "is_invalid": True}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            # Determine selected model with ViT as default
            selected_model_type = request.data.get('model', 'ViT')
            active_model = None
            actual_model_used = 'ViT'

            if selected_model_type == 'ResNet':
                if RESNET_LOADED:
                    active_model = RESNET_MODEL
                    actual_model_used = 'ResNet'
                elif VIT_LOADED:
                    active_model = VIT_MODEL
                    actual_model_used = 'ViT'
                    print("ResNet model requested but not loaded. Falling back to default ViT.")
            else: # Default is ViT
                if VIT_LOADED:
                    active_model = VIT_MODEL
                    actual_model_used = 'ViT'
                elif RESNET_LOADED:
                    active_model = RESNET_MODEL
                    actual_model_used = 'ResNet'
                    print("ViT model requested but not loaded. Falling back to ResNet.")

            if active_model is None:
                return Response({"error": "Requested classification engine is not active."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            input_tensor = transform(image).unsqueeze(0)
            with torch.no_grad():
                output = active_model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                predicted_idx = torch.argmax(probabilities).item()

            prediction = classes[predicted_idx]
            confidence = probabilities[predicted_idx].item()

            if confidence < 0.60:
                return Response({"error": "AI is unsure.", "is_invalid": True}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            diagnosis = Diagnosis.objects.create(
                doctor=request.user,
                patient_name=request.data.get('patient_name', 'Unknown Patient'),
                image=image_file,
                prediction=prediction,
                confidence=round(confidence * 100, 2),
                glaucoma_prob=round(probabilities[0].item() * 100, 2),
                normal_prob=round(probabilities[1].item() * 100, 2),
                doctor_notes=request.data.get('doctor_notes', ''),
                recommendations=request.data.get('recommendations', ''),
                model_used=actual_model_used
            )
            log_activity(request.user, 'SCAN', f"Performed scan using {actual_model_used} for patient: {diagnosis.patient_name}")
            return Response({
                "diagnosis_id": diagnosis.id, 
                "prediction": prediction, 
                "confidence": round(confidence * 100, 2),
                "probabilities": {
                    "glaucoma": diagnosis.glaucoma_prob,
                    "normal": diagnosis.normal_prob
                },
                "model_used": diagnosis.model_used
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DiagnosisDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, pk):
        try:
            diagnosis = Diagnosis.objects.get(pk=pk)
            # Only allow the doctor who created it or the assigned specialist to update
            if diagnosis.doctor != request.user and diagnosis.specialist != request.user:
                return Response({"error": "Access Denied"}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = DiagnosisSerializer(diagnosis, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                log_activity(request.user, 'UPDATE', f"Updated details for diagnosis #{pk}")
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Diagnosis.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class ReferToSpecialistView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        try:
            diagnosis = Diagnosis.objects.get(pk=pk)
            specialist_id = request.data.get('specialist_id')
            specialist = User.objects.get(pk=specialist_id, profile__role='SPECIALIST')
            
            diagnosis.specialist = specialist
            diagnosis.is_referred = True
            diagnosis.referral_notes = request.data.get('referral_notes', '')
            diagnosis.save()
            
            log_activity(request.user, 'REFER', f"Referred diagnosis #{pk} to {specialist.username}")
            
            # Send email notification to specialist
            if specialist.email:
                try:
                    result_label = "GLAUCOMA DETECTED" if diagnosis.prediction == 'glaucoma' else "NO GLAUCOMA"
                    result_color = "#e53e3e" if diagnosis.prediction == 'glaucoma' else "#38a169"
                    
                    subject = f"[Glauco-Guard] New Referral Case #{diagnosis.id} — {result_label}"
                    
                    html_message = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 640px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                      <div style="background: linear-gradient(135deg, #005b9f, #004275); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 22px;">👁️ Glauco-Guard AI</h1>
                        <p style="color: #bee3f8; margin: 8px 0 0;">Clinical Referral Notification</p>
                      </div>
                      
                      <div style="padding: 30px; background: #fff;">
                        <p style="font-size: 16px; color: #2d3748;">Dear <strong>Dr. {specialist.username}</strong>,</p>
                        <p style="color: #4a5568;">A new patient case has been assigned to you for specialist review. Please log in to the Glauco-Guard platform to access the full diagnostic report.</p>
                        
                        <div style="background: {result_color}15; border-left: 4px solid {result_color}; border-radius: 8px; padding: 16px; margin: 20px 0;">
                          <p style="margin: 0; font-size: 18px; font-weight: bold; color: {result_color};">AI Result: {result_label}</p>
                          <p style="margin: 4px 0 0; color: #718096; font-size: 14px;">Confidence: {diagnosis.confidence:.1f}%</p>
                        </div>
                        
                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                          <tr style="background: #f7fafc;">
                            <td style="padding: 12px 16px; font-weight: bold; color: #718096; width: 40%;">Case ID</td>
                            <td style="padding: 12px 16px; color: #2d3748;">#{diagnosis.id}</td>
                          </tr>
                          <tr>
                            <td style="padding: 12px 16px; font-weight: bold; color: #718096;">Patient Name</td>
                            <td style="padding: 12px 16px; color: #2d3748;">{diagnosis.patient_name}</td>
                          </tr>
                          <tr style="background: #f7fafc;">
                            <td style="padding: 12px 16px; font-weight: bold; color: #718096;">Patient Phone</td>
                            <td style="padding: 12px 16px; color: #2d3748;">{diagnosis.patient_phone or 'Not provided'}</td>
                          </tr>
                          <tr>
                            <td style="padding: 12px 16px; font-weight: bold; color: #718096;">Referring Doctor</td>
                            <td style="padding: 12px 16px; color: #2d3748;">Dr. {request.user.username}</td>
                          </tr>
                          <tr style="background: #f7fafc;">
                            <td style="padding: 12px 16px; font-weight: bold; color: #718096;">Glaucoma Probability</td>
                            <td style="padding: 12px 16px; color: #e53e3e; font-weight: bold;">{diagnosis.glaucoma_prob:.1f}%</td>
                          </tr>
                          <tr>
                            <td style="padding: 12px 16px; font-weight: bold; color: #718096;">Normal Probability</td>
                            <td style="padding: 12px 16px; color: #38a169; font-weight: bold;">{diagnosis.normal_prob:.1f}%</td>
                          </tr>
                          <tr style="background: #f7fafc;">
                            <td style="padding: 12px 16px; font-weight: bold; color: #718096;">Date of Scan</td>
                            <td style="padding: 12px 16px; color: #2d3748;">{diagnosis.created_at.strftime('%d %B %Y, %I:%M %p')}</td>
                          </tr>
                        </table>
                        
                        <div style="background: #ebf8ff; border-radius: 8px; padding: 16px; margin: 20px 0;">
                          <p style="margin: 0 0 6px; font-weight: bold; color: #2c5282;">📋 Doctor's Clinical Notes:</p>
                          <p style="margin: 0; color: #4a5568;">{diagnosis.doctor_notes or 'No notes provided.'}</p>
                        </div>
                        
                        <div style="background: #fffbeb; border-radius: 8px; padding: 16px; margin: 20px 0;">
                          <p style="margin: 0 0 6px; font-weight: bold; color: #744210;">📨 Referral Instructions:</p>
                          <p style="margin: 0; color: #4a5568;">{diagnosis.referral_notes or 'Please review the attached AI diagnostic report.'}</p>
                        </div>
                        
                        <p style="color: #718096; font-size: 13px; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
                          This is an automated notification from the Glauco-Guard AI Platform.<br>
                          Please log in to the mobile application to review the full retinal scan and report.
                        </p>
                      </div>
                    </div>
                    """
                    
                    send_mail(
                        subject=subject,
                        message=f"New referral: Case #{diagnosis.id} - {diagnosis.patient_name} ({result_label}). Please log in to Glauco-Guard to review.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[specialist.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                except Exception as email_error:
                    # Log but don't fail the referral
                    print(f"Email notification failed: {email_error}")
            
            return Response({"message": f"Successfully referred to {specialist.username}"})
        except (Diagnosis.DoesNotExist, User.DoesNotExist):
            return Response({"error": "Diagnosis or Specialist not found"}, status=status.HTTP_404_NOT_FOUND)

class SpecialistCasesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if request.user.profile.role != 'SPECIALIST':
            return Response({"error": "Only specialists can view this"}, status=status.HTTP_403_FORBIDDEN)
        cases = Diagnosis.objects.filter(specialist=request.user)
        serializer = DiagnosisSerializer(cases, many=True)
        return Response(serializer.data)

class SpecialistListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        specialists = User.objects.filter(profile__role='SPECIALIST').order_by('-profile__is_available', 'username')
        serializer = UserSerializer(specialists, many=True)
        return Response(serializer.data)

class UpdateAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if request.user.profile.role != 'SPECIALIST':
            return Response({"error": "Only specialists can toggle availability"}, status=403)
        
        available = request.data.get('is_available', True)
        request.user.profile.is_available = available
        request.user.profile.save()
        return Response({"message": "Status updated", "is_available": available})

class DoctorHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        diagnoses = Diagnosis.objects.filter(doctor=request.user).order_by('-created_at')
        serializer = DiagnosisSerializer(diagnoses, many=True)
        return Response(serializer.data)

class DownloadReportView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        try:
            diagnosis = Diagnosis.objects.get(pk=pk)
            log_activity(request.user, 'VIEW', f"Downloaded report for diagnosis #{pk}")
            pdf_buffer = generate_glaucoma_report(diagnosis)
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Report_{diagnosis.id}.pdf"'
            return response
        except Diagnosis.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

from django.shortcuts import render
from django.views import View

class HomeView(View):
    def get(self, request):
        diagnoses = Diagnosis.objects.all().order_by('-created_at')
        total_scans = diagnoses.count()
        glaucoma_scans = diagnoses.filter(prediction='glaucoma').count()
        normal_scans = diagnoses.filter(prediction='normal').count()
        glaucoma_rate = round((glaucoma_scans / total_scans * 100), 1) if total_scans > 0 else 0.0
        
        context = {
            'diagnoses': diagnoses,
            'total_scans': total_scans,
            'glaucoma_scans': glaucoma_scans,
            'normal_scans': normal_scans,
            'glaucoma_rate': glaucoma_rate,
        }
        return render(request, 'home.html', context)
