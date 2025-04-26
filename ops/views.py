from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connections
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from core.permissions import UserPermission
from ops.permissions import has_property_permission
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json

from .models import PropertyListing

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_property_permission(UserPermission.CREATE_PROPERTY_LISTING)
def create_property_listing(request):
    print("\n=== Property Listing Creation Debug ===")
    print(f"User: {request.user}")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User role: {request.user.role}")
    print(f"Request method: {request.method}")
    print(f"Authorization header: {request.headers.get('Authorization')}")

    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        data = json.loads(request.body)
        user_property_id = data.get('user_property_id')
        listing_type = data.get('listing_type')
        price = data.get('price')

        if not user_property_id or not listing_type or price is None:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            price = float(price)  # Validate price is a valid number
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid price value'}, status=400)

        # Lookup property_id from user_property_id
        with connections['core'].cursor() as cursor:
            cursor.execute("SELECT property_id FROM core_userproperty WHERE id = %s", [user_property_id])
            property_id_result = cursor.fetchone()
            property_id = property_id_result[0] if property_id_result else None

        # Verify property exists and is verified
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title 
                FROM core_property p
                JOIN core_userproperty up ON p.id = up.property_id
                WHERE up.id = %s AND up.is_verified = true AND up.is_active = true
            """, [user_property_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'Property not found or not verified'}, status=404)
            
            # Just using the title is enough since we've already verified the property exists
            property_title = result[1]

        # Check for existing active listing
        with connections['ops'].cursor() as cursor:
            cursor.execute("""
                SELECT id 
                FROM ops_propertylisting 
                WHERE user_property_id = %s AND is_active = true
            """, [user_property_id])
            
            if cursor.fetchone():
                return JsonResponse({'error': 'An active listing already exists for this property'}, status=400)

        # Create new listing
        with connections['ops'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO ops_propertylisting 
                (user_property_id, listing_type, price, is_active, created_at) 
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, [user_property_id, listing_type, price, True, timezone.now()])
            
            listing_id = cursor.fetchone()[0]

        # Update property status to 'available'
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                UPDATE core_property 
                SET status = 'available'
                WHERE id = %s
            """, [property_id])

        # Create response with clean body and listing_id in header
        response = JsonResponse({
            'message': 'Property listing created successfully',
            'property_title': property_title,
            'listing_type': listing_type,
            'price': price
        }, status=201)
        
        # Add listing_id to response header
        response['X-Listing-Id'] = str(listing_id)
        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_property_permission(UserPermission.VIEW_ALL_LISTINGS)
def get_properties(request):
    """Get a list of verified properties with optional filters"""
    try:
        # Check if user is a property seeker
        if request.user.role != 'property_seeker':
            return JsonResponse({'error': 'Only property seekers can view properties'}, status=403)

        # Get filter parameters
        location = request.GET.get('location')
        property_type = request.GET.get('type')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        listing_type = request.GET.get('listing_type')
        search = request.GET.get('search')
        sort_by = request.GET.get('sort_by', 'created_at')
        sort_order = request.GET.get('sort_order', 'desc')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))

        # First, get verified properties from core database
        with connections['core'].cursor() as cursor:
            property_query = """
                SELECT 
                    p.id as property_id,
                    p.title,
                    p.property_type,
                    p.description,
                    p.location,
                    p.status,
                    up.id as user_property_id,
                    u.firstname,
                    u.lastname,
                    u.email,
                    u.phone_number
                FROM core_property p
                JOIN core_userproperty up ON p.id = up.property_id
                JOIN core_user u ON up.owner_id = u.id
                WHERE up.is_verified = true 
                AND up.is_active = true
                AND p.status = 'available'
            """
            params = []

            if location:
                property_query += " AND LOWER(p.location) LIKE LOWER(%s)"
                params.append(f"%{location}%")
            if property_type:
                property_query += " AND p.property_type = %s"
                params.append(property_type)
            if search:
                property_query += " AND (LOWER(p.title) LIKE LOWER(%s) OR LOWER(p.description) LIKE LOWER(%s))"
                params.extend([f"%{search}%", f"%{search}%"])

            cursor.execute(property_query, params)
            properties = [dict(zip([col[0] for col in cursor.description], row)) 
                         for row in cursor.fetchall()]

            # Get images for properties
            for prop in properties:
                cursor.execute("""
                    SELECT image, uploaded_at
                    FROM core_propertyimage
                    WHERE property_id = %s AND is_active = true
                    ORDER BY uploaded_at DESC
                """, [prop['property_id']])
                prop['images'] = [dict(zip(['image', 'uploaded_at'], row)) 
                                for row in cursor.fetchall()]

        # Then, get listings from ops database
        with connections['ops'].cursor() as cursor:
            listing_query = """
                SELECT 
                    id,
                    user_property_id,
                    listing_type,
                    price,
                    is_active,
                    created_at
                FROM ops_propertylisting
                WHERE is_active = true
            """
            params = []

            if listing_type:
                listing_query += " AND listing_type = %s"
                params.append(listing_type)
            if min_price:
                listing_query += " AND price >= %s"
                params.append(float(min_price))
            if max_price:
                listing_query += " AND price <= %s"
                params.append(float(max_price))

            cursor.execute(listing_query, params)
            listings = [dict(zip([col[0] for col in cursor.description], row)) 
                       for row in cursor.fetchall()]

        # Join the data in Python
        listing_map = {str(l['user_property_id']): l for l in listings}
        combined_results = []
        
        for prop in properties:
            listing = listing_map.get(str(prop['user_property_id']))
            if listing:  # Only include properties that have active listings
                combined_results.append({
                    'id': listing['id'],
                    'price': float(listing['price']),
                    'listing_type': listing['listing_type'],
                    'created_at': listing['created_at'].isoformat() if listing['created_at'] else None,
                    'title': prop['title'],
                    'property_type': prop['property_type'],
                    'description': prop['description'],
                    'location': prop['location'],
                    'owner': {
                        'name': f"{prop['firstname']} {prop['lastname']}",
                        'email': prop['email'],
                        'phone': prop['phone_number']
                    },
                    'images': prop['images']
                })

        # Sort results
        if sort_by == 'price':
            combined_results.sort(key=lambda x: x['price'], 
                               reverse=(sort_order.lower() == 'desc'))
        elif sort_by == 'created_at':
            combined_results.sort(key=lambda x: x['created_at'], 
                               reverse=(sort_order.lower() == 'desc'))

        # Apply pagination
        total_count = len(combined_results)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = combined_results[start_idx:end_idx]

        return JsonResponse({
            'properties': paginated_results,
            'pagination': {
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@has_property_permission(UserPermission.UPDATE_PROPERTY_LISTING)
def update_property_listing(request, listing_id):
    """Get or update a property listing"""
    if request.method == "GET":
        try:
            # First get the listing details from ops database
            with connections['ops'].cursor() as cursor:
                cursor.execute("""
                    SELECT price, listing_type, user_property_id, is_active
                    FROM ops_propertylisting
                    WHERE id = %s AND is_active = true
                """, [listing_id])
                
                listing_result = cursor.fetchone()
                if not listing_result:
                    return JsonResponse({'error': 'Listing not found or not active'}, status=404)
                
                price, listing_type, user_property_id, is_active = listing_result

            # Then get the property details from core database
            with connections['core'].cursor() as cursor:
                cursor.execute("""
                    SELECT p.title, p.property_type, p.description, p.location
                    FROM core_property p
                    JOIN core_userproperty up ON up.property_id = p.id
                    WHERE up.id = %s
                """, [user_property_id])
                
                property_result = cursor.fetchone()
                if not property_result:
                    return JsonResponse({'error': 'Associated property not found'}, status=404)
                
                return JsonResponse({
                    'price': float(price),
                    'listing_type': listing_type,
                    'property': {
                        'title': property_result[0],
                        'type': property_result[1],
                        'description': property_result[2],
                        'location': property_result[3]
                    }
                })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == "PATCH":
        try:
            data = json.loads(request.body)
            
            # Check if listing exists and is active
            with connections['ops'].cursor() as cursor:
                cursor.execute("""
                    SELECT user_property_id 
                    FROM ops_propertylisting 
                    WHERE id = %s AND is_active = true
                """, [listing_id])
                
                result = cursor.fetchone()
                if not result:
                    return JsonResponse({'error': 'Active listing not found'}, status=404)

                # Update the price if provided
                if 'price' in data:
                    cursor.execute("""
                        UPDATE ops_propertylisting 
                        SET price = %s
                        WHERE id = %s
                        RETURNING price
                    """, [float(data['price']), listing_id])
                    
                    updated_data = cursor.fetchone()
                    if updated_data:
                        return JsonResponse({
                            'message': 'Listing updated successfully',
                            'price': float(updated_data[0])  # Convert Decimal to float
                        })
                    else:
                        return JsonResponse({'error': 'Failed to update listing'}, status=500)
                else:
                    return JsonResponse({'error': 'No valid fields to update'}, status=400)

        except ValueError as ve:
            return JsonResponse({'error': 'Invalid price value'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_property_permission(UserPermission.VIEW_ALL_LISTINGS)
def get_all_listings(request):
    """Get all active property listings with optional filters"""
    try:
        # Check if user is a property seeker
        if request.user.role != 'property_seeker':
            return JsonResponse({'error': 'Only property seekers can view all listings'}, status=403)

        # Get filter parameters
        location = request.GET.get('location')
        property_type = request.GET.get('type')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        listing_type = request.GET.get('listing_type')
        search = request.GET.get('search')
        sort_by = request.GET.get('sort_by', 'created_at')
        sort_order = request.GET.get('sort_order', 'desc')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))

        # First, get listings from ops database
        listings_query = """
            SELECT 
                pl.id, pl.user_property_id, pl.price, pl.listing_type, 
                pl.created_at, pl.is_active
            FROM ops_propertylisting pl
            WHERE pl.is_active = true
        """
        listings_params = []

        # Add price filters
        if min_price:
            listings_query += " AND pl.price >= %s"
            listings_params.append(float(min_price))
        if max_price:
            listings_query += " AND pl.price <= %s"
            listings_params.append(float(max_price))
        if listing_type:
            listings_query += " AND pl.listing_type = %s"
            listings_params.append(listing_type)

        # Add sorting
        valid_sort_fields = {
            'price': 'pl.price',
            'created_at': 'pl.created_at'
        }
        sort_field = valid_sort_fields.get(sort_by, 'pl.created_at')
        listings_query += f" ORDER BY {sort_field} {sort_order.upper()}"

        # Execute listings query
        with connections['ops'].cursor() as cursor:
            cursor.execute(listings_query, listings_params)
            listings = [
                {
                    'id': row[0],
                    'user_property_id': int(row[1]),  # Ensure this is an integer
                    'price': float(row[2]),
                    'listing_type': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'is_active': row[5]
                }
                for row in cursor.fetchall()
            ]

        if not listings:
            return JsonResponse({
                'listings': [],
                'pagination': {
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                },
                'filters': {
                    'location': location,
                    'property_type': property_type,
                    'price_range': {'min': min_price, 'max': max_price},
                    'listing_type': listing_type,
                    'search': search
                }
            })

        # Get property and user details from core database
        user_property_ids = [int(listing['user_property_id']) for listing in listings]  # Keep as integers
        property_query = """
            SELECT 
                up.id as user_property_id,
                p.title, p.property_type, p.description, p.location,
                u.firstname, u.lastname, u.phone_number,
                (SELECT image FROM core_propertyimage 
                 WHERE property_id = p.id AND is_active = true 
                 ORDER BY uploaded_at DESC LIMIT 1) as main_image
            FROM core_userproperty up
            JOIN core_property p ON up.property_id = p.id
            JOIN core_user u ON up.owner_id = u.id
            WHERE up.id = ANY(%s)
            AND up.is_verified = true
            AND up.is_active = true
        """

        # Add location and property type filters
        property_params = [user_property_ids]  # Pass the list directly
        if location:
            property_query += " AND LOWER(p.location) LIKE LOWER(%s)"
            property_params.append(f"%{location}%")
        if property_type:
            property_query += " AND p.property_type = %s"
            property_params.append(property_type)
        if search:
            property_query += " AND (LOWER(p.title) LIKE LOWER(%s) OR LOWER(p.description) LIKE LOWER(%s))"
            property_params.extend([f"%{search}%", f"%{search}%"])

        # Get property details
        property_details = {}
        with connections['core'].cursor() as cursor:
            cursor.execute(property_query, property_params)
            columns = ['user_property_id', 'title', 'property_type', 'description', 
                      'location', 'owner_firstname', 'owner_lastname', 
                      'owner_phone', 'main_image']
            for row in cursor.fetchall():
                details = dict(zip(columns, row))
                details['user_property_id'] = int(details['user_property_id'])  # Ensure this is an integer
                details['owner'] = {
                    'name': f"{details.pop('owner_firstname')} {details.pop('owner_lastname')}",
                    'phone': details.pop('owner_phone')
                }
                property_details[details['user_property_id']] = details  # Use integer as key

        # Combine the results
        combined_listings = []
        for listing in listings:
            user_property_id = listing['user_property_id']  # Already an integer
            if user_property_id in property_details:
                details = property_details[user_property_id]
                combined_listing = {
                    'id': listing['id'],
                    'price': listing['price'],
                    'listing_type': listing['listing_type'],
                    'created_at': listing['created_at'],
                    'title': details['title'],
                    'property_type': details['property_type'],
                    'description': details['description'],
                    'location': details['location'],
                    'owner': details['owner'],
                    'main_image': details['main_image']
                }
                combined_listings.append(combined_listing)

        # Apply pagination
        total_count = len(combined_listings)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_listings = combined_listings[start_idx:end_idx]

        return JsonResponse({
            'listings': paginated_listings,
            'pagination': {
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            },
            'filters': {
                'location': location,
                'property_type': property_type,
                'price_range': {
                    'min': min_price,
                    'max': max_price
                },
                'listing_type': listing_type,
                'search': search
            }
        })

    except ValueError as ve:
        return JsonResponse({'error': 'Invalid numeric parameter'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_property_permission(UserPermission.DEACTIVATE_PROPERTY_LISTING)
def deactivate_property_listing(request, listing_id):
    """Deactivate a property listing"""
    try:
        # Check if listing exists and is active
        with connections['ops'].cursor() as cursor:
            cursor.execute("""
                SELECT user_property_id 
                FROM ops_propertylisting 
                WHERE id = %s AND is_active = true
            """, [listing_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'Active listing not found'}, status=404)

            # Deactivate the listing
            cursor.execute("""
                UPDATE ops_propertylisting 
                SET is_active = false 
                WHERE id = %s
            """, [listing_id])

        return JsonResponse({
            'message': 'Property listing deactivated successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_property_permission(UserPermission.REACTIVATE_PROPERTY_LISTING)
def reactivate_property_listing(request, listing_id):
    """Reactivate a deactivated property listing"""
    try:
        # Check if listing exists and is inactive
        with connections['ops'].cursor() as cursor:
            cursor.execute("""
                SELECT user_property_id 
                FROM ops_propertylisting 
                WHERE id = %s AND is_active = false
            """, [listing_id])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'error': 'Inactive listing not found'}, status=404)

            # Check if there's already an active listing for this property
            user_property_id = result[0]
            cursor.execute("""
                SELECT id 
                FROM ops_propertylisting 
                WHERE user_property_id = %s AND is_active = true
            """, [user_property_id])
            
            if cursor.fetchone():
                return JsonResponse({
                    'error': 'Cannot reactivate: Another active listing exists for this property'
                }, status=400)

            # Reactivate the listing
            cursor.execute("""
                UPDATE ops_propertylisting 
                SET is_active = true 
                WHERE id = %s
                RETURNING id, price, listing_type
            """, [listing_id])

            listing_data = cursor.fetchone()
            if listing_data:
                return JsonResponse({
                    'message': 'Property listing reactivated successfully',
                    'is_active': True,
                    'listing_id': listing_data[0],
                    'price': float(listing_data[1]),
                    'listing_type': listing_data[2]
                })
            else:
                return JsonResponse({'error': 'Failed to reactivate listing'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_owner_listings(request):
    """Get all listings (active and inactive) for the authenticated property owner"""
    try:
        # Check if user is a property owner
        if request.user.role != 'property_owner':
            return JsonResponse({'error': 'Only property owners can view their listings'}, status=403)

        # Get filter parameters
        status = request.GET.get('status')  # 'active' or 'inactive'
        sort_by = request.GET.get('sort_by', 'created_at')
        sort_order = request.GET.get('sort_order', 'desc')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))

        # First, get user_property_ids from core database
        with connections['core'].cursor() as cursor:
            cursor.execute("""
                SELECT id 
                FROM core_userproperty 
                WHERE owner_id = %s
            """, [request.user.id])
            user_property_ids = [row[0] for row in cursor.fetchall()]

        if not user_property_ids:
            return JsonResponse({
                'listings': [],
                'pagination': {
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                }
            })

        # Then, get listings from ops database
        with connections['ops'].cursor() as cursor:
            listing_query = """
                SELECT 
                    id,
                    user_property_id,
                    price,
                    listing_type,
                    is_active,
                    created_at
                FROM ops_propertylisting
                WHERE user_property_id = ANY(%s)
            """
            params = [user_property_ids]

            # Add status filter if specified
            if status == 'active':
                listing_query += " AND is_active = true"
            elif status == 'inactive':
                listing_query += " AND is_active = false"

            # Add sorting
            valid_sort_fields = {
                'price': 'price',
                'created_at': 'created_at'
            }
            sort_field = valid_sort_fields.get(sort_by, 'created_at')
            listing_query += f" ORDER BY {sort_field} {sort_order.upper()}"

            # Get total count first
            count_query = listing_query.split("ORDER BY")[0]
            cursor.execute(count_query, params)
            total_count = len(cursor.fetchall())

            # Add pagination
            listing_query += " LIMIT %s OFFSET %s"
            offset = (page - 1) * per_page
            params.extend([per_page, offset])

            # Execute main query
            cursor.execute(listing_query, params)
            listings = [dict(zip([col[0] for col in cursor.description], row)) 
                       for row in cursor.fetchall()]

        # If no listings found, return empty response
        if not listings:
            return JsonResponse({
                'listings': [],
                'pagination': {
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                }
            })

        # Get property details from core database
        with connections['core'].cursor() as cursor:
            property_query = """
                SELECT 
                    up.id as user_property_id,
                    p.title,
                    p.property_type,
                    p.description,
                    p.location,
                    p.status as property_status,
                    p.id as property_id
                FROM core_userproperty up
                JOIN core_property p ON up.property_id = p.id
                JOIN core_user u ON up.owner_id = u.id
                WHERE up.id = ANY(%s)
            """
            cursor.execute(property_query, [user_property_ids])
            property_details = {
                str(row[0]): dict(zip(['user_property_id', 'title', 'property_type', 
                                     'description', 'location', 'property_status',
                                     'property_id'], row))
                for row in cursor.fetchall()
            }

            # Get images for each property
            for prop_details in property_details.values():
                cursor.execute("""
                    SELECT image, uploaded_at
                    FROM core_propertyimage
                    WHERE property_id = %s AND is_active = true
                    ORDER BY uploaded_at DESC
                """, [prop_details['property_id']])
                prop_details['images'] = [
                    dict(zip(['image', 'uploaded_at'], row))
                    for row in cursor.fetchall()
                ]

        # Combine the results
        combined_listings = []
        for listing in listings:
            user_property_id = str(listing['user_property_id'])
            if user_property_id in property_details:
                property_info = property_details[user_property_id]
                combined_listing = {
                    'id': listing['id'],
                    'price': float(listing['price']),
                    'listing_type': listing['listing_type'],
                    'is_active': listing['is_active'],
                    'created_at': listing['created_at'].isoformat() if listing['created_at'] else None,
                    'title': property_info['title'],
                    'property_type': property_info['property_type'],
                    'description': property_info['description'],
                    'location': property_info['location'],
                    'property_status': property_info['property_status'],
                    'images': property_info.get('images', [])
                }
                combined_listings.append(combined_listing)

        return JsonResponse({
            'listings': combined_listings,
            'pagination': {
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


