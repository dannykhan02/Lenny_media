from .email_utils import send_email
from .email_templates import (
    booking_confirmation_template,
    admin_booking_alert_template,
    booking_status_update_template,
    booking_updated_template
)
from .quote_email_template import (
    get_client_confirmation_email,
    get_admin_alert_email,
    get_client_reschedule_email,
    get_client_cancellation_email,
    get_quote_sent_email,
    get_quote_accepted_email,    # NEW
    get_quote_rejected_email     # NEW
)
from .quote_service import QuoteService
from .cloudinary_service import (
    upload_image,
    upload_file,
    delete_image,
    get_cloudinary_config,
    upload_profile_picture,
    cleanup_old_profile_picture,
    generate_cloudinary_url
)

__all__ = [
    'send_email',
    'booking_confirmation_template',
    'admin_booking_alert_template',
    'booking_status_update_template',
    'booking_updated_template',
    'get_client_confirmation_email',
    'get_admin_alert_email',
    'get_client_reschedule_email',
    'get_client_cancellation_email',
    'get_quote_sent_email',
    'get_quote_accepted_email',    # NEW
    'get_quote_rejected_email',    # NEW
    'QuoteService',
    # Cloudinary services
    'upload_image',
    'upload_file',
    'delete_image',
    'get_cloudinary_config',
    'upload_profile_picture',
    'cleanup_old_profile_picture',
    'generate_cloudinary_url'
]