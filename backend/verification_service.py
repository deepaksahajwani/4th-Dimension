"""
Team Member Email and Phone Verification Service
"""
import os
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client

# Initialize clients
sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)

async def send_verification_email(
    to_email: str,
    user_name: str,
    verification_link: str,
    otp: str
) -> Tuple[bool, Optional[str]]:
    """
    Send verification email with link and OTP
    
    Returns: (success: bool, error_message: Optional[str])
    """
    try:
        sender_email = os.getenv('SENDER_EMAIL')
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5; margin-bottom: 10px;">Welcome to 4th Dimension!</h1>
                        <p style="color: #666; font-size: 16px;">Architecture & Design</p>
                    </div>
                    
                    <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <h2 style="color: #1F2937; margin-top: 0;">Hello {user_name},</h2>
                        <p style="font-size: 16px;">
                            You have been added as a team member. Please verify your email address to complete your registration.
                        </p>
                    </div>
                    
                    <div style="margin-bottom: 30px;">
                        <h3 style="color: #4F46E5;">Verification Methods:</h3>
                        
                        <div style="background: #EEF2FF; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                            <p style="margin: 0 0 10px 0;"><strong>Option 1: Click the verification link</strong></p>
                            <a href="{verification_link}" 
                               style="display: inline-block; background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                Verify Email Address
                            </a>
                        </div>
                        
                        <div style="background: #FEF3C7; padding: 15px; border-radius: 8px;">
                            <p style="margin: 0 0 10px 0;"><strong>Option 2: Enter OTP code</strong></p>
                            <div style="font-size: 32px; font-weight: bold; color: #D97706; letter-spacing: 5px; text-align: center; padding: 10px; background: white; border-radius: 5px;">
                                {otp}
                            </div>
                            <p style="margin: 10px 0 0 0; font-size: 12px; color: #92400E;">
                                This OTP will expire in 15 minutes
                            </p>
                        </div>
                    </div>
                    
                    <div style="border-top: 1px solid #ddd; padding-top: 20px; color: #666; font-size: 14px;">
                        <p><strong>Next Steps:</strong></p>
                        <ol style="margin: 10px 0;">
                            <li>Verify your email address (using link or OTP)</li>
                            <li>Verify your phone number (OTP will be sent via SMS)</li>
                            <li>Complete your profile and start collaborating</li>
                        </ol>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
                        <p>If you didn't request this, please ignore this email.</p>
                        <p style="margin-top: 15px;">
                            <strong>4th Dimension - Architecture & Design</strong><br>
                            Building Dreams, Creating Realities
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        message = Mail(
            from_email=sender_email,
            to_emails=to_email,
            subject='Verify Your Email - 4th Dimension Team',
            html_content=html_content
        )
        
        response = sendgrid_client.send(message)
        
        if response.status_code in [200, 201, 202]:
            return True, None
        else:
            return False, f"SendGrid returned status {response.status_code}"
            
    except Exception as e:
        return False, str(e)

async def send_verification_sms(
    phone_number: str,
    otp: str
) -> Tuple[bool, Optional[str]]:
    """
    Send verification SMS with OTP
    
    Returns: (success: bool, error_message: Optional[str])
    """
    try:
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        message_body = f"""4th Dimension Team Verification

Your OTP code is: {otp}

This code will expire in 15 minutes.

If you didn't request this, please ignore."""
        
        message = twilio_client.messages.create(
            body=message_body,
            from_=from_number,
            to=phone_number
        )
        
        if message.sid:
            return True, None
        else:
            return False, "Failed to send SMS"
            
    except Exception as e:
        return False, str(e)

def is_otp_expired(created_at: datetime, expiry_minutes: int = 15) -> bool:
    """Check if OTP has expired"""
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    expiry_time = created_at + timedelta(minutes=expiry_minutes)
    return datetime.now(timezone.utc) > expiry_time
