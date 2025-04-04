from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import User
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.utils.timezone import now
import re

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def register_user(request):
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Validate required fields
            required_fields = ['firstname', 'lastname', 'email', 'phone_number', 'password', 'role', 'id_type', 'id_value']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'{field} is required'}, status=400)
            
            # Check if email already exists
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({'error': 'Email already registered'}, status=400)

            # Hash the password before saving
            hashed_password = make_password(data['password'])

            user = User.objects.create(
                firstname=data['firstname'],
                lastname=data['lastname'],
                email=data['email'],
                phone_number=data['phone_number'],
                password_hash=hashed_password,
                role=data['role'],
                id_type=data['id_type'],
                id_value=data['id_value'],
                is_verified=False
            )
            return JsonResponse({
                'message': 'Registration successful! Please wait for account verification.',
                'user_id': user.id,
                'is_verified': user.is_verified
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Login User

@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)

        try:
            user = User.objects.get(email=email)
            
            # Check verification status first
            if not user.is_verified:
                return JsonResponse({
                    'error': 'Account pending verification. Please wait for verification email.',
                    'is_verified': False
                }, status=403)

            # For users registered before password hashing was implemented
            if not user.password_hash.startswith('pbkdf2_sha256$'):
                user.password_hash = make_password(user.password_hash)
                user.save()

            if check_password(password, user.password_hash):
                # Update last_login
                user.last_login = now()
                user.save()

                return JsonResponse({
                    'message': 'Login successful',
                    'user_id': user.id,
                    'role': user.role,
                    'is_verified': user.is_verified
                })
            else:
                return JsonResponse({'error': 'Invalid email or password'}, status=401)

        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


#function for admin to get all unverified users
@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def get_unverified_users(request):
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method == 'GET':
        users = User.objects.filter(is_verified=False).values('id', 'firstname', 'lastname', 'email', 'role', 'id_type', 'id_value')
        response = JsonResponse(list(users), safe=False)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    return JsonResponse({'error': 'Method not allowed'}, status=405)

#function for admin to verify users using id regex validation
@csrf_exempt
def verify_user(request):
    if request.method != 'PATCH':
        return JsonResponse({'error': 'PATCH only'}, status=405)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')

        user = User.objects.get(id=user_id)

        # Regex patterns
        patterns = {
            'Ghana Card': r'^GHA-\d{9}-\d$',
            'Passport': r'^[A-Z]{1}\d{7}$'
        }

        pattern = patterns.get(user.id_type)
        if not pattern:
            return JsonResponse({'error': 'Unsupported ID type'}, status=400)

        if not re.match(pattern, user.id_value):
            return JsonResponse({'error': f'{user.id_type} format is invalid'}, status=400)

        user.is_verified = True
        user.save()
        return JsonResponse({'message': f'{user.firstname} {user.lastname} verified successfully.'})

    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)