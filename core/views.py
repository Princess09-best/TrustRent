from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import User

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = User.objects.create(
            firstname=data['firstname'],
            lastname=data['lastname'],
            email=data['email'],
            phone_number=data['phone_number'],
            password_hash=data['password'],  # just for now
            role=data['role'],
            id_type=data['id_type'],
            id_value=data['id_value'],
            is_verified=False
        )
        return JsonResponse({'message': 'User registered', 'user_id': user.id})
