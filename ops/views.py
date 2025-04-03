from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from .models import User
import json

@csrf_exempt
def register_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)

        required = ['firstname', 'lastname', 'email', 'phone_number', 'password', 'role', 'id_type', 'id_value']
        missing = [field for field in required if field not in data]

        if missing:
            return JsonResponse({'error': f'Missing fields: {", ".join(missing)}'}, status=400)

        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'error': 'User with this email already exists'}, status=400)

        user = User.objects.create(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            phone_number=data['phone_number'],
            password_hash=make_password(data['password']),
            role=data['role'],
            id_type=data['id_type'],
            id_value=data['id_value'],
            is_verified=False
        )

        return JsonResponse({'message': 'User registered successfully', 'user_id': user.id})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
