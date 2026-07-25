import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.db import models

logger = logging.getLogger('audit_logger')

class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to log requests and responses for audit trailing.
    Outputs as structured logs that can be captured by DataDog/CloudWatch.
    """
    
    def process_request(self, request):
        request.start_time = time.time()
        
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        else:
            duration = 0
            
        user = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
        
        log_data = {
            'event': 'api_request',
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'user': user,
            'ip': self.get_client_ip(request)
        }
        
        # We use standard logging. The formatter handles JSON transformation in production
        logger.info(log_data)
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AuditableModel(models.Model):
    """
    Abstract base model to automatically track who created/modified a record and when.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Needs tracking of user down the line using thread locals if desired:
    # created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_%(class)ss')
    
    class Meta:
        abstract = True
