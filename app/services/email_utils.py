"""
Email Utilities Module
Simple email sending functions for Lenny Media
"""
import logging
from flask_mail import Mail, Message
from flask import current_app

# Initialize Mail globally - must be attached via mail.init_app(app)
mail = Mail()

# Configure logging
logger = logging.getLogger(__name__)


def send_email(recipient, subject, html_body):
    """
    Send a single email with HTML content
    
    Args:
        recipient (str): Email address of recipient
        subject (str): Email subject line
        html_body (str): HTML content of email
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            html=html_body
        )
        
        mail.send(msg)
        logger.info(f"Email sent successfully to {recipient}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {str(e)}", exc_info=True)
        return False


def send_multiple_emails(recipients, subject, html_body):
    """
    Send the same email to multiple recipients
    
    Args:
        recipients (list): List of email addresses
        subject (str): Email subject line
        html_body (str): HTML content of email
        
    Returns:
        dict: Results with 'success' count and 'failed' list
    """
    results = {'success': 0, 'failed': []}
    
    for recipient in recipients:
        if send_email(recipient, subject, html_body):
            results['success'] += 1
        else:
            results['failed'].append(recipient)
    
    return results


def test_email_configuration():
    """
    Test email configuration by sending a test email to admin
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">
                <h2 style="color: #16a34a; margin-top: 0;">✅ Email Configuration Successful!</h2>
                <p>Your Flask-Mail configuration is working correctly.</p>
                <div style="background: #f5f5f4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Mail Server:</strong> """ + current_app.config['MAIL_SERVER'] + """</p>
                    <p style="margin: 5px 0;"><strong>Mail Port:</strong> """ + str(current_app.config['MAIL_PORT']) + """</p>
                    <p style="margin: 5px 0;"><strong>Sender:</strong> """ + current_app.config['MAIL_DEFAULT_SENDER'] + """</p>
                </div>
                <p style="color: #16a34a; font-weight: bold;">✓ You can now send booking confirmation and notification emails.</p>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject="Email Configuration Test - Lenny Media",
            recipients=[current_app.config['ADMIN_EMAIL']],
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            html=html_body
        )
        
        mail.send(msg)
        logger.info("Test email sent successfully to admin")
        return True
        
    except Exception as e:
        logger.error(f"Email configuration test failed: {str(e)}", exc_info=True)
        return False