from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),  # This ensures all mobile requests start with /api/
    path('', HomeView.as_view(), name='home'),
]

# Serve media files (for retinal images and PDF reports)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
