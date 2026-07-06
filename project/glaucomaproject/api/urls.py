from django.urls import path
from .views import (
    PredictView, DownloadReportView, LoginView, ChangePasswordView,
    DiagnosisDetailView, ReferToSpecialistView, SpecialistCasesView, SpecialistListView,
    UpdateAvailabilityView, DoctorHistoryView
)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/toggle-availability/', UpdateAvailabilityView.as_view(), name='toggle_availability'),
    path('predict/', PredictView.as_view(), name='predict'),
    path('diagnosis/<int:pk>/', DiagnosisDetailView.as_view(), name='diagnosis_detail'),
    path('diagnosis/<int:pk>/refer/', ReferToSpecialistView.as_view(), name='refer_diagnosis'),
    path('specialist/cases/', SpecialistCasesView.as_view(), name='specialist_cases'),
    path('specialist/list/', SpecialistListView.as_view(), name='specialist_list'),
    path('doctor/history/', DoctorHistoryView.as_view(), name='doctor_history'),
    path('report/<int:pk>/', DownloadReportView.as_view(), name='download_report'),
]
