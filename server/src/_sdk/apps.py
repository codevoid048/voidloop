"""_sdk/apps.py - SDK app configuration"""

from django.apps import AppConfig


class SdkConfig(AppConfig):
    """Configuration for the _sdk infrastructure app"""
    name = '_sdk'
    verbose_name = 'SDK & Infrastructure'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Register signal handlers when Django starts"""
        import _sdk.signals  # noqa
