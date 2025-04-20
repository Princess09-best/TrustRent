from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import User, Property
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.utils.timezone import now
import re
from django.shortcuts import render
from django.utils import timezone
from django.db import connections
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from ledger.models import PropertyLedger
import hashlib
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserProperty

# Registering a new user
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def register_user(request):
    if request.method == "OPTIONS":
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        # Validate required fields
        required_fields = ['firstname', 'lastname', 'email', 'phone_number', 'password', 'role', 'id_type', 'id_value']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'{field} is required'}, status=400)
        
        # Validate email format
        try:
            validate_email(data['email'])
        except ValidationError:
            return JsonResponse({'error': 'Invalid email format'}, status=400)

        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'error': 'Email already registered'}, status=400)

        # Validate phone number format (Ghana format: +233XXXXXXXXX)
        phone_pattern = r'^\+233[0-9]{9}$'
        if not re.match(phone_pattern, data['phone_number']):
            return JsonResponse({'error': 'Invalid phone number format. Use format: +233XXXXXXXXX'}, status=400)

        # Validate password strength
        if len(data['password']) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters long'}, status=400)

        # Validate role
        valid_roles = ['property_owner', 'property_seeker']
        if data['role'] not in valid_roles:
            return JsonResponse({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}, status=400)

        # Validate ID type and value
        valid_id_types = ['Ghana Card', 'Passport']
        if data['id_type'] not in valid_id_types:
            return JsonResponse({'error': f'Invalid ID type. Must be one of: {", ".join(valid_id_types)}'}, status=400)

        # Validate ID value format
        id_patterns = {
            'Ghana Card': r'^GHA-\d{9}-\d$',
            'Passport': r'^[A-Z]{1}\d{7}$'
        }
        if not re.match(id_patterns[data['id_type']], data['id_value']):
            return JsonResponse({
                'error': f'Invalid {data["id_type"]} format. ' + 
                        ('Use format: GHA-XXXXXXXXX-X' if data['id_type'] == 'Ghana Card' else 'Use format: LXXXXXXX')
            }, status=400)

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
        
        response = JsonResponse({
            'message': 'Registration successful! Please wait for account verification.',
            'status': 'pending_verification',
            'is_verified': False
        }, status=201)
        
        # Add user ID in response header
        response['X-User-Id'] = str(user.id)
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Logging in a user
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
            
            # For users registered before password hashing was implemented
            if not user.password_hash.startswith('pbkdf2_sha256$'):
                user.password_hash = make_password(user.password_hash)
                user.save()

            if not check_password(password, user.password_hash):
                return JsonResponse({'error': 'Invalid email or password'}, status=401)
            
            # Only check verification after password is confirmed
            if not user.is_verified:
                return JsonResponse({
                    'error': 'Account pending verification. Please wait for verification email.',
                    'is_verified': False
                }, status=403)

            # Generate JWT token properly using for_user
            refresh = RefreshToken.for_user(user)
            # Add custom claims
            refresh['email'] = user.email
            refresh['role'] = user.role

            # Updating last_login
            user.last_login = now()
            user.save()

            return JsonResponse({
                'message': 'Login successful',
                'token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'role': user.role,
                'is_verified': user.is_verified,
                'name': f"{user.firstname} {user.lastname}"
            })

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
    

# Creating a property by property owner only
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_property(request):
    try:
        data = json.loads(request.body)

        required_fields = ['title', 'property_type', 'description', 'location']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return Response({'error': f'Missing fields: {", ".join(missing)}'}, status=status.HTTP_400_BAD_REQUEST)

        # Get owner_id from authenticated user
        owner_id = request.user.id

        # Validate property type
        valid_property_types = [choice[0] for choice in Property.PROPERTY_TYPE_CHOICES]
        if data['property_type'] not in valid_property_types:
            return Response({
                'error': f'Invalid property type. Must be one of: {", ".join(valid_property_types)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create property
        property = Property.objects.create(
            title=data['title'],
            property_type=data['property_type'],
            description=data['description'],
            location=data['location'],
            status='pending_verification'
        )

        # Create user property association
        user_property = UserProperty.objects.create(
            property=property,
            owner_id=owner_id,
            is_verified=False,
            is_active=True
        )

        return Response({
            'message': 'Property created successfully. Awaiting verification.',
            'property_id': property.id,
            'user_property_id': user_property.id,
            'status': 'pending_verification'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Uploading a document
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    try:
        property_id = request.POST.get('property_id')
        file = request.FILES.get('attachment')

        if not property_id or not file:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type
        if not file.name.lower().endswith('.pdf'):
            return Response({
                'error': 'Invalid file type. Only PDF documents are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Additional validation for PDF mime type
        if file.content_type != 'application/pdf':
            return Response({
                'error': 'Invalid file type. Only PDF documents are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get user property and verify ownership
        try:
            user_property = UserProperty.objects.get(
                property_id=property_id,
                owner=request.user,
                is_active=True
            )
        except UserProperty.DoesNotExist:
            return Response({
                'error': 'Property not found or you do not have permission'
            }, status=status.HTTP_404_NOT_FOUND)

        # Generate document hash
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        document_hash = hasher.hexdigest()

        # Save file
        path = f'property_documents/{property_id}/{file.name}'
        saved_path = default_storage.save(path, ContentFile(file.read()))

        # Update user property with document info
        user_property.document_path = saved_path
        user_property.document_hash = document_hash
        user_property.document_uploaded_at = timezone.now()
        user_property.save()

        return Response({
            'message': 'Document uploaded successfully. The document will be reviewed during property verification.',
            'status': 'pending_review'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Getting all unverified properties by land commission representative 
@csrf_exempt
@require_http_methods(["GET"])
def get_unverified_properties(request):
    try:
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    up.id as user_property_id,
                    up.owner_id,
                    u.firstname,
                    u.lastname,
                    p.id as property_id,
                    p.title as property_title,
                    p.location as property_location,
                    up.verification_status,
                    pd.attachment as document_url
                FROM 
                    core_userproperty up
                    JOIN core_user u ON up.owner_id = u.id
                    JOIN core_property p ON up.property_id = p.id
                    LEFT JOIN core_propertydocument pd ON pd.user_property_id = up.id
                WHERE 
                    up.is_verified = false 
                    AND up.verification_status = 'pending'
            """)
            rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                "user_property_id": row[0],
                "owner_id": row[1],
                "owner_name": f"{row[2]} {row[3]}",
                "property_id": row[4],
                "property_title": row[5],
                "property_location": row[6],
                "verification_status": row[7],
                "document_url": row[8] if row[8] else None
            })
        
        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Verifying a property by land commission representative
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def verify_property(request):
    """
    Verify a property and register it on the blockchain if approved
    """
    try:
        # Get required fields from request
        user_property_id = request.data.get('user_property_id')
        verification_status = request.data.get('verification_status')

        if not user_property_id or not verification_status:
            return Response(
                {'error': 'user_property_id and verification_status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if verification_status not in ['approved', 'rejected']:
            return Response(
                {'error': 'verification_status must be either approved or rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the property
        try:
            user_property = UserProperty.objects.get(id=user_property_id)
        except UserProperty.DoesNotExist:
            return Response(
                {'error': 'Property not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update verification status and timestamps
        verification_time = timezone.now()
        user_property.verification_status = verification_status
        user_property.last_verified_at = verification_time
        
        # If approved, register on blockchain
        if verification_status == 'approved':
            try:
                # Get document hash if exists
                document_hash = user_property.get_document_hash()

                # Format property ID with PROP_ prefix
                property_id = f"PROP_{user_property.property.id}"

                # Register on blockchain with verifier ID as integers
                success, message, block = PropertyLedger.register_property(
                    property_id=property_id,
                    owner_id=int(user_property.owner.id),
                    document_hash=document_hash,
                    verified_by=int(request.user.id),
                    timestamp=verification_time
                )
                
                if not success:
                    return Response({
                        'error': f'Error registering property on blockchain: {message}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Update transaction hash and verification status
                user_property.transaction_hash = block.current_hash
                user_property.is_verified = True
                user_property.save()
                
                return Response({
                    'message': 'Property ownership verification approved successfully.',
                    'verification_status': verification_status,
                    'transaction_hash': block.current_hash,
                    'verified_at': verification_time
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': f'Error registering property on blockchain: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # If rejected, just save the status
        user_property.save()
        return Response({
            'message': 'Property verification status updated.',
            'verification_status': verification_status,
            'verified_at': verification_time
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Error processing verification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Rejecting a property by land commission representative
@csrf_exempt
@require_http_methods(["PATCH"])
def reject_property(request):
    try:
        data = json.loads(request.body)
        user_property_id = data.get('user_property_id')

        with connections['core'].cursor() as cursor:
            cursor.execute("""
                UPDATE core_userproperty 
                SET is_verified = false, verification_status = 'rejected', is_active = false
                WHERE id = %s
                RETURNING id
                """, [user_property_id])
            
            if not cursor.fetchone():
                return JsonResponse({'error': 'UserProperty not found.'}, status=404)

        return JsonResponse({'message': 'Property rejected, documents not correct'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_property_image(request):
    """Upload an image for a property"""
    try:
        property_id = request.POST.get('property_id')
        image = request.FILES.get('image')

        if not property_id or not image:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Validate image type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if image.content_type not in allowed_types:
            return JsonResponse({'error': 'Invalid image type. Only JPEG and PNG are allowed.'}, status=400)

        # Validate image size (max 10MB)
        if image.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'Image size too large. Maximum size is 10MB.'}, status=400)

        # Verify property exists and user has access
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT up.id 
                FROM core_userproperty up
                JOIN core_property p ON up.property_id = p.id
                WHERE p.id = %s AND up.owner_id = %s AND up.is_active = true
            """, [property_id, request.POST.get('user_id')])
            
            if not cursor.fetchone():
                return JsonResponse({'error': 'Property not found or access denied'}, status=404)

            # Save the image file
            file_name = f"property_{property_id}_{image.name}"
            saved_file_path = default_storage.save(f'property_images/{file_name}', ContentFile(image.read()))

            # Create PropertyImage record
            cursor.execute("""
                INSERT INTO core_propertyimage 
                (property_id, image, is_active, uploaded_at) 
                VALUES (%s, %s, %s, %s) RETURNING id
            """, [property_id, saved_file_path, True, timezone.now()])
            
            image_id = cursor.fetchone()[0]

        return JsonResponse({
            'message': 'Image uploaded successfully. The image will be displayed once processed.',
            'status': 'processing'
        }, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_all_properties(request):
    try:
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.id,
                    p.title,
                    p.property_type,
                    p.description,
                    p.location,
                    p.status,
                    p.created_at,
                    u.firstname,
                    u.lastname,
                    up.is_verified,
                    pi.image as property_image,
                    pl.price as listing_price,
                    pl.listing_type
                FROM 
                    core_property p
                    JOIN core_userproperty up ON p.id = up.property_id
                    JOIN core_user u ON up.owner_id = u.id
                    LEFT JOIN core_propertyimage pi ON p.id = pi.property_id AND pi.is_active = true
                    LEFT JOIN ops_propertylisting pl ON up.id = pl.user_property_id AND pl.is_active = true
                WHERE 
                    up.is_verified = true 
                    AND up.is_active = true
                    AND p.status != 'unlisted'
            """)
            rows = cursor.fetchall()

        properties = []
        for row in rows:
            properties.append({
                "id": row[0],
                "title": row[1],
                "property_type": row[2],
                "description": row[3],
                "location": row[4],
                "status": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "owner_name": f"{row[7]} {row[8]}",
                "is_verified": row[9],
                "property_image": row[10] if row[10] else None,
                "price": float(row[11]) if row[11] else None,
                "listing_type": row[12]
            })
        
        return JsonResponse(properties, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_property_detail(request, property_id):
    try:
        property_data = {}
        
        # First get property details from core database
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.id, p.title, p.property_type, p.description, 
                    p.location, p.status,
                    u.firstname, u.lastname, u.phone_number,
                    up.id as user_property_id
                FROM core_property p
                JOIN core_userproperty up ON p.id = up.property_id
                JOIN core_user u ON up.owner_id = u.id
                WHERE 
                    p.id = %s 
                    AND up.is_verified = true 
                    AND up.is_active = true
                    AND p.status = 'available'
            """, [property_id])
            
            result = cursor.fetchone()
            if not result:
                return Response({'error': 'Property not found or not available'}, status=status.HTTP_404_NOT_FOUND)
            
            columns = ['id', 'title', 'property_type', 'description', 'location', 'status', 
                      'owner_firstname', 'owner_lastname', 'owner_phone', 'user_property_id']
            property_data = dict(zip(columns, result))
            
            # Format owner information
            property_data['owner'] = {
                'name': f"{property_data.pop('owner_firstname')} {property_data.pop('owner_lastname')}",
                'phone': property_data.pop('owner_phone')
            }
            
            user_property_id = property_data.pop('user_property_id')  # We'll use this to get listing info
            
            # Get only active property images
            cursor.execute("""
                SELECT image
                FROM core_propertyimage
                WHERE property_id = %s AND is_active = true
                ORDER BY uploaded_at DESC
            """, [property_id])
            property_data['images'] = [row[0] for row in cursor.fetchall()]

        # Then get listing details from ops database
        with connections['ops'].cursor() as cursor:
            cursor.execute("""
                SELECT id, listing_type, price
                FROM ops_propertylisting 
                WHERE user_property_id = %s AND is_active = true
            """, [user_property_id])
            
            listing = cursor.fetchone()
            if listing:
                listing_columns = ['listing_id', 'listing_type', 'price']
                listing_data = dict(zip(listing_columns, listing))
                # Add listing data to property data
                property_data.update(listing_data)
            
        return Response(property_data)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_document_access(request):
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        reason = data.get('reason')

        if not all([property_id, reason]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Get requester from authenticated user
        requester = request.user

        # Verify property exists and is available
        with connections['core'].cursor() as cursor:
            # First verify the requester is a property seeker
            if requester.role != 'property_seeker':
                return Response({
                    'error': 'Only property seekers can request document access'
                }, status=status.HTTP_403_FORBIDDEN)

            # Then check property and get user_property_id
            cursor.execute("""
                SELECT up.id, up.owner_id 
                FROM core_userproperty up
                JOIN core_property p ON up.property_id = p.id
                WHERE p.id = %s AND up.is_verified = true AND p.status = 'available'
            """, [property_id])
            
            result = cursor.fetchone()
            if not result:
                return Response({'error': 'Property not found or not available'}, status=status.HTTP_404_NOT_FOUND)
            
            user_property_id, owner_id = result

            # Check if requester is not the owner
            if requester.id == owner_id:
                return Response({
                    'error': 'Property owners cannot request access to their own documents'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if there's already a pending or approved request
            cursor.execute("""
                SELECT status 
                FROM core_documentaccessrequest 
                WHERE user_property_id = %s AND requester_id = %s AND status IN ('pending', 'approved')
            """, [user_property_id, requester.id])
            
            if cursor.fetchone():
                return Response({
                    'error': 'You already have a pending or approved request for this document'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create the request
            cursor.execute("""
                INSERT INTO core_documentaccessrequest 
                (user_property_id, requester_id, request_date, status, reason) 
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [
                user_property_id,
                requester.id,
                timezone.now(),
                'pending',
                reason
            ])
            
            request_id = cursor.fetchone()[0]

        response_data = {
            'message': 'Document access request submitted successfully. Awaiting owner approval.',
            'status': 'pending',
            'request_id': request_id
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_document_request(request):
    try:
        data = json.loads(request.body)
        request_id = data.get('request_id')
        decision = data.get('decision')
        response_note = data.get('response_note', '')

        if not all([request_id, decision]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if decision not in ['approved', 'denied']:
            return Response({'error': 'Invalid decision. Must be either "approved" or "denied"'}, status=status.HTTP_400_BAD_REQUEST)

        with connections['core'].cursor() as cursor:
            # Verify the request exists and owner has rights
            cursor.execute("""
                SELECT dar.status, up.owner_id, u.email as requester_email
                FROM core_documentaccessrequest dar
                JOIN core_userproperty up ON dar.user_property_id = up.id
                JOIN core_user u ON dar.requester_id = u.id
                WHERE dar.id = %s
            """, [request_id])
            
            result = cursor.fetchone()
            if not result:
                return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
            
            current_status, request_owner_id, requester_email = result

            # Verify ownership
            if request.user.id != request_owner_id:
                return Response({'error': 'You do not have permission to respond to this request'}, status=status.HTTP_403_FORBIDDEN)

            # Check if request is still pending
            if current_status != 'pending':
                return Response({'error': 'This request has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

            # Update request status
            cursor.execute("""
                UPDATE core_documentaccessrequest 
                SET status = %s, response_date = %s, response_note = %s
                WHERE id = %s
            """, [decision, timezone.now(), response_note, request_id])

        return Response({
            'message': f'Document access request {decision}',
            'requester_email': requester_email
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_requests(request):
    try:
        role = request.user.role

        with connections['core'].cursor() as cursor:
            if role == 'property_owner':
                # Get requests for owner's properties
                cursor.execute("""
                    SELECT 
                        p.title as property_title,
                        u.firstname || ' ' || u.lastname as requester_name,
                        u.email as requester_email,
                        dar.request_date,
                        dar.status,
                        dar.reason,
                        dar.response_date,
                        dar.response_note
                    FROM core_documentaccessrequest dar
                    JOIN core_userproperty up ON dar.user_property_id = up.id
                    JOIN core_property p ON up.property_id = p.id
                    JOIN core_user u ON dar.requester_id = u.id
                    WHERE up.owner_id = %s
                    ORDER BY dar.request_date DESC
                """, [request.user.id])
            elif role == 'property_seeker':
                # Get requests made by the property seeker
                cursor.execute("""
                    SELECT 
                        p.title as property_title,
                        u.firstname || ' ' || u.lastname as owner_name,
                        dar.request_date,
                        dar.status,
                        dar.reason,
                        dar.response_date,
                        dar.response_note
                    FROM core_documentaccessrequest dar
                    JOIN core_userproperty up ON dar.user_property_id = up.id
                    JOIN core_property p ON up.property_id = p.id
                    JOIN core_user u ON up.owner_id = u.id
                    WHERE dar.requester_id = %s
                    ORDER BY dar.request_date DESC
                """, [request.user.id])
            else:
                return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

            columns = ['property_title', 'contact_name', 'contact_email' if role == 'property_owner' else None,
                      'request_date', 'status', 'reason', 'response_date', 'response_note']
            columns = [col for col in columns if col is not None]
            
            requests = []
            for row in cursor.fetchall():
                request_data = dict(zip(columns, row))
                # Convert datetime objects to ISO format strings
                request_data['request_date'] = request_data['request_date'].isoformat()
                if request_data['response_date']:
                    request_data['response_date'] = request_data['response_date'].isoformat()
                requests.append(request_data)

        return Response(requests)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)