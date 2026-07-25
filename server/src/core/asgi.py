"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')

django_asgi_app = get_asgi_application()

serve_static = os.getenv("SERVE_STATIC_FILES", "true").strip().lower() in {
	"1",
	"true",
	"yes",
	"on",
}

if serve_static:
	application = ASGIStaticFilesHandler(django_asgi_app)
else:
	application = django_asgi_app
