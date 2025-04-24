"""
Test script for MFA functionality.
Run this script to test the MFA features without using the API endpoints.

Usage:
    python test_mfa.py

"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrustRent.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.utils import send_otp_via_email, send_otp_via_sms

User = get_user_model()

def test_email_otp(email):
    """Test sending OTP via email"""
    try:
        user = User.objects.get(email=email)
        otp = '123456'  # For testing only
        success, message = send_otp_via_email(user.email, otp, user.firstname)
        print(f"Email OTP Test: {success} - {message}")
    except User.DoesNotExist:
        print(f"No user found with email: {email}")
    except Exception as e:
        print(f"Error testing email OTP: {str(e)}")

def test_sms_otp(email):
    """Test sending OTP via SMS"""
    try:
        user = User.objects.get(email=email)
        otp = '123456'  # For testing only
        success, message = send_otp_via_sms(user.phone_number, otp, user.firstname)
        print(f"SMS OTP Test: {success} - {message}")
    except User.DoesNotExist:
        print(f"No user found with email: {email}")
    except Exception as e:
        print(f"Error testing SMS OTP: {str(e)}")

def test_user_mfa_functions(email):
    """Test User model MFA functions"""
    try:
        user = User.objects.get(email=email)
        
        # Test generate_otp
        print("\nTesting generate_otp:")
        otp = user.generate_otp()
        print(f"Generated OTP: {otp}")
        print(f"OTP stored (hashed): {user.otp_secret[:10]}...")
        print(f"OTP valid until: {user.otp_valid_until}")
        
        # Test verify_otp
        print("\nTesting verify_otp:")
        is_valid = user.verify_otp(otp)
        print(f"Valid OTP verification: {is_valid}")
        is_invalid = user.verify_otp("000000")
        print(f"Invalid OTP verification: {is_invalid}")
        
        # Test clear_otp
        print("\nTesting clear_otp:")
        user.clear_otp()
        print(f"OTP cleared: {user.otp_secret is None}")
        
    except User.DoesNotExist:
        print(f"No user found with email: {email}")
    except Exception as e:
        print(f"Error testing user MFA functions: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = input("Enter email of a user to test MFA: ")

    print("\n=== Testing Email OTP ===")
    test_email_otp(email)
    
    print("\n=== Testing SMS OTP ===")
    test_sms_otp(email)
    
    print("\n=== Testing User MFA Functions ===")
    test_user_mfa_functions(email) 