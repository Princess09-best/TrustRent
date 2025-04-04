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



# Create Property
from core.models import User, Property, UserProperty
from django.utils import timezone
@csrf_exempt
def create_property(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)

        required_fields = ['title', 'property_type', 'description', 'location', 'price', 'owner_id']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return JsonResponse({'error': f'Missing fields: {", ".join(missing)}'}, status=400)

        # Create Property
        new_property = Property.objects.create(
            title=data['title'],
            property_type=data['property_type'],
            description=data['description'],
            location=data['location'],
            price=data['price'],
            status='unlisted',  # Not available until verified
            created_at=timezone.now()
        )

        # Link to owner
        owner = User.objects.get(id=data['owner_id'])
        UserProperty.objects.create(
            owner=owner,
            property=new_property,
            is_verified=False,
            is_active=True
        )

        return JsonResponse({'message': 'Property created and linked to owner successfully.'})

    except User.DoesNotExist:
        return JsonResponse({'error': 'Owner not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Upload Document( deed document to property)
from core.models import User, Property, UserProperty, PropertyDocument
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

@csrf_exempt
@require_POST
def upload_document(request):
    try:
        user_id = request.POST.get('user_id')
        property_id = request.POST.get('property_id')
        file = request.FILES.get('attachment')

        if not user_id or not property_id or not file:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        user = User.objects.get(id=user_id)
        property = Property.objects.get(id=property_id)
        user_property = UserProperty.objects.get(owner=user, property=property)

        # Save the file
        saved_file_path = default_storage.save(f'title_deeds/{file.name}', ContentFile(file.read()))

        # Create PropertyDocument
        PropertyDocument.objects.create(
            user_property=user_property,
            attachment=saved_file_path
        )

        return JsonResponse({'message': 'Document uploaded successfully.'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Property.DoesNotExist:
        return JsonResponse({'error': 'Property not found'}, status=404)
    except UserProperty.DoesNotExist:
        return JsonResponse({'error': 'User is not the owner of this property'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
