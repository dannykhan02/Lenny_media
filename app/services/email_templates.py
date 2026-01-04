"""
Email Templates Module
HTML email templates for booking notifications
Updated: No booking ID display, WhatsApp uses same phone number
"""
from datetime import datetime
from flask import current_app


# Color scheme matching the quote template
COLORS = {
    'primary': '#FF6B35',      # Vibrant Orange - Main brand color
    'secondary': '#004E89',    # Deep Blue - Professional accent
    'success': '#10B981',      # Green - Success states
    'warning': '#F59E0B',      # Amber - Warnings
    'danger': '#EF4444',       # Red - Cancellations
    'dark': '#1F2937',         # Dark Gray - Text
    'light': '#F9FAFB',        # Light Gray - Backgrounds
    'white': '#FFFFFF',
    'border': '#E5E7EB'
}


def get_studio_info():
    """
    Get studio information from Flask config
    """
    studio_info = {
        'name': current_app.config.get('BUSINESS_NAME', 'Lenny Media Photography Studio'),
        'phone': current_app.config.get('BUSINESS_PHONE', '+254 705 459768'),
        'email': current_app.config.get('BUSINESS_EMAIL', 'dannykhan614@gmail.com'),
        'address': current_app.config.get('BUSINESS_ADDRESS', 'Juja Square, 1st Floor, Next to the Highway, Juja, Kenya'),
        'website': current_app.config.get('BUSINESS_WEBSITE', 'https://lennymedia.co.ke'),
        'instagram': current_app.config.get('SOCIAL_INSTAGRAM', ''),
        'facebook': current_app.config.get('SOCIAL_FACEBOOK', ''),
        'tiktok': current_app.config.get('SOCIAL_TIKTOK', '')
    }
    
    # Use same phone number for WhatsApp and calls
    studio_info['whatsapp'] = studio_info['phone']
    
    return studio_info


def get_base_booking_template(content: str, title: str = None) -> str:
    """
    Base HTML template for booking emails matching quote template structure
    """
    studio_info = get_studio_info()
    if title is None:
        title = f"Booking - {studio_info['name']}"
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title}</title>
    <style>
        /* Reset styles */
        body, table, td, a {{
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}
        table, td {{
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }}
        img {{
            -ms-interpolation-mode: bicubic;
            border: 0;
            height: auto;
            line-height: 100%;
            outline: none;
            text-decoration: none;
        }}
        
        /* Base styles */
        body {{
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: {COLORS['light']};
            color: {COLORS['dark']};
            line-height: 1.6;
        }}
        
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: {COLORS['white']};
        }}
        
        .header {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
            color: {COLORS['white']};
            padding: 40px 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .content {{
            padding: 40px 30px;
        }}
        
        .greeting {{
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['dark']};
            margin-bottom: 20px;
        }}
        
        .message {{
            font-size: 15px;
            color: #4B5563;
            margin-bottom: 30px;
        }}
        
        .info-box {{
            background-color: {COLORS['light']};
            border-left: 4px solid {COLORS['primary']};
            padding: 20px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        
        .info-box h3 {{
            margin: 0 0 15px 0;
            font-size: 16px;
            color: {COLORS['dark']};
            font-weight: 600;
        }}
        
        .info-row {{
            display: table;
            width: 100%;
            margin: 10px 0;
            font-size: 14px;
            line-height: 1.5;
        }}
        
        .info-label {{
            display: table-cell;
            font-weight: 600;
            color: {COLORS['dark']};
            width: 160px;
            padding-right: 10px;
            vertical-align: top;
        }}
        
        .info-value {{
            display: table-cell;
            color: #6B7280;
            vertical-align: top;
        }}
        
        .warning-box {{
            background-color: #FEF3C7;
            border-left: 4px solid {COLORS['warning']};
            padding: 20px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        
        .danger-box {{
            background-color: #FEE2E2;
            border-left: 4px solid {COLORS['danger']};
            padding: 20px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        
        .success-box {{
            background-color: #D1FAE5;
            border-left: 4px solid {COLORS['success']};
            padding: 20px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, {COLORS['primary']} 0%, #FF8A5B 100%);
            color: {COLORS['white']} !important;
            padding: 14px 32px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 15px;
            margin: 20px 0;
        }}
        
        .contact-section {{
            background-color: {COLORS['light']};
            padding: 25px;
            margin: 30px 0;
            border-radius: 8px;
            border: 1px solid {COLORS['border']};
        }}
        
        .contact-section h3 {{
            margin: 0 0 15px 0;
            font-size: 16px;
            color: {COLORS['dark']};
        }}
        
        .contact-methods {{
            margin-top: 15px;
        }}
        
        .contact-item {{
            display: table;
            width: 100%;
            font-size: 14px;
            color: {COLORS['dark']};
            line-height: 1.5;
            margin-bottom: 12px;
        }}
        
        .contact-item:last-child {{
            margin-bottom: 0;
        }}
        
        .contact-icon {{
            display: table-cell;
            width: 25px;
            padding-right: 8px;
            vertical-align: top;
        }}
        
        .contact-label {{
            display: table-cell;
            font-weight: 600;
            width: 140px;
            padding-right: 10px;
            vertical-align: top;
        }}
        
        .contact-value {{
            display: table-cell;
            vertical-align: top;
        }}
        
        .contact-item a {{
            color: {COLORS['primary']};
            text-decoration: none;
            font-weight: 600;
        }}
        
        .booking-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #FFE4CC 0%, #FFD1B3 100%);
            color: {COLORS['primary']};
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 20px;
            border: 1px solid #FF6B35;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 6px 15px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .notes-box {{
            background: {COLORS['light']};
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
            border: 1px solid {COLORS['border']};
            border-left: 3px solid {COLORS['primary']};
        }}
        
        /* Mobile responsive styles */
        @media only screen and (max-width: 600px) {{
            .email-container {{
                width: 100% !important;
            }}
            
            .header {{
                padding: 30px 20px !important;
            }}
            
            .header h1 {{
                font-size: 24px !important;
            }}
            
            .header p {{
                font-size: 13px !important;
            }}
            
            .content {{
                padding: 30px 20px !important;
            }}
            
            .greeting {{
                font-size: 16px !important;
            }}
            
            .message {{
                font-size: 14px !important;
            }}
            
            .info-box,
            .warning-box,
            .danger-box,
            .success-box {{
                padding: 15px !important;
                margin: 20px 0 !important;
            }}
            
            .info-box h3 {{
                font-size: 15px !important;
            }}
            
            .info-row {{
                display: block !important;
            }}
            
            .info-label {{
                display: block !important;
                width: 100% !important;
                padding-right: 0 !important;
                margin-bottom: 4px !important;
            }}
            
            .info-value {{
                display: block !important;
                padding-left: 0 !important;
            }}
            
            .contact-section {{
                padding: 20px !important;
                margin: 20px 0 !important;
            }}
            
            .contact-item {{
                display: block !important;
                margin-bottom: 15px !important;
            }}
            
            .contact-icon {{
                display: inline !important;
                width: auto !important;
            }}
            
            .contact-label {{
                display: block !important;
                width: 100% !important;
                padding-right: 0 !important;
                margin-bottom: 4px !important;
                margin-top: 5px !important;
            }}
            
            .contact-value {{
                display: block !important;
                padding-left: 0 !important;
            }}
            
            .cta-button {{
                display: block !important;
                width: 100% !important;
                box-sizing: border-box !important;
                text-align: center !important;
                padding: 14px 20px !important;
            }}
            
            .booking-badge {{
                padding: 6px 15px !important;
                font-size: 11px !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        {content}
        {get_booking_email_footer()}
    </div>
</body>
</html>
"""


def get_booking_email_footer() -> str:
    """
    Standard footer for booking emails using studio info from config
    """
    studio_info = get_studio_info()
    
    # Build social media links if available
    footer_links = []
    if studio_info['website']:
        footer_links.append(f'<a href="{studio_info["website"]}" style="color: {COLORS["white"]}; text-decoration: none; margin: 0 10px; opacity: 0.8;">Website</a>')
    if studio_info['instagram']:
        footer_links.append(f'<a href="{studio_info["instagram"]}" style="color: {COLORS["white"]}; text-decoration: none; margin: 0 10px; opacity: 0.8;">Instagram</a>')
    if studio_info['facebook']:
        footer_links.append(f'<a href="{studio_info["facebook"]}" style="color: {COLORS["white"]}; text-decoration: none; margin: 0 10px; opacity: 0.8;">Facebook</a>')
    if studio_info['tiktok']:
        footer_links.append(f'<a href="{studio_info["tiktok"]}" style="color: {COLORS["white"]}; text-decoration: none; margin: 0 10px; opacity: 0.8;">TikTok</a>')
    
    links_html = " • ".join(footer_links) if footer_links else ""
    
    return f"""
        <div style="background-color: {COLORS['dark']}; color: {COLORS['white']}; padding: 30px; text-align: center; font-size: 13px;">
            <p style="margin: 0 0 10px 0; font-weight: 600; font-size: 16px;">{studio_info['name']}</p>
            <p style="margin: 5px 0; opacity: 0.9;">Professional Media Production Services</p>
            {f'''<p style="margin: 5px 0; opacity: 0.8;">{studio_info['address']}</p>''' if studio_info['address'] else ''}
            {f'''<div style="margin: 15px 0;">{links_html}</div>''' if links_html else ''}
            <p style="margin: 20px 0 0 0; opacity: 0.7; font-size: 12px;">
                © {datetime.now().year} {studio_info['name']}. All rights reserved.
            </p>
        </div>
"""


def get_whatsapp_link(phone: str) -> str:
    """
    Generate WhatsApp click-to-chat link from phone number
    Uses same phone number as calls
    """
    if not phone:
        return "#"
    
    # Clean phone number: remove spaces, plus signs, and hyphens
    clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    return f"https://wa.me/{clean_phone}"


# ============================================================================
# BOOKING CONFIRMATION EMAIL (Client)
# ============================================================================

def booking_confirmation_template(booking):
    """
    Generate HTML template for client booking confirmation email
    Updated: No booking ID display, WhatsApp uses same phone number
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    # Format additional notes if present
    notes_display = ""
    if booking.additional_notes:
        notes_display = f"""
            <div class="notes-box">
                <p style="margin: 0 0 10px 0; font-weight: 600; color: {COLORS['dark']}; font-size: 15px;">📝 Your Notes & Preferences:</p>
                <p style="margin: 0; color: #6B7280; line-height: 1.7; font-style: italic; padding: 12px; background: {COLORS['white']}; border-radius: 4px;">
                    "{booking.additional_notes}"
                </p>
                <p style="margin: 10px 0 0 0; font-size: 13px; color: #9CA3AF;">We've noted your preferences and will incorporate them into your session planning.</p>
            </div>
        """
    
    # Format time display
    time_display = ""
    if booking.preferred_time:
        time_display = f"""
            <div class="info-row">
                <span class="info-label">Preferred Time:</span>
                <span class="info-value" style="color: {COLORS['dark']}; font-weight: 600;">{booking.preferred_time.strftime('%I:%M %p')}</span>
            </div>
        """
    
    # Format location display
    location_display = ""
    if booking.location:
        location_display = f"""
            <div class="info-row">
                <span class="info-label">Location:</span>
                <span class="info-value">{booking.location}</span>
            </div>
        """
    
    # Format budget display
    budget_display = ""
    if booking.budget_range:
        budget_display = f"""
            <div class="info-row">
                <span class="info-label">Budget Range:</span>
                <span class="info-value" style="color: {COLORS['primary']}; font-weight: 600;">KES {booking.budget_range}</span>
            </div>
        """
    
    content = f"""
        <div class="header">
            <div class="booking-badge">✨ Booking Confirmed</div>
            <h1>🎬 Booking Request Received!</h1>
            <p>Thank you for choosing {studio_info['name']}</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {booking.client_name},</div>
            
            <div class="message">
                Thank you for reaching out to {studio_info['name']}! 🎥✨
                <br><br>
                We've successfully received your booking request and our team is already reviewing it. 
                We're excited about the opportunity to bring your vision to life.
            </div>
            
            <div class="success-box">
                <h3>✅ Your Booking Has Been Submitted</h3>
                <p style="margin: 0; color: #059669; font-weight: 600; font-size: 15px;">
                    We'll get back to you within 24 hours to confirm your session
                </p>
            </div>
            
            <div class="info-box">
                <h3>📋 Booking Summary</h3>
                <div class="info-row">
                    <span class="info-label">Name:</span>
                    <span class="info-value">{booking.client_name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Email:</span>
                    <span class="info-value">{booking.client_email}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Phone:</span>
                    <span class="info-value">{booking.client_phone}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Service Type:</span>
                    <span class="info-value" style="color: {COLORS['dark']}; font-weight: 600;">{booking.service_type}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Preferred Date:</span>
                    <span class="info-value">{booking.preferred_date.strftime('%A, %B %d, %Y')}</span>
                </div>
                {time_display}
                {location_display}
                {budget_display}
                <div class="info-row">
                    <span class="info-label">Booking Status:</span>
                    <span class="info-value" style="color: {COLORS['warning']}; font-weight: 700; text-transform: uppercase;">{booking.status.value if booking.status else 'PENDING'}</span>
                </div>
            </div>
            
            <div class="warning-box">
                <h3 style="color: #92400E;">📋 What Happens Next?</h3>
                <ul style="margin: 10px 0 0 20px; padding: 0; color: #92400E;">
                    <li style="margin: 5px 0;">Our team reviews your request within 24 hours</li>
                    <li style="margin: 5px 0;">We contact you to confirm availability and details</li>
                    <li style="margin: 5px 0;">You receive payment details to secure your booking</li>
                    <li style="margin: 5px 0;">Final preparations and session planning begins</li>
                </ul>
            </div>
            
            {notes_display}
            
            <div class="contact-section">
                <h3>📞 Need Immediate Assistance?</h3>
                <p style="margin: 0 0 15px 0; color: #6B7280; font-size: 14px;">
                    While we prepare your booking confirmation, feel free to reach out if you have any urgent questions 
                    or would like to discuss your project in more detail.
                </p>
                <div class="contact-methods">
                    {f'''<div class="contact-item">
                        <span class="contact-icon">📱</span>
                        <span class="contact-label">Call Us:</span>
                        <span class="contact-value"><a href="tel:{studio_info['phone']}">{studio_info['phone']}</a></span>
                    </div>''' if studio_info['phone'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">💬</span>
                        <span class="contact-label">WhatsApp:</span>
                        <span class="contact-value"><a href="{whatsapp_link}">Start a conversation</a></span>
                    </div>''' if studio_info['whatsapp'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">📍</span>
                        <span class="contact-label">Visit Us:</span>
                        <span class="contact-value">{studio_info['address']}</span>
                    </div>''' if studio_info['address'] else ''}
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: {COLORS['light']}; border-radius: 8px;">
                <p style="margin: 0; color: {COLORS['dark']}; font-size: 15px; font-weight: 600;">
                    We're excited to work with you! 🎬✨
                </p>
                <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 14px;">
                    Warm regards,<br>
                    <strong>The {studio_info['name']} Team</strong>
                </p>
            </div>
        </div>
"""
    
    return get_base_booking_template(content, f"Booking Confirmation - {studio_info['name']}")


# ============================================================================
# ADMIN BOOKING ALERT EMAIL
# ============================================================================

def admin_booking_alert_template(booking):
    """
    Generate HTML template for admin new booking alert email
    Updated: No booking ID display
    """
    studio_info = get_studio_info()
    
    # Format all booking details
    time_display = booking.preferred_time.strftime('%I:%M %p') if booking.preferred_time else "Not specified"
    
    content = f"""
        <div class="header">
            <div class="booking-badge" style="background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); color: {COLORS['danger']}; border-color: {COLORS['danger']};">
                🚨 NEW BOOKING • {booking.service_type.upper()}
            </div>
            <h1>🚨 New Booking Request</h1>
            <p>Action Required - Admin Review Needed</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello Admin,</div>
            
            <div class="message">
                A new booking request has just been submitted and requires your attention.
                Please log in to the admin dashboard to review and process this request.
            </div>
            
            <div class="info-box">
                <h3>📋 Client Details</h3>
                <div class="info-row">
                    <span class="info-label">Client Name:</span>
                    <span class="info-value">{booking.client_name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Email:</span>
                    <span class="info-value">{booking.client_email}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Phone:</span>
                    <span class="info-value"><a href="tel:{booking.client_phone}" style="color: {COLORS['primary']}; text-decoration: none; font-weight: 600;">{booking.client_phone}</a></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Service Type:</span>
                    <span class="info-value" style="color: {COLORS['dark']}; font-weight: 600;">{booking.service_type}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Event Date & Time:</span>
                    <span class="info-value">{booking.preferred_date.strftime('%A, %B %d, %Y')} at {time_display}</span>
                </div>
                {f'''<div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{booking.location}</span>
                </div>''' if booking.location else ''}
                {f'''<div class="info-row">
                    <span class="info-label">Budget Range:</span>
                    <span class="info-value" style="color: {COLORS['primary']}; font-weight: 600;">KES {booking.budget_range}</span>
                </div>''' if booking.budget_range else ''}
                <div class="info-row">
                    <span class="info-label">Booking Status:</span>
                    <span class="info-value" style="color: {COLORS['warning']}; font-weight: 700; text-transform: uppercase;">{booking.status.value if booking.status else 'PENDING'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Submitted:</span>
                    <span class="info-value">{booking.created_at.strftime('%Y-%m-%d at %I:%M %p')}</span>
                </div>
            </div>
            
            {f'''<div class="notes-box">
                <h3 style="color: {COLORS['dark']}; margin-top: 0; font-size: 15px;">📝 CLIENT NOTES & PREFERENCES</h3>
                <p style="margin: 0; white-space: pre-wrap; color: #6B7280; line-height: 1.7; padding: 15px; background: {COLORS['white']}; border-radius: 4px; border: 1px solid {COLORS['border']};">
                    {booking.additional_notes}
                </p>
            </div>''' if booking.additional_notes else '''<div class="notes-box">
                <h3 style="color: {COLORS['dark']}; margin-top: 0; font-size: 15px;">📝 Client Notes:</h3>
                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-style: italic;">No additional notes provided by client.</p>
            </div>'''}
            
            <div class="warning-box">
                <h3 style="color: #92400E;">⏰ IMMEDIATE ACTION REQUIRED</h3>
                <p style="margin: 8px 0 0 0; color: #92400E; line-height: 1.7;">
                    <strong>✓ Contact Client:</strong> Respond within <strong>24 hours</strong> to confirm availability<br>
                    <strong>✓ Review Details:</strong> Check client preferences and budget range<br>
                    <strong>✓ Update Status:</strong> Mark as confirmed once details are finalized<br>
                    <strong>✓ Assign Team:</strong> Allocate photographer/videographer if needed
                </p>
            </div>
            
            <div style="background-color: {COLORS['light']}; padding: 20px; border-radius: 8px; margin-top: 30px; border: 1px solid {COLORS['border']}; text-align: center;">
                <p style="margin: 0; color: #6B7280; font-size: 14px;">
                    <strong>Response Target:</strong> 24 hours • <strong>Status:</strong> PENDING
                </p>
            </div>
        </div>
"""
    
    return get_base_booking_template(content, f"New Booking Alert - {studio_info['name']}")


# ============================================================================
# BOOKING STATUS UPDATE EMAIL
# ============================================================================

def booking_status_update_template(booking, old_status, new_status):
    """
    Generate HTML template for booking status update email
    Updated: No booking ID display
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    # Status-specific configurations
    status_configs = {
        'CONFIRMED': {
            'title': '🎉 Booking Confirmed!',
            'header_gradient': f"linear-gradient(135deg, {COLORS['success']} 0%, #059669 100%)",
            'accent_color': COLORS['success'],
            'badge_bg': f"linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%)",
            'badge_color': '#065F46',
            'message': f"""
                <p style="color: #4B5563; line-height: 1.8;">Great news! Your <strong style="color: {COLORS['success']};">{booking.service_type}</strong> session has been <strong style="color: {COLORS['success']};">officially confirmed</strong>.</p>
                <p style="color: #6B7280; line-height: 1.8;">We're excited to work with you on <strong>{booking.preferred_date.strftime('%A, %B %d, %Y')}</strong>
                {f"at <strong>{booking.preferred_time.strftime('%I:%M %p')}</strong>" if booking.preferred_time else ""}.</p>
            """,
            'next_steps': """
                <div class="success-box">
                    <h3>✅ What's Next?</h3>
                    <p style="margin: 0; color: #065F46; line-height: 1.8;">
                        <strong>✓ Within 24 Hours:</strong> Our team will contact you with final details<br>
                        <strong>✓ Payment:</strong> You'll receive payment instructions to secure your booking<br>
                        <strong>✓ Preparation:</strong> We'll send a session preparation guide<br>
                        <strong>✓ Final Confirmation:</strong> All details will be confirmed 48 hours before
                    </p>
                </div>
            """
        },
        'CANCELLED': {
            'title': '❌ Booking Cancelled',
            'header_gradient': f"linear-gradient(135deg, {COLORS['danger']} 0%, #DC2626 100%)",
            'accent_color': COLORS['danger'],
            'badge_bg': f"linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%)",
            'badge_color': '#7F1D1D',
            'message': f"""
                <p style="color: #4B5563; line-height: 1.8;">We regret to inform you that your booking scheduled for <strong>{booking.preferred_date.strftime('%A, %B %d, %Y')}</strong> has been cancelled.</p>
                <p style="color: #6B7280; line-height: 1.8;">If this was unexpected or you'd like to reschedule, please contact our team immediately.</p>
            """,
            'next_steps': """
                <div class="warning-box">
                    <h3 style="color: #92400E;">📝 Your Options</h3>
                    <p style="margin: 0; color: #92400E; line-height: 1.8;">
                        <strong>✓ Reschedule:</strong> Contact us to book another date<br>
                        <strong>✓ Alternatives:</strong> Discuss other services that might work better<br>
                        <strong>✓ Refund:</strong> Request a refund if applicable<br>
                        <strong>✓ Future Bookings:</strong> We'd love to work with you another time
                    </p>
                </div>
            """
        },
        'COMPLETED': {
            'title': '🎊 Session Completed!',
            'header_gradient': f"linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)",
            'accent_color': '#7C3AED',
            'badge_bg': f"linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%)",
            'badge_color': '#5B21B6',
            'message': f"""
                <p style="color: #4B5563; line-height: 1.8;">Thank you for choosing <strong>{studio_info['name']}</strong> for your {booking.service_type}!</p>
                <p style="color: #6B7280; line-height: 1.8;">We hope you had an amazing experience during your session on <strong>{booking.preferred_date.strftime('%B %d, %Y')}</strong>.</p>
            """,
            'next_steps': """
                <div class="info-box">
                    <h3>📦 What Happens Next</h3>
                    <p style="margin: 0; color: #1F2937; line-height: 1.8;">
                        <strong>✓ Editing:</strong> Your photos/videos are being professionally edited<br>
                        <strong>✓ Preview:</strong> You'll receive a preview within <strong style="color: {COLORS['primary']};">3-5 business days</strong><br>
                        <strong>✓ Delivery:</strong> Final delivery within <strong style="color: {COLORS['primary']};">7-14 business days</strong><br>
                        <strong>✓ Feedback:</strong> We'd love your feedback - please consider leaving a review!
                    </p>
                </div>
            """
        }
    }
    
    config = status_configs.get(new_status, {
        'title': f'ℹ️ Booking Status Updated: {new_status}',
        'header_gradient': f"linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%)",
        'accent_color': COLORS['primary'],
        'badge_bg': f"linear-gradient(135deg, #FFE4CC 0%, #FFD1B3 100%)",
        'badge_color': COLORS['primary'],
        'message': f"""
            <p style='color: #4B5563; line-height: 1.8;'>Your booking status has been updated from <strong style='color: #9CA3AF;'>{old_status}</strong> to <strong style='color: {COLORS['primary']};'>{new_status}</strong>.</p>
        """,
        'next_steps': """
            <div class="info-box">
                <h3>❓ Questions?</h3>
                <p style="margin: 0; color: #1F2937; line-height: 1.8;">
                    If you have any questions about this status change or need further assistance, please don't hesitate to contact us.
                </p>
            </div>
        """
    })
    
    # Format booking details
    time_display = booking.preferred_time.strftime('%I:%M %p') if booking.preferred_time else "Not specified"
    location_display = booking.location if booking.location else "Not specified"
    budget_display = f"KES {booking.budget_range}" if booking.budget_range else "Not specified"
    
    content = f"""
        <div class="header" style="background: {config['header_gradient']};">
            <div class="booking-badge" style="background: {config['badge_bg']}; color: {config['badge_color']}; border-color: {config['accent_color']};">
                Status Update • {new_status}
            </div>
            <h1>{config['title']}</h1>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {booking.client_name},</div>
            
            {config['message']}
            
            <!-- Status Change Overview -->
            <div style="background: {COLORS['light']}; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid {COLORS['border']}; border-left: 4px solid {config['accent_color']};">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                    <div style="font-weight: 600; color: #6B7280; font-size: 14px;">Previous Status:</div>
                    <div class="status-badge" style="background: {COLORS['light']}; color: #9CA3AF;">{old_status}</div>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="font-weight: 600; color: #6B7280; font-size: 14px;">New Status:</div>
                    <div class="status-badge" style="background: {config['badge_bg']}; color: {config['badge_color']}; border: 1px solid {config['accent_color']};">{new_status}</div>
                </div>
            </div>
            
            <!-- Booking Details -->
            <div class="info-box">
                <h3>📋 Booking Details</h3>
                <div class="info-row">
                    <span class="info-label">Service Type:</span>
                    <span class="info-value" style="color: {COLORS['dark']}; font-weight: 600;">{booking.service_type}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Date:</span>
                    <span class="info-value">{booking.preferred_date.strftime('%A, %B %d, %Y')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Time:</span>
                    <span class="info-value">{time_display}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{location_display}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Budget Range:</span>
                    <span class="info-value" style="color: {COLORS['primary']}; font-weight: 600;">{budget_display}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Updated On:</span>
                    <span class="info-value">{booking.updated_at.strftime('%B %d, %Y at %I:%M %p')}</span>
                </div>
            </div>
            
            {f'''<div class="notes-box">
                <h3 style="color: {COLORS['dark']}; margin-top: 0; font-size: 15px;">📝 YOUR NOTES & PREFERENCES</h3>
                <p style="margin: 0; color: #6B7280; line-height: 1.7; padding: 15px; background: {COLORS['white']}; border-radius: 4px; border: 1px solid {COLORS['border']}; font-style: italic;">
                    "{booking.additional_notes}"
                </p>
            </div>''' if booking.additional_notes else ''}
            
            {config['next_steps']}
            
            <div class="contact-section">
                <h3>📞 Questions or Need Assistance?</h3>
                <p style="margin: 0 0 15px 0; color: #6B7280; font-size: 14px;">
                    Our team is ready to assist you with any questions or special requests.
                </p>
                <div class="contact-methods">
                    {f'''<div class="contact-item">
                        <span class="contact-icon">📱</span>
                        <span class="contact-label">Call Us:</span>
                        <span class="contact-value"><a href="tel:{studio_info['phone']}">{studio_info['phone']}</a></span>
                    </div>''' if studio_info['phone'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">💬</span>
                        <span class="contact-label">WhatsApp:</span>
                        <span class="contact-value"><a href="{whatsapp_link}">Start a conversation</a></span>
                    </div>''' if studio_info['whatsapp'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">✉️</span>
                        <span class="contact-label">Email:</span>
                        <span class="contact-value"><a href="mailto:{studio_info['email']}">{studio_info['email']}</a></span>
                    </div>''' if studio_info['email'] else ''}
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: {COLORS['light']}; border-radius: 8px;">
                <p style="margin: 0; color: {COLORS['dark']}; font-size: 15px; font-weight: 600;">
                    Thank you for choosing {studio_info['name']} 🎬
                </p>
                <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 14px;">
                    Warm regards,<br>
                    <strong>The {studio_info['name']} Team</strong>
                </p>
            </div>
        </div>
"""
    
    return get_base_booking_template(content, f"Booking Status Update - {studio_info['name']}")


# ============================================================================
# BOOKING UPDATED EMAIL (Details changed)
# ============================================================================

def booking_updated_template(booking, updates, updated_by):
    """
    Generate HTML template for when booking details are updated (excluding status changes)
    Updated: No booking ID display
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    # Create update summary
    update_summary = []
    for field, (old_value, new_value) in updates.items():
        if field == 'preferred_date' and old_value:
            old_value = old_value.strftime('%B %d, %Y')
            new_value = new_value.strftime('%B %d, %Y')
        elif field == 'preferred_time' and old_value:
            old_value = old_value.strftime('%I:%M %p') if hasattr(old_value, 'strftime') else old_value
            new_value = new_value.strftime('%I:%M %p') if hasattr(new_value, 'strftime') else new_value
        elif field == 'budget_range':
            old_value = f"KES {old_value}" if old_value else "Not specified"
            new_value = f"KES {new_value}" if new_value else "Not specified"
        
        field_display = field.replace('_', ' ').title()
        update_summary.append(f"""
            <div class="info-row" style="background: {COLORS['light']}; padding: 12px; border-radius: 4px; margin-bottom: 8px;">
                <span class="info-label" style="font-weight: 600;">{field_display}:</span>
                <span class="info-value" style="text-align: left;">
                    <span style="color: {COLORS['danger']}; text-decoration: line-through;">{old_value if old_value else 'Not set'}</span> 
                    → 
                    <span style="color: {COLORS['success']}; font-weight: 600;">{new_value if new_value else 'Not set'}</span>
                </span>
            </div>
        """)
    
    content = f"""
        <div class="header">
            <div class="booking-badge">📝 Booking Updated</div>
            <h1>🔄 Booking Details Modified</h1>
            <p>Your booking has been updated by our team</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {booking.client_name},</div>
            
            <div class="message">
                Our team has updated some details of your <strong>{booking.service_type}</strong> booking to better accommodate your needs.
            </div>
            
            <div class="info-box">
                <h3>📋 Updated Information</h3>
                {"".join(update_summary)}
                
                <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid {COLORS['border']}; color: #6B7280; font-size: 14px;">
                    <p style="margin: 0;"><strong>Updated by:</strong> {updated_by}<br>
                    <strong>Updated on:</strong> {booking.updated_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
            
            <!-- Current Booking Status -->
            <div style="background: {COLORS['light']}; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid {COLORS['border']}; text-align: center;">
                <p style="margin: 0 0 10px 0; font-weight: 600; color: {COLORS['dark']}; font-size: 15px;">Current Booking Status</p>
                <div class="status-badge" style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); color: #92400E; border: 2px solid {COLORS['warning']};">
                    {booking.status.value if booking.status else 'PENDING'}
                </div>
            </div>
            
            <div class="warning-box">
                <h3 style="color: #92400E;">❓ Questions About These Changes?</h3>
                <p style="margin: 8px 0 0 0; color: #92400E; line-height: 1.8;">
                    If you have any questions or need to discuss these modifications, please contact us:<br>
                    📞 <a href="tel:{studio_info['phone']}" style="color: #92400E; text-decoration: none; font-weight: 600;">{studio_info['phone']}</a><br>
                    📧 <a href="mailto:{studio_info['email']}" style="color: #92400E; text-decoration: none; font-weight: 600;">{studio_info['email']}</a>
                </p>
            </div>
            
            <div class="contact-section">
                <h3>💬 Need to Discuss These Changes?</h3>
                <p style="margin: 0 0 15px 0; color: #6B7280; font-size: 14px;">
                    If these changes don't work for you, please reply to this email or contact us directly to discuss alternatives.
                </p>
                <div class="contact-methods">
                    {f'''<div class="contact-item">
                        <span class="contact-icon">💬</span>
                        <span class="contact-label">WhatsApp:</span>
                        <span class="contact-value"><a href="{whatsapp_link}">Chat with us</a></span>
                    </div>''' if studio_info['whatsapp'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">📱</span>
                        <span class="contact-label">Call Us:</span>
                        <span class="contact-value"><a href="tel:{studio_info['phone']}">{studio_info['phone']}</a></span>
                    </div>''' if studio_info['phone'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">✉️</span>
                        <span class="contact-label">Email:</span>
                        <span class="contact-value"><a href="mailto:{studio_info['email']}">{studio_info['email']}</a></span>
                    </div>''' if studio_info['email'] else ''}
                </div>
            </div>
            
            <p style="margin-top: 30px; color: #6B7280; font-size: 15px; line-height: 1.7; text-align: center;">
                <em>If these changes don't work for you, please reply to this email within 24 hours.</em>
            </p>
        </div>
"""
    
    return get_base_booking_template(content, f"Booking Updated - {studio_info['name']}")