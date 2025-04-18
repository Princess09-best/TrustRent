from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connections
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json

from .models import PropertyListing

@csrf_exempt
@require_http_methods(["POST"])
def create_property_listing(request):
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
            
            property_id_check, property_title = result

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
@require_http_methods(["GET"])
def get_properties(request):
    """Get a list of verified properties with optional filters"""
    try:
        # Get filter parameters
        location = request.GET.get('location')
        property_type = request.GET.get('type')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        listing_type = request.GET.get('listing_type')  # rent or sale
        search = request.GET.get('search')  # search in title and description
        sort_by = request.GET.get('sort_by', 'created_at')  # default sort by creation date
        sort_order = request.GET.get('sort_order', 'desc')  # default descending order
        page = int(request.GET.get('page', 1))  # default page 1
        per_page = int(request.GET.get('per_page', 10))  # default 10 items per page
        
        # Base query with all required visibility rules
        query = """
            SELECT 
                p.id, p.title, p.property_type, p.description, 
                p.location, p.status, p.created_at,
                u.firstname, u.lastname, u.email, u.phone_number,
                pl.id as listing_id, pl.listing_type, pl.price, pl.is_active as listing_status,
                pl.created_at as listing_created_at,
                pi.image as property_image
            FROM core_property p
            JOIN core_userproperty up ON p.id = up.property_id
            JOIN core_user u ON up.owner_id = u.id
            JOIN ops_propertylisting pl ON up.id = pl.user_property_id
            LEFT JOIN core_propertyimage pi ON p.id = pi.property_id AND pi.is_active = true
            WHERE 
                up.is_verified = true 
                AND up.is_active = true
                AND p.status = 'available'
                AND pl.is_active = true
        """
        params = []
        
        # Add filters
        if location:
            query += " AND LOWER(p.location) LIKE LOWER(%s)"
            params.append(f"%{location}%")
        if property_type:
            query += " AND p.property_type = %s"
            params.append(property_type)
        if min_price:
            query += " AND pl.price >= %s"
            params.append(float(min_price))
        if max_price:
            query += " AND pl.price <= %s"
            params.append(float(max_price))
        if listing_type:
            query += " AND pl.listing_type = %s"
            params.append(listing_type)
        if search:
            query += " AND (LOWER(p.title) LIKE LOWER(%s) OR LOWER(p.description) LIKE LOWER(%s))"
            params.extend([f"%{search}%", f"%{search}%"])
            
        # Add sorting
        valid_sort_fields = ['price', 'created_at', 'listing_created_at']
        if sort_by in valid_sort_fields:
            query += f" ORDER BY {sort_by} {sort_order.upper()}"
            
        # Add pagination
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
            
        # Execute query
        with connections['core'].cursor() as cursor:
            # Get total count for pagination
            count_query = query.replace("SELECT p.id, p.title", "SELECT COUNT(*)")
            count_query = count_query.split("ORDER BY")[0]  # Remove ORDER BY clause
            cursor.execute(count_query, params[:-2])  # Exclude LIMIT and OFFSET params
            total_count = cursor.fetchone()[0]
            
            # Get paginated results
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            properties = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Get all images for each property
            for property in properties:
                cursor.execute("""
                    SELECT image, uploaded_at
                    FROM core_propertyimage
                    WHERE property_id = %s AND is_active = true
                    ORDER BY uploaded_at DESC
                """, [property['id']])
                property['images'] = [dict(zip(['image', 'uploaded_at'], row)) 
                                    for row in cursor.fetchall()]
            
        return JsonResponse({
            'properties': properties,
            'pagination': {
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        }, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
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
@require_http_methods(["GET", "PATCH"])
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
@require_http_methods(["GET"])
def get_all_listings(request):
    """Get all active property listings with optional filters"""
    try:
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
@require_http_methods(["POST"])
def reactivate_property_listing(request, listing_id):
    """Reactivate a deactivated property listing"""
    try:
        data = json.loads(request.body)
        reactivation_reason = data.get('reactivation_reason')

        if not reactivation_reason:
            return JsonResponse({'error': 'Reactivation reason is required'}, status=400)

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

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)