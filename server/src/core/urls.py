from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.api import api
from config import config

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
]

if not config.aws.use_s3 and settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
