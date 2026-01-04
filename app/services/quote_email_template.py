"""
Email templates for Quote Service
Handles all email communications for quote lifecycle events
Enhanced with full mobile responsiveness and price estimation
"""

from datetime import datetime
from typing import Dict
from flask import current_app


# Color scheme for Lenny Studio (Professional media studio theme)
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
    Get studio information from Flask config - matches what email_template.py uses
    """
    studio_info = {
        'name': current_app.config.get('BUSINESS_NAME', 'Lenny Studio'),
        'phone': current_app.config.get('BUSINESS_PHONE', ''),
        'email': current_app.config.get('BUSINESS_EMAIL', ''),
        'address': current_app.config.get('BUSINESS_ADDRESS', ''),
        'website': current_app.config.get('BUSINESS_WEBSITE', ''),
        'instagram': current_app.config.get('SOCIAL_INSTAGRAM', ''),
        'facebook': current_app.config.get('SOCIAL_FACEBOOK', ''),
        'tiktok': current_app.config.get('SOCIAL_TIKTOK', '')
    }
    
    # WhatsApp Uses Same Phone Number as Calls
    studio_info['whatsapp'] = studio_info['phone']

    return studio_info


def get_base_template(content: str, title: str = None) -> str:
    """
    Base HTML template wrapper for all emails with enhanced mobile responsiveness
    """
    studio_info = get_studio_info()
    if title is None:
        title = studio_info['name']
    
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
        
        .services-list {{
            margin: 10px 0;
            padding: 0;
            list-style: none;
        }}
        
        .services-list li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
            color: #6B7280;
            font-size: 14px;
        }}
        
        .services-list li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: {COLORS['primary']};
            font-weight: bold;
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
        
        .social-links {{
            text-align: center;
            margin: 25px 0;
            padding: 20px 0;
            border-top: 1px solid {COLORS['border']};
            border-bottom: 1px solid {COLORS['border']};
        }}
        
        .social-link {{
            display: inline-block;
            padding: 10px 20px;
            background-color: {COLORS['light']};
            color: {COLORS['dark']};
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            margin: 5px;
        }}
        
        .footer {{
            background-color: {COLORS['dark']};
            color: {COLORS['white']};
            padding: 30px;
            text-align: center;
            font-size: 13px;
        }}
        
        .footer-links {{
            margin: 15px 0;
        }}
        
        .footer-link {{
            color: {COLORS['white']};
            text-decoration: none;
            margin: 0 10px;
            opacity: 0.8;
        }}
        
        .divider {{
            height: 1px;
            background-color: {COLORS['border']};
            margin: 30px 0;
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
            
            .social-links {{
                padding: 15px 0 !important;
            }}
            
            .social-link {{
                display: block !important;
                margin: 8px 0 !important;
                padding: 12px 20px !important;
            }}
            
            .footer {{
                padding: 25px 20px !important;
            }}
            
            .footer-links {{
                margin: 12px 0 !important;
            }}
            
            .footer-link {{
                display: inline-block !important;
                margin: 5px 8px !important;
            }}
        }}
        
        /* Small mobile (iPhone SE, etc) */
        @media only screen and (max-width: 375px) {{
            .header {{
                padding: 25px 15px !important;
            }}
            
            .header h1 {{
                font-size: 22px !important;
            }}
            
            .content {{
                padding: 25px 15px !important;
            }}
            
            .info-box,
            .warning-box,
            .danger-box,
            .success-box,
            .contact-section {{
                padding: 12px !important;
            }}
            
            .cta-button {{
                padding: 12px 16px !important;
                font-size: 14px !important;
            }}
        }}
        
        /* Outlook-specific fixes */
        .ExternalClass {{
            width: 100%;
        }}
        
        .ExternalClass,
        .ExternalClass p,
        .ExternalClass span,
        .ExternalClass font,
        .ExternalClass td,
        .ExternalClass div {{
            line-height: 100%;
        }}
    </style>
    <!--[if mso]>
    <style type="text/css">
        .info-row,
        .contact-item {{
            display: block !important;
        }}
        .info-label,
        .contact-label {{
            display: block !important;
            width: 100% !important;
        }}
        .info-value,
        .contact-value {{
            display: block !important;
        }}
    </style>
    <![endif]-->
</head>
<body>
    <div class="email-container">
        {content}
        {get_footer()}
    </div>
</body>
</html>
"""


def get_footer() -> str:
    """
    Standard footer for all emails - matches email_template.py style
    """
    studio_info = get_studio_info()
    
    footer_links = []
    if studio_info['website']:
        footer_links.append(f'<a href="{studio_info["website"]}" class="footer-link">Website</a>')
    if studio_info['instagram']:
        footer_links.append(f'<a href="{studio_info["instagram"]}" class="footer-link">Instagram</a>')
    if studio_info['facebook']:
        footer_links.append(f'<a href="{studio_info["facebook"]}" class="footer-link">Facebook</a>')
    if studio_info['tiktok']:
        footer_links.append(f'<a href="{studio_info["tiktok"]}" class="footer-link">TikTok</a>')
    
    links_html = " • ".join(footer_links) if footer_links else ""
    
    return f"""
        <div class="footer">
            <p style="margin: 0 0 10px 0; font-weight: 600; font-size: 16px;">{studio_info['name']}</p>
            <p style="margin: 5px 0; opacity: 0.9;">Professional Media Production Services</p>
            {f'''<p style="margin: 5px 0; opacity: 0.8;">{studio_info['address']}</p>''' if studio_info['address'] else ''}
            {f'''<div class="footer-links">{links_html}</div>''' if links_html else ''}
            <p style="margin: 20px 0 0 0; opacity: 0.7; font-size: 12px;">
                © {datetime.now().year} {studio_info['name']}. All rights reserved.
            </p>
        </div>
"""


def format_services_list(services: list, show_estimate_notice: bool = True) -> str:
    """
    Format selected services with pricing as clean HTML list
    NOW INCLUDES PRICING from enriched service data
    
    Args:
        services: List of service dictionaries with pricing
        show_estimate_notice: Whether to show "prices are estimates" notice
    """
    if not services:
        return "<p style='color: #6B7280; font-size: 14px;'>No services specified</p>"
    
    # Add estimate notice at the top if requested
    estimate_notice = ""
    if show_estimate_notice:
        estimate_notice = f"""
        <div style="background: #FEF3C7; padding: 12px; border-radius: 6px; margin-bottom: 15px; border-left: 3px solid {COLORS['warning']};">
            <p style="margin: 0; font-size: 13px; color: #92400E; font-weight: 500;">
                💡 <strong>Note:</strong> Prices shown are estimates based on typical projects. 
                Your final quote may vary based on specific requirements, duration, and complexity.
            </p>
        </div>
        """
    
    services_html = ""
    for service in services:
        if isinstance(service, dict):
            title = service.get('title', 'Unknown Service')
            price_range = service.get('price_range', '')
            category = service.get('category', '')
            features = service.get('features', [])
            
            # Category badge
            category_badge = ""
            if category:
                category_colors = {
                    'photography': '#10B981',
                    'videography': '#3B82F6',
                }
                category_color = category_colors.get(category.lower(), '#6B7280')
                category_badge = f"""
                <span style="display: inline-block; background: {category_color}; 
                             color: white; padding: 2px 8px; border-radius: 4px; 
                             font-size: 11px; font-weight: 600; margin-left: 8px; text-transform: uppercase;">
                    {category}
                </span>
                """
            
            # Features list (show first 3)
            features_html = ""
            if features and len(features) > 0:
                features_items = "".join([
                    f"<li style='font-size: 12px; color: #6B7280; margin: 3px 0;'>✓ {feat}</li>"
                    for feat in features[:3]
                ])
                features_html = f"""
                <ul style="margin: 5px 0 0 20px; padding: 0; list-style: none;">
                    {features_items}
                </ul>
                """
            
            services_html += f"""
            <li style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #E5E7EB;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                    <strong style="font-size: 15px; color: {COLORS['dark']};">{title}</strong>
                    {category_badge}
                </div>
                {f'''<div style="margin-top: 6px;">
                    <span style="color: {COLORS['primary']}; font-weight: 600; font-size: 14px;">
                        💰 {price_range}
                    </span>
                </div>''' if price_range else ''}
                {features_html}
            </li>
            """
        else:
            # Legacy string format
            services_html += f"<li style='margin-bottom: 12px;'>{str(service)}</li>"
    
    return f"""
    {estimate_notice}
    <ul class='services-list' style="margin: 0; padding: 0; list-style: none;">
        {services_html}
    </ul>
    """


def get_price_estimate_box(price_estimate: Dict, context: str = "quote") -> str:
    """
    Generate a price estimate display box with contextual messaging.
    
    Args:
        price_estimate: Dictionary with 'formatted', 'service_count', 'min', 'max'
        context: 'quote' (initial), 'sent' (formal quote), or 'accepted' (confirmed)
    """
    if not price_estimate or not price_estimate.get('formatted'):
        return ""
    
    # Contextual messages based on quote status
    context_messages = {
        'quote': {
            'title': '💰 Estimated Price Range',
            'subtitle': 'Based on selected services. Final quote may vary.',
            'bg_gradient': f"linear-gradient(135deg, {COLORS['primary']} 0%, #FF8A5B 100%)",
            'note': 'This is a preliminary estimate. We\'ll provide a detailed breakdown in your formal quote.'
        },
        'sent': {
            'title': '💵 Your Custom Quote',
            'subtitle': 'Detailed pricing for your project',
            'bg_gradient': f"linear-gradient(135deg, {COLORS['success']} 0%, #059669 100%)",
            'note': 'This quote is valid for the period specified above.'
        },
        'accepted': {
            'title': '✅ Confirmed Booking Amount',
            'subtitle': 'Final agreed pricing',
            'bg_gradient': f"linear-gradient(135deg, {COLORS['success']} 0%, #047857 100%)",
            'note': 'This is the confirmed amount for your booking. Payment details will follow.'
        }
    }
    
    msg = context_messages.get(context, context_messages['quote'])
    
    return f"""
    <div class="info-box" style="background: {msg['bg_gradient']}; 
                                  border-left: none; color: white; margin: 25px 0;">
        <h3 style="color: white; margin: 0 0 10px 0; font-size: 18px;">{msg['title']}</h3>
        <p style="font-size: 28px; font-weight: 700; margin: 0; color: white; letter-spacing: -0.5px;">
            {price_estimate['formatted']}
        </p>
        <p style="font-size: 14px; margin: 10px 0 0 0; opacity: 0.95; font-weight: 500;">
            {msg['subtitle']}
        </p>
        <p style="font-size: 12px; margin: 10px 0 0 0; opacity: 0.85; font-style: italic;">
            {msg['note']}
        </p>
    </div>
"""


def get_whatsapp_link(phone: str) -> str:
    """
    Generate WhatsApp click-to-chat link WITHOUT pre-filled message
    Cleaner approach - let conversation happen naturally
    
    WhatsApp Uses Same Phone Number as Calls: +254 705 459768
    """
    if not phone:
        return "#"
    
    # Clean the phone number for WhatsApp URL
    # Remove all spaces, keep the plus sign for country code
    clean_phone = phone.replace(' ', '').replace('-', '')
    
    # WhatsApp requires country code without leading '+' in URL
    whatsapp_number = clean_phone.replace('+', '')
    
    return f"https://wa.me/{whatsapp_number}"


# ============================================================================
# CLIENT CONFIRMATION EMAIL (POST Request)
# ============================================================================

def get_client_confirmation_email(quote_data: Dict) -> Dict[str, str]:
    """
    Email sent to client after successful quote submission
    UPDATED: Shows service pricing and estimate
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    # Calculate and display price estimate with clear messaging
    price_estimate_html = ""
    if quote_data.get('price_estimate'):
        price_estimate_html = get_price_estimate_box(quote_data['price_estimate'], context='quote')
    
    content = f"""
        <div class="header">
            <h1>🎬 Quote Request Received!</h1>
            <p>Thank you for choosing {studio_info['name']}</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {quote_data.get('client_name', 'Valued Client')},</div>
            
            <div class="message">
                Thank you for reaching out to {studio_info['name']}! 🎥✨
                <br><br>
                We've successfully received your quote request and our team is already reviewing it. 
                We're excited about the opportunity to bring your vision to life.
            </div>
            
            <div class="success-box">
                <h3>✅ Your Request Has Been Submitted</h3>
                <p style="margin: 0; color: #059669; font-weight: 600; font-size: 15px;">
                    We'll get back to you within 24 hours with a detailed quote
                </p>
            </div>
            
            {price_estimate_html}
            
            <div class="info-box">
                <h3>📋 Quote Summary</h3>
                <div class="info-row">
                    <span class="info-label">Name:</span>
                    <span class="info-value">{quote_data.get('client_name', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Email:</span>
                    <span class="info-value">{quote_data.get('client_email', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Phone:</span>
                    <span class="info-value">{quote_data.get('client_phone', 'N/A')}</span>
                </div>
                {f'''<div class="info-row">
                    <span class="info-label">Company:</span>
                    <span class="info-value">{quote_data.get('company_name')}</span>
                </div>''' if quote_data.get('company_name') else ''}
                <div class="info-row">
                    <span class="info-label">Event Date:</span>
                    <span class="info-value">{quote_data.get('event_date', 'Not specified')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Event Time:</span>
                    <span class="info-value">{quote_data.get('event_time', 'Not specified')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{quote_data.get('event_location', 'Not specified')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Your Budget:</span>
                    <span class="info-value">{quote_data.get('budget_range', 'Not specified')}</span>
                </div>
            </div>
            
            <div class="warning-box" style="background-color: #FEF3C7;">
                <h3 style="color: #92400E;">📋 What Happens Next?</h3>
                <ul style="margin: 10px 0 0 20px; padding: 0; color: #92400E;">
                    <li style="margin: 5px 0;">Our team will review your requirements in detail</li>
                    <li style="margin: 5px 0;">We'll prepare a customized quote with exact pricing</li>
                    <li style="margin: 5px 0;">You'll receive the formal quote within 24 hours</li>
                    <li style="margin: 5px 0;">The final price may differ based on your specific needs</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3>🎬 Selected Services & Pricing</h3>
                {format_services_list(quote_data.get('selected_services', []), show_estimate_notice=True)}
            </div>
            
            <div class="contact-section">
                <h3>📞 Need Immediate Assistance?</h3>
                <p style="margin: 0 0 15px 0; color: #6B7280; font-size: 14px;">
                    While we prepare your detailed quote, feel free to reach out if you have any urgent questions 
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
    
    return {
        'subject': f'Quote Request Received - {studio_info["name"]}',
        'html': get_base_template(content, f"Quote Confirmation - {studio_info['name']}"),
        'recipient': quote_data.get('client_email')
    }


# ============================================================================
# ADMIN ALERT EMAIL (POST Request)
# ============================================================================

def get_admin_alert_email(quote_data: Dict) -> Dict[str, str]:
    """
    Email sent to admin when new quote is submitted
    UPDATED: Shows service pricing for admin reference
    """
    studio_info = get_studio_info()
    has_conflict = quote_data.get('has_conflict', False)
    
    # Price estimate for admin reference
    price_estimate_html = ""
    if quote_data.get('price_estimate'):
        estimate = quote_data['price_estimate']
        if estimate.get('formatted'):
            min_val = estimate.get('min', 0)
            max_val = estimate.get('max', 0)
            price_estimate_html = f"""
            <div class="info-row">
                <span class="info-label">Est. Price Range:</span>
                <span class="info-value" style="font-weight: 600; color: {COLORS['success']};">
                    {estimate['formatted']}
                </span>
            </div>
            <div class="info-row">
                <span class="info-label">Client Budget:</span>
                <span class="info-value" style="color: {'#059669' if quote_data.get('budget_range') and 'budget matches' else '#92400E'};">
                    {quote_data.get('budget_range', 'Not specified')}
                    {' ✓ Within range' if min_val and quote_data.get('budget_range') and str(min_val) in quote_data.get('budget_range', '') else ''}
                </span>
            </div>
            """
    
    conflict_warning = ""
    if has_conflict:
        conflict_warning = f"""
            <div class="warning-box">
                <h3>⚠️ Time Conflict Detected</h3>
                <p style="margin: 0; color: #92400E; font-weight: 600;">
                    This quote conflicts with {quote_data.get('conflicting_count', 0)} existing quote(s) 
                    on the same date/time. Please review and resolve immediately.
                </p>
            </div>
        """
    
    content = f"""
        <div class="header">
            <h1>🚨 New Quote Request</h1>
            <p>Action Required - Admin Review Needed</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello Admin,</div>
            
            <div class="message">
                A new quote request has just been submitted and requires your attention.
                Please log in to the admin dashboard to review and process this request.
            </div>
            
            {conflict_warning}
            
            <div class="info-box">
                <h3>📋 Client Details</h3>
                <div class="info-row">
                    <span class="info-label">Client Name:</span>
                    <span class="info-value">{quote_data.get('client_name', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Email:</span>
                    <span class="info-value">{quote_data.get('client_email', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Phone:</span>
                    <span class="info-value">{quote_data.get('client_phone', 'N/A')}</span>
                </div>
                {f'''<div class="info-row">
                    <span class="info-label">Company:</span>
                    <span class="info-value">{quote_data.get('company_name')}</span>
                </div>''' if quote_data.get('company_name') else ''}
                <div class="info-row">
                    <span class="info-label">Event Date & Time:</span>
                    <span class="info-value">{quote_data.get('event_date', 'N/A')} at {quote_data.get('event_time', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{quote_data.get('event_location', 'Not specified')}</span>
                </div>
                {price_estimate_html}
                <div class="info-row">
                    <span class="info-label">Submitted:</span>
                    <span class="info-value">{quote_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}</span>
                </div>
            </div>
            
            <div class="info-box">
                <h3>🎬 Requested Services with Pricing</h3>
                {format_services_list(quote_data.get('selected_services', []), show_estimate_notice=False)}
            </div>
            
            {f'''<div class="info-box">
                <h3>📝 Project Description</h3>
                <p style="margin: 0; color: #6B7280; font-size: 14px; white-space: pre-line;">
                    {quote_data.get('project_description')}
                </p>
            </div>''' if quote_data.get('project_description') else ''}
            
            <div class="info-box">
                <h3>👉 Action Required</h3>
                <ul style="margin: 0; padding-left: 20px; color: #6B7280;">
                    <li style="margin: 8px 0;">Review the complete request details</li>
                    <li style="margin: 8px 0;">Check service pricing against client budget</li>
                    <li style="margin: 8px 0;">Resolve any time conflicts if present</li>
                    <li style="margin: 8px 0;">Prepare and send a detailed quote</li>
                    <li style="margin: 8px 0;">Update the quote status accordingly</li>
                    {f'<li style="margin: 8px 0; color: {COLORS["warning"]}; font-weight: 600;">⚠️ Reschedule if conflict cannot be resolved</li>' if has_conflict else ''}
                </ul>
            </div>
            
            <div style="background-color: {COLORS['light']}; padding: 20px; border-radius: 8px; margin-top: 30px;">
                <p style="margin: 0; color: #6B7280; font-size: 14px; text-align: center;">
                    <strong>Response Target:</strong> 24 hours • <strong>Status:</strong> PENDING • <strong>Quote ID:</strong> #{quote_data.get('id', 'N/A')}
                </p>
            </div>
        </div>
"""
    
    return {
        'subject': f'🚨 New Quote Request - {quote_data.get("client_name")} {"[CONFLICT]" if has_conflict else ""}',
        'html': get_base_template(content, "New Quote Alert - Admin"),
        'recipient': studio_info['email']
    }


# ============================================================================
# CLIENT RESCHEDULE EMAIL (PUT Request)
# ============================================================================

def get_client_reschedule_email(quote_data: Dict, admin_note: str = None) -> Dict[str, str]:
    """
    Email sent to client when quote is rescheduled due to conflict
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    content = f"""
        <div class="header">
            <h1>🔄 Schedule Update</h1>
            <p>Your quote has been rescheduled</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {quote_data.get('client_name', 'Valued Client')},</div>
            
            <div class="message">
                We hope you're doing well! 
                <br><br>
                We encountered a schedule conflict regarding your requested event time. 
                To ensure we give your project our full attention and deliver the best results, 
                we've made the following update to your quote.
            </div>
            
            <div class="warning-box">
                <h3>🔄 Updated Schedule</h3>
                <div class="info-row">
                    <span class="info-label">New Event Date:</span>
                    <span class="info-value" style="font-weight: 600; color: {COLORS['warning']};">{quote_data.get('event_date', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">New Event Time:</span>
                    <span class="info-value" style="font-weight: 600; color: {COLORS['warning']};">{quote_data.get('event_time', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{quote_data.get('event_location', 'As originally specified')}</span>
                </div>
            </div>
            
            {f'''<div class="info-box">
                <h3>📝 Reason for Reschedule</h3>
                <p style="margin: 0; color: #6B7280; font-size: 14px;">
                    {admin_note}
                </p>
            </div>''' if admin_note else ''}
            
            <div class="info-box">
                <h3>📌 Your Original Request</h3>
                <div style="margin-top: 10px;">
                    <span class="info-label" style="display: block; margin-bottom: 10px;">Selected Services:</span>
                    {format_services_list(quote_data.get('selected_services', []), show_estimate_notice=False)}
                </div>
                {f'''<div class="info-row" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid {COLORS['border']};">
                    <span class="info-label">Estimated Cost:</span>
                    <span class="info-value" style="font-weight: 600; color: {COLORS['primary']};">
                        {quote_data['price_estimate']['formatted']}
                    </span>
                </div>
                <p style="margin: 8px 0 0 0; font-size: 12px; color: #6B7280;">
                    (This remains the same - pricing hasn't changed)
                </p>''' if quote_data.get('price_estimate') and quote_data['price_estimate'].get('formatted') else ''}
                <div class="info-row">
                    <span class="info-label">Your Budget:</span>
                    <span class="info-value">{quote_data.get('budget_range', 'Not specified')}</span>
                </div>
            </div>
            
            <div class="contact-section">
                <h3>📞 Schedule Doesn't Work for You?</h3>
                <p style="margin: 0 0 15px 0; color: #6B7280; font-size: 14px;">
                    We understand that changes can be inconvenient. If this new schedule doesn't work for you, 
                    please don't hesitate to reach out and we'll find a solution together.
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
                        <span class="contact-icon">🏢</span>
                        <span class="contact-label">Visit the Studio:</span>
                        <span class="contact-value">{studio_info['address']}</span>
                    </div>''' if studio_info['address'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">✉️</span>
                        <span class="contact-label">Email:</span>
                        <span class="contact-value"><a href="mailto:{studio_info['email']}">{studio_info['email']}</a></span>
                    </div>''' if studio_info['email'] else ''}
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: {COLORS['light']}; border-radius: 8px;">
                <p style="margin: 0; color: {COLORS['dark']}; font-size: 15px;">
                    We appreciate your understanding and flexibility! 🙏
                </p>
                <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 14px;">
                    We look forward to creating something amazing together.
                    <br><br>
                    Best regards,<br>
                    <strong>The {studio_info['name']} Team</strong>
                </p>
            </div>
        </div>
"""
    
    return {
        'subject': f'Schedule Update - {studio_info["name"]}',
        'html': get_base_template(content, f"Schedule Update - {studio_info['name']}"),
        'recipient': quote_data.get('client_email')
    }


# ============================================================================
# CLIENT CANCELLATION EMAIL (DELETE Request)
# ============================================================================

def get_client_cancellation_email(quote_data: Dict, cancellation_reason: str = None) -> Dict[str, str]:
    """
    Email sent to client when quote is cancelled
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    content = f"""
        <div class="header" style="background: linear-gradient(135deg, {COLORS['danger']} 0%, #DC2626 100%);">
            <h1>Quote Cancellation Notice</h1>
            <p>Regarding your quote request</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {quote_data.get('client_name', 'Valued Client')},</div>
            
            <div class="message">
                We regret to inform you that your quote request has been cancelled.
                <br><br>
                We understand this may be disappointing, and we sincerely apologize for any inconvenience this may cause.
            </div>
            
            <div class="danger-box">
                <h3>❌ Quote Cancelled</h3>
                <div class="info-row">
                    <span class="info-label">Original Event Date:</span>
                    <span class="info-value">{quote_data.get('event_date', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Original Event Time:</span>
                    <span class="info-value">{quote_data.get('event_time', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Status:</span>
                    <span class="info-value" style="color: {COLORS['danger']}; font-weight: 600;">CANCELLED</span>
                </div>
            </div>
            
            {f'''<div class="info-box">
                <h3>📝 Reason for Cancellation</h3>
                <p style="margin: 0; color: #6B7280; font-size: 14px;">
                    {cancellation_reason}
                </p>
            </div>''' if cancellation_reason else '''<div class="info-box">
                <h3>📝 About This Cancellation</h3>
                <p style="margin: 0; color: #6B7280; font-size: 14px;">
                    This decision was made to ensure fairness and scheduling accuracy for all our clients. 
                    We strive to maintain the highest quality of service for every project we undertake.
                </p>
            </div>'''}
            
            <div class="info-box">
                <h3>📌 Your Original Request Summary</h3>
                <div style="margin-top: 10px;">
                    <span class="info-label" style="display: block; margin-bottom: 10px;">Selected Services:</span>
                    {format_services_list(quote_data.get('selected_services', []), show_estimate_notice=False)}
                </div>
                {f'''<div class="info-row" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid {COLORS['border']};">
                    <span class="info-label">Estimated Cost:</span>
                    <span class="info-value" style="color: #6B7280;">
                        {quote_data['price_estimate']['formatted']}
                    </span>
                </div>''' if quote_data.get('price_estimate') and quote_data['price_estimate'].get('formatted') else ''}
                <div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{quote_data.get('event_location', 'Not specified')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Budget Range:</span>
                    <span class="info-value">{quote_data.get('budget_range', 'Not specified')}</span>
                </div>
            </div>
            
            <div class="contact-section">
                <h3>💡 Still Interested? Let's Find a Solution!</h3>
                <p style="margin: 0 0 15px 0; color: #6B7280; font-size: 14px;">
                    We'd love to help you explore alternative options or discuss a different approach to your project. 
                    Your vision matters to us, and we're here to make it happen.
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
                        <span class="contact-icon">🏢</span>
                        <span class="contact-label">Visit the Studio:</span>
                        <span class="contact-value">{studio_info['address']}</span>
                    </div>''' if studio_info['address'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">✉️</span>
                        <span class="contact-label">Email:</span>
                        <span class="contact-value"><a href="mailto:{studio_info['email']}">{studio_info['email']}</a></span>
                    </div>''' if studio_info['email'] else ''}
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                {f'''<a href="{studio_info['website']}" class="cta-button" style="background: linear-gradient(135deg, {COLORS['primary']} 0%, #FF8A5B 100%);">
                    📝 Submit a New Quote Request
                </a>''' if studio_info['website'] else ''}
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: {COLORS['light']}; border-radius: 8px;">
                <p style="margin: 0; color: {COLORS['dark']}; font-size: 15px;">
                    Thank you for considering {studio_info['name']} 🎬
                </p>
                <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 14px;">
                    We hope to work with you in the future.
                    <br><br>
                    Warm regards,<br>
                    <strong>The {studio_info['name']} Team</strong>
                </p>
            </div>
        </div>
"""
    
    return {
        'subject': f'Quote Cancellation Notice - {studio_info["name"]}',
        'html': get_base_template(content, f"Quote Cancelled - {studio_info['name']}"),
        'recipient': quote_data.get('client_email')
    }


# ============================================================================
# QUOTE SENT EMAIL (When admin sends final quote to client)
# ============================================================================

def get_quote_sent_email(quote_data: Dict) -> Dict[str, str]:
    """
    Email sent to client when admin sends the final quote
    UPDATED: More conversational WhatsApp CTA
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    valid_until_text = ""
    if quote_data.get('valid_until'):
        valid_until_text = f'''
            <div class="warning-box" style="background-color: #FEF3C7;">
                <p style="margin: 0; color: #92400E; font-weight: 600;">
                    ⏰ This quote is valid until {quote_data.get('valid_until')}
                </p>
            </div>
        '''
    
    content = f"""
        <div class="header">
            <h1>📄 Your Custom Quote is Ready!</h1>
            <p>We've prepared a detailed proposal for your project</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {quote_data.get('client_name', 'Valued Client')},</div>
            
            <div class="message">
                Great news! We've carefully reviewed your requirements and prepared a custom quote 
                tailored specifically to your needs. 🎉
                <br><br>
                Our team has put together a comprehensive proposal that we believe will exceed your expectations.
            </div>
            
            <div class="success-box">
                <h3>✅ Your Custom Quote</h3>
                {f'''<div class="info-row">
                    <span class="info-label">Quoted Amount:</span>
                    <span class="info-value" style="font-weight: 700; color: {COLORS['success']}; font-size: 24px;">
                        KES {quote_data.get('quoted_amount', 0):,}
                    </span>
                </div>
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(16, 185, 129, 0.2);">
                    <p style="margin: 0; font-size: 13px; color: #059669; font-weight: 500;">
                        💡 This quote is based on your specific requirements and includes:
                    </p>
                    <ul style="margin: 8px 0 0 20px; padding: 0; font-size: 13px; color: #047857;">
                        <li>All selected services and features</li>
                        <li>Professional equipment and expertise</li>
                        <li>Post-production and delivery</li>
                    </ul>
                </div>''' if quote_data.get('quoted_amount') else '''
                <p style="margin: 0; color: {COLORS['warning']}; font-weight: 600;">
                    Custom pricing details are included in the quote below.
                </p>'''}
                <div class="info-row" style="margin-top: 12px;">
                    <span class="info-label">Event Date:</span>
                    <span class="info-value">{quote_data.get('event_date', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Event Time:</span>
                    <span class="info-value">{quote_data.get('event_time', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{quote_data.get('event_location', 'As specified')}</span>
                </div>
            </div>
            
            {valid_until_text}
            
            {f'''<div class="info-box">
                <h3>📋 Quote Details</h3>
                <p style="margin: 0; color: #6B7280; font-size: 14px; white-space: pre-line;">
                    {quote_data.get('quote_details')}
                </p>
            </div>''' if quote_data.get('quote_details') else ''}
            
            <div class="info-box">
                <h3>🎬 Services Included in Your Quote</h3>
                {format_services_list(quote_data.get('selected_services', []), show_estimate_notice=False)}
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid {COLORS['border']};">
                    <p style="margin: 0; font-size: 13px; color: #6B7280;">
                        <strong>Note:</strong> The quoted amount above reflects your specific project requirements. 
                        Any changes to services or scope may affect the final price.
                    </p>
                </div>
            </div>
            
            <div class="contact-section">
                <h3>💬 Let's Discuss Your Quote</h3>
                <p style="margin: 0 0 15px 0; color: #6B7280; font-size: 14px;">
                    Have questions about the pricing, services, or timeline? We're here to help! 
                    Let's have a conversation to address any concerns and fine-tune the details.
                </p>
                <div class="contact-methods">
                    {f'''<div class="contact-item">
                        <span class="contact-icon">💬</span>
                        <span class="contact-label">WhatsApp:</span>
                        <span class="contact-value">
                            <a href="{whatsapp_link}" style="color: {COLORS['primary']}; font-weight: 600;">
                                Chat with us about this quote
                            </a>
                        </span>
                    </div>''' if studio_info['whatsapp'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">📞</span>
                        <span class="contact-label">Call Us:</span>
                        <span class="contact-value">
                            <a href="tel:{studio_info['phone']}" style="color: {COLORS['primary']}; font-weight: 600;">
                                {studio_info['phone']}
                            </a>
                        </span>
                    </div>''' if studio_info['phone'] else ''}
                    {f'''<div class="contact-item">
                        <span class="contact-icon">✉️</span>
                        <span class="contact-label">Email:</span>
                        <span class="contact-value">
                            <a href="mailto:{studio_info['email']}" style="color: {COLORS['primary']}; font-weight: 600;">
                                {studio_info['email']}
                            </a>
                        </span>
                    </div>''' if studio_info['email'] else ''}
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 25px; background: linear-gradient(135deg, {COLORS['light']} 0%, #E5E7EB 100%); border-radius: 8px;">
                <p style="margin: 0; color: {COLORS['dark']}; font-size: 16px; font-weight: 600;">
                    Ready to bring your vision to life? 🎬✨
                </p>
                <p style="margin: 15px 0; color: #6B7280; font-size: 14px;">
                    We're excited to work on your project and create something amazing together.
                    Reach out to us and let's get started!
                </p>
                <p style="margin: 15px 0 0 0; color: #6B7280; font-size: 13px;">
                    Best regards,<br>
                    <strong>The {studio_info['name']} Team</strong>
                </p>
            </div>
        </div>
"""
    
    return {
        'subject': f'Your Custom Quote is Ready! - {studio_info["name"]}',
        'html': get_base_template(content, f"Quote Ready - {studio_info['name']}"),
        'recipient': quote_data.get('client_email')
    }


# ============================================================================
# QUOTE ACCEPTED EMAIL (Status changed to ACCEPTED)
# ============================================================================

def get_quote_accepted_email(quote_data: Dict) -> Dict[str, str]:
    """
    Email sent to client when their quote is accepted (status changed to ACCEPTED)
    This confirms the booking and provides next steps
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    content = f"""
        <div class="header">
            <h1>🎉 Booking Confirmed!</h1>
            <p>Your quote has been accepted</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {quote_data.get('client_name', 'Valued Client')},</div>
            
            <div class="message">
                Fantastic news! Your quote has been officially accepted and your booking is now confirmed! 🎊
                <br><br>
                We're thrilled to work with you and can't wait to bring your vision to life.
            </div>
            
            <div class="success-box">
                <h3>✅ Booking Confirmed - Final Amount</h3>
                {f'''<div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.3); border-radius: 8px; margin-bottom: 15px;">
                    <p style="margin: 0 0 8px 0; font-size: 14px; color: #047857; font-weight: 600;">Total Project Cost</p>
                    <p style="margin: 0; font-size: 32px; font-weight: 700; color: white; letter-spacing: -1px;">
                        KES {quote_data.get('quoted_amount', 0):,}
                    </p>
                    <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">Final confirmed amount</p>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 6px;">
                    <p style="margin: 0; font-size: 13px; color: white; font-weight: 500;">
                        ✓ Price locked in - No surprises<br>
                        ✓ All services and features included<br>
                        ✓ Payment schedule will be provided
                    </p>
                </div>''' if quote_data.get('quoted_amount') else ''}
                <div class="info-row" style="margin-top: 15px;">
                    <span class="info-label">Event Date:</span>
                    <span class="info-value">{quote_data.get('event_date', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Event Time:</span>
                    <span class="info-value">{quote_data.get('event_time', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{quote_data.get('event_location', 'As specified')}</span>
                </div>
            </div>
            
            <div class="info-box">
                <h3>📋 Next Steps</h3>
                <ul style="margin: 0; padding-left: 20px; color: #6B7280;">
                    <li style="margin: 8px 0;">Our team will contact you within 24 hours to finalize details</li>
                    <li style="margin: 8px 0;">Please review and sign the service agreement we'll send</li>
                    <li style="margin: 8px 0;">Payment schedule and instructions will be provided</li>
                    <li style="margin: 8px 0;">Pre-event consultation will be scheduled</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3>🎬 Confirmed Services Package</h3>
                {format_services_list(quote_data.get('selected_services', []), show_estimate_notice=False)}
                <div style="margin-top: 15px; padding: 12px; background: {COLORS['light']}; border-radius: 6px;">
                    <p style="margin: 0; font-size: 13px; color: {COLORS['dark']}; font-weight: 600;">
                        💼 What's Included:
                    </p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #6B7280;">
                        All services listed above are confirmed and included in your booking. 
                        We'll work closely with you to ensure every detail meets your expectations.
                    </p>
                </div>
            </div>
            
            {f'''<div class="info-box">
                <h3>💡 Project Notes</h3>
                <p style="margin: 0; color: #6B7280; font-size: 14px; white-space: pre-line;">
                    {quote_data.get('quote_details')}
                </p>
            </div>''' if quote_data.get('quote_details') else ''}
            
            <div class="contact-section">
                <h3>📞 Questions or Need to Discuss Details?</h3>
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
            
            <div style="text-align: center; margin-top: 30px; padding: 25px; background: linear-gradient(135deg, {COLORS['success']} 0%, #059669 100%); border-radius: 8px; color: white;">
                <p style="margin: 0; font-size: 18px; font-weight: 600;">
                    🎬 Let's Create Something Amazing! ✨
                </p>
                <p style="margin: 15px 0 0 0; font-size: 14px; opacity: 0.9;">
                    We're excited to work with you!
                    <br><br>
                    Best regards,<br>
                    <strong>The {studio_info['name']} Team</strong>
                </p>
            </div>
        </div>
"""
    
    return {
        'subject': f'🎉 Booking Confirmed - {studio_info["name"]}',
        'html': get_base_template(content, f"Booking Confirmed - {studio_info['name']}"),
        'recipient': quote_data.get('client_email')
    }


# ============================================================================
# QUOTE REJECTED EMAIL (Status changed to REJECTED)
# ============================================================================

def get_quote_rejected_email(quote_data: Dict, rejection_reason: str = None) -> Dict[str, str]:
    """
    Email sent to client when their quote is rejected (status changed to REJECTED)
    """
    studio_info = get_studio_info()
    whatsapp_link = get_whatsapp_link(studio_info['whatsapp'])
    
    default_reason = """Unfortunately, we are unable to accommodate your request at this time. 
    This could be due to scheduling conflicts, resource availability, or project scope considerations."""
    
    content = f"""
        <div class="header" style="background: linear-gradient(135deg, {COLORS['danger']} 0%, #DC2626 100%);">
            <h1>Quote Decision Update</h1>
            <p>Regarding your quote request</p>
        </div>
        
        <div class="content">
            <div class="greeting">Hello {quote_data.get('client_name', 'Valued Client')},</div>
            
            <div class="message">
                Thank you for considering {studio_info['name']} for your project.
                <br><br>
                After careful review, we regret to inform you that we are unable to proceed with your quote at this time.
            </div>
            
            <div class="danger-box">
                <h3>Quote Status Update</h3>
                <div class="info-row">
                    <span class="info-label">Quote ID:</span>
                    <span class="info-value">#{quote_data.get('id', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Original Event Date:</span>
                    <span class="info-value">{quote_data.get('event_date', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Status:</span>
                    <span class="info-value" style="color: {COLORS['danger']}; font-weight: 600;">REJECTED</span>
                </div>
            </div>
            
            <div class="info-box">
                <h3>📝 Reason</h3>
                <p style="margin: 0; color: #6B7280; font-size: 14px; white-space: pre-line;">
                    {rejection_reason if rejection_reason else default_reason}
                </p>
            </div>
            
            <div class="info-box">
                <h3>📌 Your Original Request Summary</h3>
                <div style="margin-top: 10px;">
                    <span class="info-label" style="display: block; margin-bottom: 10px;">Selected Services:</span>
                    {format_services_list(quote_data.get('selected_services', []), show_estimate_notice=False)}
                </div>
                {f'''<div class="info-row" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid {COLORS['border']};">
                    <span class="info-label">Estimated Cost:</span>
                    <span class="info-value" style="color: #6B7280;">
                        {quote_data['price_estimate']['formatted']}
                    </span>
                </div>''' if quote_data.get('price_estimate') and quote_data['price_estimate'].get('formatted') else ''}
                <div class="info-row">
                    <span class="info-label">Location:</span>
                    <span class="info-value">{quote_data.get('event_location', 'Not specified')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Budget Range:</span>
                    <span class="info-value">{quote_data.get('budget_range', 'Not specified')}</span>
                </div>
            </div>
            
            <div class="contact-section">
                <h3>💡 Still Interested? Let's Explore Alternatives</h3>
                <p style="margin: 0 0 15px 0; color: #6B7280; font-size: 14px;">
                    While we couldn't accommodate this particular request, we'd love to help you find an alternative solution. 
                    Perhaps a different date, service package, or approach might work better.
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
                <p style="margin: 0; color: {COLORS['dark']}; font-size: 15px;">
                    Thank you for considering {studio_info['name']}
                </p>
                <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 14px;">
                    We hope to have the opportunity to work with you in the future.
                    <br><br>
                    Warm regards,<br>
                    <strong>The {studio_info['name']} Team</strong>
                </p>
            </div>
        </div>
"""
    
    return {
        'subject': f'Quote Decision - {studio_info["name"]}',
        'html': get_base_template(content, f"Quote Decision - {studio_info['name']}"),
        'recipient': quote_data.get('client_email')
    }