import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from fastapi import HTTPException
import logging
from datetime import datetime
import pytz

# Current time in UTC
utc_now = datetime.now(pytz.utc)

# Convert to IST
ist = pytz.timezone('Asia/Kolkata')
ist_now = utc_now.astimezone(ist)

# Format the time
formatted_time = ist_now.strftime('%B %d, %Y at %I:%M %p IST')

load_dotenv()

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Your App")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Validate email configuration
if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL]):
    raise ValueError("Email configuration is incomplete. Please check your .env file.")

def send_email(to_email: str, subject: str, html_content: str, text_content: str = None):
    """
    Send email using SMTP
    """
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = to_email

        # Create text and HTML parts
        if text_content:
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Connect to server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable security
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        text = msg.as_string()
        server.sendmail(SMTP_FROM_EMAIL, to_email, text)
        server.quit()
        
        print(f"[EMAIL] Successfully sent email to {to_email}")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Failed to send email to {to_email}: {str(e)}")
        logging.error(f"Email sending failed: {str(e)}")
        return False

def send_password_reset_email(to_email: str, reset_token: str, first_name: str):
    """
    Send password reset email with reset link
    """
    try:
        # Create reset URL
        reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        
        # Email subject
        subject = "Password Reset Request"
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2c3e50;
                    margin: 0;
                }}
                .content {{
                    background-color: white;
                    padding: 25px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .reset-button {{
                    display: inline-block;
                    background-color: #3498db;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .reset-button:hover {{
                    background-color: #2980b9;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #7f8c8d;
                    font-size: 14px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    color: #856404;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border-left: 4px solid #ffc107;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{SMTP_FROM_NAME}</h1>
                </div>
                
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>Hello {first_name},</p>
                    
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="reset-button">Reset Password</a>
                    </div>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #3498db;">{reset_url}</p>
                    
                    <div class="warning">
                        <strong>Important:</strong> This link will expire in 30 minutes for security reasons.
                    </div>
                    
                    <p>If you didn't request this password reset, please ignore this email. Your password will remain unchanged.</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent from {SMTP_FROM_NAME}</p>
                    <p>If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (fallback)
        text_content = f"""
        Password Reset Request
        
        Hello {first_name},
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_url}
        
        This link will expire in 30 minutes for security reasons.
        
        If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
        
        ---
        {SMTP_FROM_NAME}
        """
        
        # Send the email
        success = send_email(to_email, subject, html_content, text_content)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to send password reset email. Please try again later."
            )
        
        return True
        
    except Exception as e:
        print(f"[EMAIL] Error sending password reset email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send password reset email. Please try again later."
        )

def send_password_change_confirmation(to_email: str, first_name: str):
    """
    Send confirmation email after password has been successfully changed
    """
    try:
        subject = "Password Changed Successfully"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Changed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2c3e50;
                    margin: 0;
                }}
                .content {{
                    background-color: white;
                    padding: 25px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .success {{
                    background-color: #d4edda;
                    color: #155724;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border-left: 4px solid #28a745;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #7f8c8d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{SMTP_FROM_NAME}</h1>
                </div>
                
                <div class="content">
                    <h2>Password Changed Successfully</h2>
                    <p>Hello {first_name},</p>
                    
                    <div class="success">
                        <strong>Success!</strong> Your password has been changed successfully.
                    </div>
                    
                    <p>Your account password was updated on {formatted_time}.</p>
                    
                    <p>If you did not make this change, please contact our support team immediately.</p>
                    
                    <p>For security reasons, we recommend:</p>
                    <ul>
                        <li>Use a strong, unique password</li>
                        <li>Don't share your password with anyone</li>
                        <li>Enable two-factor authentication if available</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>This email was sent from {SMTP_FROM_NAME}</p>
                    <p>If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Changed Successfully
        
        Hello {first_name},
        
        Your password has been changed successfully on {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}.
        
        If you did not make this change, please contact our support team immediately.
        
        For security reasons, we recommend:
        - Use a strong, unique password
        - Don't share your password with anyone
        - Enable two-factor authentication if available
        
        ---
        {SMTP_FROM_NAME}
        """
        
        success = send_email(to_email, subject, html_content, text_content)
        
        if success:
            print(f"[EMAIL] Password change confirmation sent to {to_email}")
        
        return success
        
    except Exception as e:
        print(f"[EMAIL] Error sending password change confirmation: {str(e)}")
        # Don't raise exception here as password change was successful
        return False

def test_email_configuration():
    """
    Test function to verify email configuration
    """
    try:
        # Test email
        test_email = "test@example.com"  # Replace with your email for testing
        
        html_content = """
        <html>
        <body>
            <h2>Email Configuration Test</h2>
            <p>If you receive this email, your SMTP configuration is working correctly!</p>
        </body>
        </html>
        """
        
        success = send_email(test_email, "Email Configuration Test", html_content)
        
        if success:
            print("✅ Email configuration test passed!")
        else:
            print("❌ Email configuration test failed!")
            
    except Exception as e:
        print(f"❌ Email configuration error: {str(e)}")

# Run this function to test your email setup
# test_email_configuration()