import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import LoginHistory

User = get_user_model()
logger = logging.getLogger('security')


class SecurityAuditMiddleware(MiddlewareMixin):
    """Middleware for security auditing and logging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Log security-relevant requests"""
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        request.client_ip = ip
        
        # Log sensitive endpoints
        sensitive_paths = [
            '/admin/',
            '/api/auth/',
            '/api/trading/',
            '/api/portfolio/',
            '/accounts/login/',
            '/accounts/signup/',
        ]
        
        if any(request.path.startswith(path) for path in sensitive_paths):
            logger.info(
                f"Security: {request.method} {request.path} from {ip} "
                f"User: {getattr(request.user, 'email', 'Anonymous')} "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
            )
    
    def process_response(self, request, response):
        """Log security-relevant responses"""
        
        # Log failed authentication attempts
        if (hasattr(request, 'user') and 
            request.path.startswith('/accounts/login/') and 
            response.status_code in [400, 401, 403]):
            
            logger.warning(
                f"Security: Failed login attempt from {getattr(request, 'client_ip', 'Unknown')} "
                f"Path: {request.path} Status: {response.status_code}"
            )
        
        # Log successful logins
        if (hasattr(request, 'user') and 
            request.user.is_authenticated and 
            request.path.startswith('/accounts/login/') and 
            response.status_code == 200):
            
            self._log_successful_login(request)
        
        return response
    
    def _log_successful_login(self, request):
        """Log successful login and create login history record"""
        try:
            LoginHistory.objects.create(
                user=request.user,
                ip_address=getattr(request, 'client_ip', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True,
                timestamp=timezone.now()
            )
            
            logger.info(
                f"Security: Successful login for {request.user.email} "
                f"from {getattr(request, 'client_ip', 'Unknown')}"
            )
        except Exception as e:
            logger.error(f"Security: Failed to log successful login: {e}")


class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        super().__init__(get_response)
    
    def process_request(self, request):
        """Implement basic rate limiting"""
        
        # Get client IP
        ip = getattr(request, 'client_ip', request.META.get('REMOTE_ADDR'))
        
        # Rate limit sensitive endpoints
        sensitive_endpoints = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/trading/order/',
        ]
        
        if any(request.path.startswith(endpoint) for endpoint in sensitive_endpoints):
            current_time = timezone.now()
            
            # Clean old entries (older than 1 hour)
            cutoff_time = current_time - timezone.timedelta(hours=1)
            self.request_counts = {
                key: timestamps for key, timestamps in self.request_counts.items()
                if any(ts > cutoff_time for ts in timestamps)
            }
            
            # Check rate limit
            if ip not in self.request_counts:
                self.request_counts[ip] = []
            
            # Remove old timestamps for this IP
            self.request_counts[ip] = [
                ts for ts in self.request_counts[ip] if ts > cutoff_time
            ]
            
            # Check if rate limit exceeded
            if len(self.request_counts[ip]) >= 100:  # 100 requests per hour
                logger.warning(
                    f"Security: Rate limit exceeded for IP {ip} "
                    f"on endpoint {request.path}"
                )
                from django.http import HttpResponseTooManyRequests
                return HttpResponseTooManyRequests("Rate limit exceeded")
            
            # Add current request
            self.request_counts[ip].append(current_time)
        
        return None


class CSRFLoggingMiddleware(MiddlewareMixin):
    """Log CSRF failures for security monitoring"""
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Log CSRF token failures"""
        return None
    
    def process_exception(self, request, exception):
        """Log CSRF exceptions"""
        if 'CSRF' in str(exception):
            logger.warning(
                f"Security: CSRF failure from {getattr(request, 'client_ip', 'Unknown')} "
                f"Path: {request.path} User: {getattr(request.user, 'email', 'Anonymous')}"
            )
        return None

