from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import DocumentAccessRequest, User, Property, PropertyImage, UserProperty, VerificationHistory, PropertyDocument
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.utils.timezone import now
import re
from django.shortcuts import render
from django.utils import timezone
from django.db import connections, connection
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
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import UserProperty
from .permissions import (
    UserPermission, 
    has_permission, 
    UserRole, 
    SYSTEM_ALLOWED_ROLES, 
    HasUserPermission,
    ROLE_PERMISSIONS
)
from .utils import send_otp_via_email, send_otp_via_sms

# Global variable for role permissions
ROLE_PERMISSIONS = ROLE_PERMISSIONS

# Registering a new user
@api_view(['POST', 'OPTIONS'])
@permission_classes([HasUserPermission(UserPermission.REGISTER_ACCOUNT.value)])
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

        # Validate role based on access matrix
        valid_roles = [UserRole.PROPERTY_OWNER.value, UserRole.PROPERTY_SEEKER.value]
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

        # Create the user
        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            firstname=data['firstname'],
            lastname=data['lastname'],
            phone_number=data['phone_number'],
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

# Modified login function to handle MFA
@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        otp = data.get('otp')  # Optional OTP for 2FA

        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)

        try:
            user = User.objects.get(email=email)
            
            if not user.check_password(password):
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
            
            if not user.is_verified:
                return JsonResponse({
                    'error': 'Account pending verification',
                    'status': 'pending'
                }, status=403)

            # Check if MFA is enabled for this user
            if user.mfa_enabled:
                # If OTP is provided, verify it
                if otp:
                    if not user.verify_otp(otp):
                        return JsonResponse({
                            'error': 'Invalid or expired OTP',
                            'mfa_required': True
                        }, status=401)
                    
                    # OTP verified, clear it
                    user.clear_otp()
                else:
                    # No OTP provided, but MFA is required
                    # Generate and send a new OTP
                    new_otp = user.generate_otp()
                    
                    # Send OTP via the user's preferred method
                    if user.mfa_method == 'email':
                        success, message = send_otp_via_email(user.email, new_otp, user.firstname)
                    elif user.mfa_method == 'sms':
                        success, message = send_otp_via_sms(user.phone_number, new_otp, user.firstname)
                    else:
                        success, message = False, "MFA method not configured"
                    
                    if not success:
                        return JsonResponse({'error': message}, status=500)
                    
                    return JsonResponse({
                        'message': 'OTP sent for verification',
                        'mfa_required': True,
                        'mfa_method': user.mfa_method
                    }, status=200)

            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            
            # Update last login
            user.last_login = now()
            user.save()

            # Set tokens in response headers
            response = JsonResponse({'message': 'Login successful'})
            response['Authorization'] = f'Bearer {str(refresh.access_token)}'
            response['X-Refresh-Token'] = str(refresh)
            
            return response

        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Login failed'}, status=500)

#function for admin to get all unverified users
@api_view(['GET'])
@permission_classes([HasUserPermission(UserPermission.VIEW_UNVERIFIED_USERS.value)])
def get_unverified_users(request):
    """
    Get list of all unverified users.
    Only accessible by system admins.
    """
    users = User.objects.filter(is_verified=False).values(
        'id', 'firstname', 'lastname', 'email', 'role', 'id_type', 'id_value'
    )
    return Response(list(users), status=status.HTTP_200_OK)

#function for admin to verify users using id regex validation
@csrf_exempt
@api_view(['PATCH'])
@permission_classes([HasUserPermission(UserPermission.VERIFY_USERS.value)])
def verify_user(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')

        # Validate user_id format
        if not isinstance(user_id, (int, str)) or (isinstance(user_id, str) and not user_id.isdigit()):
            return JsonResponse({'error': 'Invalid user_id format. Must be a number'}, status=400)

        # Convert to integer for database query
        user_id = int(user_id)
        user = User.objects.get(id=user_id)

        # Check if user is already verified
        if user.is_verified:
            return JsonResponse({'error': 'User is already verified'}, status=400)

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
    except ValueError:
        return JsonResponse({'error': 'Invalid user_id format. Must be a number'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

# Creating a property by property owner only
@api_view(['POST'])
@permission_classes([HasUserPermission(UserPermission.CREATE_PROPERTY.value)])
def create_property(request):
    try:
        print("\n=== Create Property Debug ===")
        print(f"User: {request.user}")
        print(f"User role: {request.user.role}")
        print(f"User permissions: {ROLE_PERMISSIONS.get(request.user.role, [])}")
        print(f"Required permission: {UserPermission.CREATE_PROPERTY.value}")
        print(f"Is authenticated: {request.user.is_authenticated}")
        print(f"Is superuser: {getattr(request.user, 'is_superuser', False)}")
        
        # Check permission using the string value
        if UserPermission.CREATE_PROPERTY.value not in ROLE_PERMISSIONS.get(request.user.role, []):
            print("Permission denied - user does not have CREATE_PROPERTY permission")
            return Response(
                {'error': 'You do not have permission to create properties'}, 
                status=status.HTTP_403_FORBIDDEN
            )

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
            status='unlisted'
        )

        # Create user property association
        user_property = UserProperty.objects.create(
            property=property,
            owner_id=owner_id,
            is_verified=False,
            is_active=True
        )

        # Create response with clean body and IDs in headers
        response = Response({
            'message': 'Property created successfully. Awaiting verification.',
            'status': 'pending_verification'
        }, status=status.HTTP_201_CREATED)
        
        # Add IDs to response headers with prefixes
        response['X-Resource-Id'] = f"PROP_{property.id}"
        response['X-UserProperty-Id'] = f"UP_{user_property.id}"
        return response

    except Exception as e:
        print(f"Error in create_property: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Uploading a document
@api_view(['POST'])
@permission_classes([HasUserPermission(UserPermission.UPLOAD_PROPERTY_DOCUMENT.value)])
def upload_document(request):
    try:
        print(f"User role: {request.user.role}")
        print(f"User permissions: {ROLE_PERMISSIONS.get(request.user.role, [])}")
        
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
            
            # Check if property is already verified - cannot upload documents to verified properties
            if user_property.is_verified:
                return Response({
                    'error': 'Cannot upload documents to a property that has already been verified.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
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

        # Create PropertyDocument record
        PropertyDocument.objects.create(
            user_property_id=user_property.id,
            attachment=saved_path,
           
            uploaded_at=timezone.now()
        )


        return Response({
            'message': 'Document uploaded successfully. The document will be reviewed during property verification.',
            'status': 'pending_review'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([HasUserPermission(UserPermission.VIEW_UNVERIFIED_PROPERTIES.value)])
def get_unverified_properties(request):
    """
    Get a list of all unverified properties.
    Only accessible by land commission representatives and system admins.
    """
    try:
        unverified_properties = UserProperty.objects.filter(
            is_verified=False,
            is_active=True
        ).select_related('property', 'owner')
        
        properties_data = []
        for user_property in unverified_properties:
            property_data = {
                'id': user_property.property.id,
                'title': user_property.property.title,
                'description': user_property.property.description,
                'location': user_property.property.location,
                'owner': {
                    'id': user_property.owner.id,
                    'email': user_property.owner.email,
                    'full_name': f"{user_property.owner.firstname} {user_property.owner.lastname}"
                },
                'created_at': user_property.created_at,
                'documents': [doc.attachment.url for doc in user_property.documents.all()],
                'images': [img.image.url for img in user_property.property.images.all()]
            }
            properties_data.append(property_data)
        
        return JsonResponse(properties_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['PATCH'])
@permission_classes([HasUserPermission(UserPermission.VERIFY_PROPERTY.value)])
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
            
        # Store previous status for history tracking
        previous_status = user_property.verification_status

        # If approving, check that required documents are uploaded
        if verification_status == 'approved':
            # Check if the property has at least one document uploaded
            #if not user_property.document_path or not user_property.document_hash:
                #return Response(
                    #{'error': 'Property cannot be approved without at least one document uploaded.'},
                    #status=status.HTTP_400_BAD_REQUEST
                #)
                
            # Check if the property has at least one image (optional check)
            images_count = PropertyImage.objects.filter(
                property_id=user_property.property.id,
                is_active=True
            ).count()
            
            if images_count == 0:
                return Response(
                    {'error': 'Property cannot be approved without at least one image uploaded.'},
                    status=status.HTTP_400_BAD_REQUEST
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
                
                # Create verification history entry
                VerificationHistory.objects.create(
                    user_property=user_property,
                    previous_status=previous_status,
                    new_status=verification_status,
                    changed_at=verification_time
                )
                
                return Response({
                    'message': 'Property ownership verification approved successfully.',
                    'verification_status': verification_status
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': f'Error registering property on blockchain: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # If rejected, save the status and create history entry
        user_property.save()
        
        # Create verification history entry for rejection
        VerificationHistory.objects.create(
            user_property=user_property,
            previous_status=previous_status,
            new_status=verification_status,
            changed_at=verification_time
        )
        
        return Response({
            'message': 'Property verification status updated.',
            'verification_status': verification_status
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Error processing verification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


    
@api_view(['POST'])
@permission_classes([HasUserPermission(UserPermission.REJECT_PROPERTY.value)])
def reject_property(request):
    """
    Reject a property with a reason
    """
    try:
        # Get required fields from request
        user_property_id = request.data.get('user_property_id')
        rejection_reason = request.data.get('rejection_reason')

        if not user_property_id or not rejection_reason:
            return Response(
                {'error': 'user_property_id and rejection_reason are required'},
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
            
        # Store previous status for history tracking
        previous_status = user_property.verification_status

        # Update verification status and rejection details
        rejection_time = timezone.now()
        user_property.verification_status = 'rejected'
        user_property.rejection_reason = rejection_reason
        user_property.last_verified_at = rejection_time
        user_property.save()
        
        # Create verification history entry
        VerificationHistory.objects.create(
            user_property=user_property,
            previous_status=previous_status,
            new_status='rejected',
            changed_at=rejection_time
        )

        return Response({
            'message': 'Property rejected successfully.',
            'rejection_reason': rejection_reason
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Error rejecting property: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([HasUserPermission(UserPermission.UPLOAD_PROPERTY_IMAGE.value)])
def upload_property_image(request):
    """Upload an image for a property"""
    try:
        print(f"User role: {request.user.role}")
        print(f"User permissions: {ROLE_PERMISSIONS.get(request.user.role, [])}")
        
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
        try:
            user_property = UserProperty.objects.get(
                property_id=property_id,
                owner=request.user,
                is_active=True
            )
            
            # Check if property is already verified - cannot upload images to verified properties
            if user_property.is_verified:
                return JsonResponse({
                    'error': 'Cannot upload images to a property that has already been verified.'
                }, status=400)
                
        except UserProperty.DoesNotExist:
            return JsonResponse({'error': 'Property not found or you do not have permission'}, status=404)

        # Save the image file
        file_name = f"property_{property_id}_{image.name}"
        saved_file_path = default_storage.save(f'property_images/{file_name}', ContentFile(image.read()))

        # Create PropertyImage record
        PropertyImage.objects.create(
            property_id=property_id,
            image=saved_file_path,
            is_active=True,
            uploaded_at=timezone.now()
        )

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
        with connection.cursor() as cursor:
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
        # Check if user is a property seeker
        if request.user.role != 'property_seeker':
            return Response({'error': 'Only property seekers can view property details'}, 
                          status=status.HTTP_403_FORBIDDEN)

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
                return Response({'error': 'Property not found or not available'}, 
                              status=status.HTTP_404_NOT_FOUND)
            
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
        # Check if user is a property seeker
        if request.user.role != 'property_seeker':
            return Response({'error': 'Only property seekers can request document access'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        data = json.loads(request.body)
        property_id = data.get('property_id')
        reason = data.get('reason')

        if not all([property_id, reason]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Get requester from authenticated user
        requester = request.user

        # Verify property exists and is available
        with connection.cursor() as cursor:
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

        # Check if user is a property owner
        if request.user.role != 'property_owner':
            return Response({'error': 'Only property owners can respond to document requests'}, 
                          status=status.HTTP_403_FORBIDDEN) 
        data = json.loads(request.body)
        request_id = data.get('request_id')
        decision = data.get('decision')
        response_note = data.get('response_note', '')

        if not all([request_id, decision]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if decision not in ['approved', 'denied']:
            return Response({'error': 'Invalid decision. Must be either "approved" or "denied"'}, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
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

        with connection.cursor() as cursor:
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

@api_view(['POST'])
@permission_classes([HasUserPermission(UserPermission.CREATE_ADMIN_ACCOUNT.value)])
def create_admin_account(request):
    """
    Endpoint for system administrators to create land commission rep and admin accounts.
    Only accessible by existing system administrators.
    """
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

        # Validate role - only allow system roles
        if data['role'] not in SYSTEM_ALLOWED_ROLES:
            return JsonResponse({
                'error': f'Invalid role. Must be one of: {", ".join(SYSTEM_ALLOWED_ROLES)}'
            }, status=400)

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

        # Create the admin/land rep account - automatically verified
        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            firstname=data['firstname'],
            lastname=data['lastname'],
            phone_number=data['phone_number'],
            role=data['role'],
            id_type=data['id_type'],
            id_value=data['id_value'],
            is_verified=True,  # Admin created accounts are automatically verified
            is_staff=True if data['role'] == UserRole.SYS_ADMIN.value else False,
            is_superuser=True if data['role'] == UserRole.SYS_ADMIN.value else False
        )
        
        response = JsonResponse({
            'message': f'{data["role"]} account created successfully.',
            'email': user.email,
            'role': user.role
        }, status=201)
        
        return response
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Add new endpoints for MFA management

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enable_mfa(request):
    """
    Enable MFA for the authenticated user
    """
    try:
        data = json.loads(request.body)
        mfa_method = data.get('mfa_method')
        
        if not mfa_method or mfa_method not in ['email', 'sms']:
            return JsonResponse({
                'error': 'Invalid MFA method. Choose either "email" or "sms"'
            }, status=400)
        
        user = request.user
        
        # Generate an OTP for verification
        otp = user.generate_otp()
        
        # Send OTP via the selected method
        if mfa_method == 'email':
            success, message = send_otp_via_email(user.email, otp, user.firstname)
        else:  # sms
            success, message = send_otp_via_sms(user.phone_number, otp, user.firstname)
        
        if not success:
            return JsonResponse({'error': message}, status=500)
        
        # Update user's MFA preference but don't enable until verified
        user.mfa_method = mfa_method
        user.save(update_fields=['mfa_method'])
        
        return JsonResponse({
            'message': f'OTP sent to your {mfa_method}. Verify to enable MFA.',
            'mfa_method': mfa_method
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_mfa_setup(request):
    """
    Verify OTP to complete MFA setup
    """
    try:
        data = json.loads(request.body)
        otp = data.get('otp')
        
        if not otp:
            return JsonResponse({'error': 'OTP is required'}, status=400)
        
        user = request.user
        
        if not user.verify_otp(otp):
            return JsonResponse({'error': 'Invalid or expired OTP'}, status=401)
        
        # OTP is valid, enable MFA
        user.mfa_enabled = True
        user.clear_otp()  # Clear the OTP after successful verification
        user.save(update_fields=['mfa_enabled'])
        
        return JsonResponse({'message': 'MFA enabled successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_mfa(request):
    """
    Disable MFA for the authenticated user
    """
    try:
        user = request.user
        
        if not user.mfa_enabled:
            return JsonResponse({'error': 'MFA is not enabled'}, status=400)
        
        # Disable MFA
        user.mfa_enabled = False
        user.mfa_method = None
        user.save(update_fields=['mfa_enabled', 'mfa_method'])
        
        return JsonResponse({'message': 'MFA disabled successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get the profile information for the currently authenticated user.
    This endpoint requires a valid JWT token in the Authorization header.
    """
    try:
        user = request.user
        
        # Prepare the user profile data
        profile_data = {
            'id': user.id,
            'first_name': user.firstname,
            'last_name': user.lastname,
            'email': user.email,
            'phone_number': user.phone_number,
            'role': user.role,
            'is_verified': user.is_verified,
            'created_at': user.created_at,
            'last_login': user.last_login
        }
        
        # Get role-specific stats
        stats = {}
        if user.role == 'property_owner':
            try:
                # Get basic property stats from the core database directly using Django ORM
                owned_properties = UserProperty.objects.filter(owner=user)
                stats = {
                    'total_properties': owned_properties.count(),
                    'verified_properties': owned_properties.filter(is_verified=True).count(),
                    'pending_properties': owned_properties.filter(verification_status='pending').count(),
                    'active_listings': 0,  # Default value until we fetch from ops
                    'total_agreements': 0,
                    'pending_agreements': 0,
                    'total_document_requests': 0,
                    'pending_document_requests': 0,
                    'total_transfers': 0,
                    'pending_transfers': 0
                }
                
                # Get the user property IDs first
                try:
                    user_property_ids = list(owned_properties.values_list('id', flat=True))
                    
                    # Get active listings count from ops database using the list of user_property_ids
                    if user_property_ids:
                        try:
                            with connections['ops'].cursor() as cursor:
                                # Using placeholders to prevent SQL injection
                                placeholders = ','.join(['%s'] * len(user_property_ids))
                                cursor.execute(f"""
                                    SELECT COUNT(*) 
                                    FROM ops_propertylisting
                                    WHERE user_property_id IN ({placeholders}) AND is_active = true
                                """, user_property_ids)
                                stats['active_listings'] = cursor.fetchone()[0]
                        except Exception as e:
                            print(f"Error fetching active listings from ops database: {str(e)}")
                            # We'll keep the default value of 0 for active_listings
                    
                    # Get rental agreement data from ledger database - using separate queries
                    try:
                        with connections['ledger'].cursor() as cursor:
                            # Check if rental_agreement table exists
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_schema = 'public'
                                    AND table_name = 'ledger_rental_agreement'
                                )
                            """)
                            
                            if cursor.fetchone()[0]:  # Table exists
                                # Total and pending agreements
                                cursor.execute("""
                                    SELECT COUNT(*), 
                                        COUNT(CASE WHEN status = 'pending' THEN 1 END)
                                    FROM ledger_rental_agreement
                                    WHERE owner_id = %s
                                """, [user.id])
                                result = cursor.fetchone()
                                if result:
                                    stats['total_agreements'] = result[0]
                                    stats['pending_agreements'] = result[1]
                            
                            # Check if property_transfer table exists
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_schema = 'public'
                                    AND table_name = 'property_transfer'
                                )
                            """)
                            
                            if cursor.fetchone()[0]:  # Table exists
                                cursor.execute("""
                                    SELECT COUNT(*),
                                        COUNT(CASE WHEN status = 'pending' THEN 1 END)
                                    FROM property_transfer
                                    WHERE current_owner_id = %s
                                """, [user.id])
                                result = cursor.fetchone()
                                if result:
                                    stats['total_transfers'] = result[0]
                                    stats['pending_transfers'] = result[1]
                    except Exception as e:
                        print(f"Error fetching ledger stats: {str(e)}")
                        # We'll keep the default values we set earlier
                    
                    # Get document request stats from core database
                    try:
                        # Query document_access_request from the core database
                        if user_property_ids:
                            placeholders = ','.join(['%s'] * len(user_property_ids))
                            with connection.cursor() as cursor:  # Use default connection for core
                                cursor.execute(f"""
                                    SELECT COUNT(*),
                                        COUNT(CASE WHEN status = 'pending' THEN 1 END)
                                    FROM core_documentaccessrequest
                                    WHERE user_property_id IN ({placeholders})
                                """, user_property_ids)
                                result = cursor.fetchone()
                                if result:
                                    stats['total_document_requests'] = result[0]
                                    stats['pending_document_requests'] = result[1]
                    except Exception as e:
                        print(f"Error fetching document request stats: {str(e)}")
                        # We'll keep the default values we set earlier
                except Exception as e:
                    print(f"Error getting user property IDs: {str(e)}")
            except Exception as e:
                print(f"Error in property owner stats: {str(e)}")
                stats = {
                    'total_properties': 0,
                    'verified_properties': 0,
                    'pending_properties': 0,
                    'active_listings': 0,
                    'total_agreements': 0,
                    'pending_agreements': 0
                }
        
        elif user.role == 'property_seeker':
            try:
                # Directly query DocumentAccessRequest from the core database
                access_requests = DocumentAccessRequest.objects.filter(requester=user)
                stats = {
                    'total_requests': access_requests.count(),
                    'pending_requests': access_requests.filter(status='pending').count(),
                    'approved_requests': access_requests.filter(status='approved').count(),
                    'total_agreements': 0,
                    'active_agreements': 0,
                    'pending_agreements': 0
                }
                
                # Get rental agreement stats from ledger database
                try:
                    with connections['ledger'].cursor() as cursor:
                        # Check if rental_agreement table exists
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public'
                                AND table_name = 'ledger_rental_agreement'
                            )
                        """)
                        
                        if cursor.fetchone()[0]:  # Table exists
                            cursor.execute("""
                                SELECT COUNT(*),
                                    COUNT(CASE WHEN status = 'active' THEN 1 END),
                                    COUNT(CASE WHEN status = 'pending' THEN 1 END)
                                FROM ledger_rental_agreement
                                WHERE tenant_id = %s
                            """, [user.id])
                            result = cursor.fetchone()
                            if result:
                                stats.update({
                                    'total_agreements': result[0] or 0,
                                    'active_agreements': result[1] or 0,
                                    'pending_agreements': result[2] or 0
                                })
                except Exception as e:
                    print(f"Error fetching seeker agreement stats: {str(e)}")
            except Exception as e:
                print(f"Error in property seeker stats: {str(e)}")
                stats = {
                    'total_requests': 0,
                    'pending_requests': 0,
                    'approved_requests': 0,
                    'total_agreements': 0,
                    'active_agreements': 0,
                    'pending_agreements': 0
                }
        
        elif user.role == 'land_rep':
            try:
                stats = {
                    'total_verifications': VerificationHistory.objects.filter(
                        user_property__property__ownership_records__owner=user
                    ).count(),
                    'pending_verifications': UserProperty.objects.filter(
                        verification_status='pending'
                    ).count()
                }
            except Exception as e:
                print(f"Error getting land rep stats: {str(e)}")
                stats = {
                    'total_verifications': 0,
                    'pending_verifications': 0
                }
                
        elif user.role == 'admin' or user.role == 'sys_admin':
            try:
                stats = {
                    'total_users': User.objects.count(),
                    'pending_verifications': User.objects.filter(is_verified=False).count(),
                    'total_properties': Property.objects.count()
                }
            except Exception as e:
                print(f"Error getting admin stats: {str(e)}")
                stats = {
                    'total_users': 0,
                    'pending_verifications': 0,
                    'total_properties': 0
                }
            
        profile_data['stats'] = stats
        
        return Response(profile_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        return Response(
            {'error': 'Failed to fetch user profile', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics for the currently authenticated user.
    This is a simplified version of the user profile endpoint that returns only the stats.
    """
    try:
        user = request.user
        
        # Get role-specific stats
        stats = {}
        if user.role == 'property_owner':
            try:
                # Get basic property stats from the core database directly using Django ORM
                owned_properties = UserProperty.objects.filter(owner=user)
                stats = {
                    'total_properties': owned_properties.count(),
                    'verified_properties': owned_properties.filter(is_verified=True).count(),
                    'pending_properties': owned_properties.filter(verification_status='pending').count(),
                    'active_listings': 0,  # Default value until we fetch from ops
                    'total_agreements': 0,
                    'pending_agreements': 0,
                    'total_document_requests': 0,
                    'pending_document_requests': 0,
                    'total_transfers': 0,
                    'pending_transfers': 0
                }
                
                # Get the user property IDs first
                try:
                    user_property_ids = list(owned_properties.values_list('id', flat=True))
                    
                    # Get active listings count from ops database using the list of user_property_ids
                    if user_property_ids:
                        try:
                            with connections['ops'].cursor() as cursor:
                                # Using placeholders to prevent SQL injection
                                placeholders = ','.join(['%s'] * len(user_property_ids))
                                cursor.execute(f"""
                                    SELECT COUNT(*) 
                                    FROM ops_propertylisting
                                    WHERE user_property_id IN ({placeholders}) AND is_active = true
                                """, user_property_ids)
                                stats['active_listings'] = cursor.fetchone()[0]
                        except Exception as e:
                            print(f"Error fetching active listings from ops database: {str(e)}")
                            # We'll keep the default value of 0 for active_listings
                    
                    # Get rental agreement data from ledger database - using separate queries
                    try:
                        with connections['ledger'].cursor() as cursor:
                            # Check if rental_agreement table exists
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_schema = 'public'
                                    AND table_name = 'ledger_rental_agreement'
                                )
                            """)
                            
                            if cursor.fetchone()[0]:  # Table exists
                                # Total and pending agreements
                                cursor.execute("""
                                    SELECT COUNT(*), 
                                        COUNT(CASE WHEN status = 'pending' THEN 1 END)
                                    FROM ledger_rental_agreement
                                    WHERE owner_id = %s
                                """, [user.id])
                                result = cursor.fetchone()
                                if result:
                                    stats['total_agreements'] = result[0]
                                    stats['pending_agreements'] = result[1]
                            
                            # Check if property_transfer table exists
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_schema = 'public'
                                    AND table_name = 'property_transfer'
                                )
                            """)
                            
                            if cursor.fetchone()[0]:  # Table exists
                                cursor.execute("""
                                    SELECT COUNT(*),
                                        COUNT(CASE WHEN status = 'pending' THEN 1 END)
                                    FROM property_transfer
                                    WHERE current_owner_id = %s
                                """, [user.id])
                                result = cursor.fetchone()
                                if result:
                                    stats['total_transfers'] = result[0]
                                    stats['pending_transfers'] = result[1]
                    except Exception as e:
                        print(f"Error fetching ledger stats: {str(e)}")
                        # We'll keep the default values we set earlier
                    
                    # Get document request stats from core database
                    try:
                        # Query document_access_request from the core database
                        if user_property_ids:
                            placeholders = ','.join(['%s'] * len(user_property_ids))
                            with connection.cursor() as cursor:  # Use default connection for core
                                cursor.execute(f"""
                                    SELECT COUNT(*),
                                        COUNT(CASE WHEN status = 'pending' THEN 1 END)
                                    FROM core_documentaccessrequest
                                    WHERE user_property_id IN ({placeholders})
                                """, user_property_ids)
                                result = cursor.fetchone()
                                if result:
                                    stats['total_document_requests'] = result[0]
                                    stats['pending_document_requests'] = result[1]
                    except Exception as e:
                        print(f"Error fetching document request stats: {str(e)}")
                        # We'll keep the default values we set earlier
                except Exception as e:
                    print(f"Error getting user property IDs: {str(e)}")
            except Exception as e:
                print(f"Error in property owner stats: {str(e)}")
                stats = {
                    'total_properties': 0,
                    'verified_properties': 0,
                    'pending_properties': 0,
                    'active_listings': 0,
                    'total_agreements': 0,
                    'pending_agreements': 0
                }
        
        elif user.role == 'property_seeker':
            try:
                # Directly query DocumentAccessRequest from the core database
                access_requests = DocumentAccessRequest.objects.filter(requester=user)
                stats = {
                    'total_requests': access_requests.count(),
                    'pending_requests': access_requests.filter(status='pending').count(),
                    'approved_requests': access_requests.filter(status='approved').count(),
                    'total_agreements': 0,
                    'active_agreements': 0,
                    'pending_agreements': 0
                }
                
                # Get rental agreement stats from ledger database
                try:
                    with connections['ledger'].cursor() as cursor:
                        # Check if rental_agreement table exists
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public'
                                AND table_name = 'ledger_rental_agreement'
                            )
                        """)
                        
                        if cursor.fetchone()[0]:  # Table exists
                            cursor.execute("""
                                SELECT COUNT(*),
                                    COUNT(CASE WHEN status = 'active' THEN 1 END),
                                    COUNT(CASE WHEN status = 'pending' THEN 1 END)
                                FROM ledger_rental_agreement
                                WHERE tenant_id = %s
                            """, [user.id])
                            result = cursor.fetchone()
                            if result:
                                stats.update({
                                    'total_agreements': result[0] or 0,
                                    'active_agreements': result[1] or 0,
                                    'pending_agreements': result[2] or 0
                                })
                except Exception as e:
                    print(f"Error fetching seeker agreement stats: {str(e)}")
            except Exception as e:
                print(f"Error in property seeker stats: {str(e)}")
                stats = {
                    'total_requests': 0,
                    'pending_requests': 0,
                    'approved_requests': 0,
                    'total_agreements': 0,
                    'active_agreements': 0,
                    'pending_agreements': 0
                }
        
        elif user.role == 'land_rep':
            try:
                stats = {
                    'total_verifications': VerificationHistory.objects.filter(
                        user_property__property__ownership_records__owner=user
                    ).count(),
                    'pending_verifications': UserProperty.objects.filter(
                        verification_status='pending'
                    ).count()
                }
            except Exception as e:
                print(f"Error getting land rep stats: {str(e)}")
                stats = {
                    'total_verifications': 0,
                    'pending_verifications': 0
                }
                
        elif user.role == 'admin' or user.role == 'sys_admin':
            try:
                stats = {
                    'total_users': User.objects.count(),
                    'pending_verifications': User.objects.filter(is_verified=False).count(),
                    'total_properties': Property.objects.count()
                }
            except Exception as e:
                print(f"Error getting admin stats: {str(e)}")
                stats = {
                    'total_users': 0,
                    'pending_verifications': 0,
                    'total_properties': 0
                }
        
        # Convert database counts to frontend expected format for dashboard
        if user.role == 'property_owner':
            dashboard_stats = {
                'properties': stats.get('total_properties', 0),
                'agreements': stats.get('total_agreements', 0),
                'pendingAgreements': stats.get('pending_agreements', 0),
                'activeAgreements': stats.get('total_agreements', 0) - stats.get('pending_agreements', 0),
                'total_properties': stats.get('total_properties', 0),
                'verified_properties': stats.get('verified_properties', 0),
                'pending_properties': stats.get('pending_properties', 0),
                'active_listings': stats.get('active_listings', 0),
            }
        elif user.role == 'property_seeker':
            dashboard_stats = {
                'agreements': stats.get('total_agreements', 0),
                'pendingAgreements': stats.get('pending_agreements', 0),
                'activeAgreements': stats.get('active_agreements', 0),
                'propertiesViewed': 0,  # This would need to be tracked separately
            }
        elif user.role == 'land_rep':
            dashboard_stats = {
                'properties': Property.objects.count(),
                'pendingProperties': stats.get('pending_verifications', 0),
                'verifiedProperties': Property.objects.filter(userproperty__is_verified=True).count(),
                'rejectedProperties': Property.objects.filter(userproperty__verification_status='rejected').count(),
            }
        elif user.role == 'admin' or user.role == 'sys_admin':
            dashboard_stats = {
                'properties': stats.get('total_properties', 0),
                'agreements': stats.get('total_agreements', 0) if 'total_agreements' in stats else 0,
                'pendingVerifications': stats.get('pending_verifications', 0),
                'pendingProperties': UserProperty.objects.filter(verification_status='pending').count(),
            }
        else:
            dashboard_stats = {}
            
        return Response(dashboard_stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Dashboard stats error: {str(e)}")
        return Response(
            {'error': 'Failed to fetch dashboard stats', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_properties(request):
    """Get all properties owned by the authenticated user"""
    try:
        user = request.user
        print(f"get_user_properties called by user: {user.email}, role: {user.role}")
        
        # Check if user is a property owner
        if user.role != 'property_owner':
            print(f"User {user.email} is not a property owner, role: {user.role}")
            return JsonResponse({'error': 'Only property owners can view their properties'}, status=403)
        
        properties = []
        
        with connection.cursor() as cursor:
            # Get all properties owned by the user
            cursor.execute("""
                SELECT 
                    p.id,
                    p.title,
                    p.property_type,
                    p.description,
                    p.location,
                    p.status,
                    p.created_at,
                    up.id as user_property_id,
                    up.is_verified,
                    up.verification_status,
                    up.last_verified_at
                FROM 
                    core_property p
                    JOIN core_userproperty up ON p.id = up.property_id
                WHERE 
                    up.owner_id = %s AND up.is_active = true
                ORDER BY
                    p.created_at DESC
            """, [user.id])
            
            property_rows = cursor.fetchall()
            print(f"Found {len(property_rows)} properties for user {user.email}")
            
            # If no properties found, return empty array
            if not property_rows:
                print(f"No properties found for user {user.email}")
                return JsonResponse([], safe=False)
            
            # Process each property and get its images
            for row in property_rows:
                property_id = row[0]
                user_property_id = row[7]
                
                # Get the first active image for this property
                cursor.execute("""
                    SELECT image
                    FROM core_propertyimage
                    WHERE property_id = %s AND is_active = true
                    ORDER BY uploaded_at DESC
                    LIMIT 1
                """, [property_id])
                
                image_result = cursor.fetchone()
                image_url = image_result[0] if image_result else None
                
                # Print image URL for debugging
                print(f"Property {property_id} raw image path: {image_url}")
                
                # Add media URL prefix if needed
                if image_url:
                    from django.conf import settings
                    # Check if MEDIA_URL needs to be prepended (if not already included)
                    if not image_url.startswith(('http://', 'https://', settings.MEDIA_URL)):
                        image_url = f"{settings.MEDIA_URL}{image_url}"
                        print(f"Property {property_id} adjusted image URL: {image_url}")
                
                # Get document count for this property
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM core_propertydocument
                    WHERE user_property_id = %s
                """, [user_property_id])
                
                document_count = cursor.fetchone()[0]
                
                # Build property object
                property_obj = {
                    "id": property_id,
                    "title": row[1],
                    "property_type": row[2],
                    "description": row[3],
                    "location": row[4],
                    "status": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "user_property_id": user_property_id,
                    "is_verified": row[8],
                    "verification_status": row[9],
                    "verification_date": row[10].isoformat() if row[10] else None,
                    "image_url": image_url,
                    "document_count": document_count
                }
                
                properties.append(property_obj)
        
        print(f"Returning {len(properties)} properties for user {user.email}")
        return JsonResponse(properties, safe=False)
    
    except Exception as e:
        print(f"Error in get_user_properties: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)