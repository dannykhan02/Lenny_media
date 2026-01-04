from .auth import auth_bp
from .service import register_service_resources
from .booking import register_booking_resources
from .quote import register_quote_resources
from .dashboard import register_dashboard_resources

__all__ = [
    'auth_bp', 
    'register_service_resources',
    'register_booking_resources',
    'register_quote_resources',
    'register_dashboard_resources'
]