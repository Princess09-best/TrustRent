from django.core.mail import send_mail
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

def send_otp_via_email(email, otp, user_name):
    """
    Send OTP to user's email address
    """
    try:
        subject = "TrustRent - Your One-Time Password for Authentication"
        message = f"""
Hello {user_name},

Your one-time password (OTP) for TrustRent authentication is: {otp}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email and consider changing your password.

Regards,
TrustRent Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"OTP email sent successfully to {email}")
        return True, "OTP sent successfully to your email"
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False, "Failed to send OTP. Please try again later."

def send_otp_via_sms(phone_number, otp, user_name):
    """
    Send OTP to user's phone number via SMS
    Using the configured SMS provider
    """
    try:
        message = f"TrustRent: Your verification code is {otp}. Valid for 10 minutes."
        
        # Determine which SMS provider to use
        provider = getattr(settings, 'SMS_PROVIDER', 'console')
        
        if provider == 'console':
            # Just log the message for development/testing
            logger.info(f"SMS OTP for {phone_number}: {otp}")
            return True, "OTP sent successfully to your phone"
            
        elif provider == 'twilio':
            # Twilio API integration
            try:
                from twilio.rest import Client
                
                account_sid = settings.SMS_API_KEY
                auth_token = settings.SMS_API_SECRET
                client = Client(account_sid, auth_token)
                
                client.messages.create(
                    body=message,
                    from_=settings.SMS_FROM_NUMBER,
                    to=phone_number
                )
                
                logger.info(f"SMS sent via Twilio to {phone_number}")
                return True, "OTP sent successfully to your phone"
            except ImportError:
                logger.error("Twilio package not installed")
                return False, "SMS service unavailable. Please try email instead."
            except Exception as e:
                logger.error(f"Twilio API error: {str(e)}")
                return False, "Failed to send SMS. Please try again later."
                
        elif provider == 'vonage':
            # Vonage (formerly Nexmo) API integration
            try:
                import vonage
                
                client = vonage.Client(
                    key=settings.SMS_API_KEY,
                    secret=settings.SMS_API_SECRET
                )
                sms = vonage.Sms(client)
                
                response = sms.send_message({
                    'from': 'TrustRent',
                    'to': phone_number,
                    'text': message
                })
                
                if response['messages'][0]['status'] == '0':
                    logger.info(f"SMS sent via Vonage to {phone_number}")
                    return True, "OTP sent successfully to your phone"
                else:
                    error = response['messages'][0]['error-text']
                    logger.error(f"Vonage API error: {error}")
                    return False, "Failed to send SMS. Please try again later."
            except ImportError:
                logger.error("Vonage package not installed")
                return False, "SMS service unavailable. Please try email instead."
            except Exception as e:
                logger.error(f"Vonage API error: {str(e)}")
                return False, "Failed to send SMS. Please try again later."
                
        elif provider == 'africastalking':
            # Africa's Talking API integration (popular in Ghana and other African countries)
            try:
                import africastalking
                
                username = settings.AFRICASTALKING_USERNAME
                api_key = settings.SMS_API_KEY
                
                africastalking.initialize(username, api_key)
                sms = africastalking.SMS
                
                response = sms.send(message, [phone_number])
                
                if response:
                    logger.info(f"SMS sent via Africa's Talking to {phone_number}")
                    return True, "OTP sent successfully to your phone"
                else:
                    logger.error("Africa's Talking API error")
                    return False, "Failed to send SMS. Please try again later."
            except ImportError:
                logger.error("Africa's Talking package not installed")
                return False, "SMS service unavailable. Please try email instead."
            except Exception as e:
                logger.error(f"Africa's Talking API error: {str(e)}")
                return False, "Failed to send SMS. Please try again later."
                
        else:
            # Default to console logging if no valid provider is configured
            logger.info(f"Would send SMS to {phone_number}: {message}")
            logger.warning(f"No valid SMS provider configured. Using console output.")
            return True, "OTP sent successfully to your phone"
            
    except Exception as e:
        logger.error(f"Failed to send OTP SMS to {phone_number}: {str(e)}")
        return False, "Failed to send OTP. Please try again later." 