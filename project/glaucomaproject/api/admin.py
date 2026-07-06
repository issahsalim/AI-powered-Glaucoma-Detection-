from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Diagnosis, UserProfile, AuditLog

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role')

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return [UserProfileInline(self.model, self.admin_site)]

    def get_role(self, obj):
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            return "No Profile"
    get_role.short_description = 'Role'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_name', 'doctor', 'specialist', 'prediction', 'is_referred', 'created_at')
    list_filter = ('prediction', 'is_referred', 'created_at')
    readonly_fields = ('created_at', 'image')
    search_fields = ('patient_name', 'id')

admin.site.register(Diagnosis, DiagnosisAdmin)

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'details')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'details')

admin.site.register(AuditLog, AuditLogAdmin)

# Specialized Admin Views for Doctors and Specialists
from .models import Doctor, Specialist

@admin.register(Doctor)
class DoctorAdmin(UserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(profile__role='DOCTOR')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ensure role is set for new doctors
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        profile.role = 'DOCTOR'
        profile.save()

@admin.register(Specialist)
class SpecialistAdmin(UserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(profile__role='SPECIALIST')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ensure role is set for new specialists
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        profile.role = 'SPECIALIST'
        profile.save()
        
    # Customize admin site text (overrides default "Django administration")
    admin.site.site_header = "Glauco-Guard Administration"
    admin.site.site_title = "Glauco-Guard Admin Portal"
    admin.site.index_title = "Welcome to Glauco-Guard"
