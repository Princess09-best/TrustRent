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

        if not user_property_id or not listing_type:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

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
            
            property_id, property_title = result

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
                (user_property_id, listing_type, is_active, created_at) 
                VALUES (%s, %s, %s, %s) RETURNING id
            """, [user_property_id, listing_type, True, timezone.now()])
            
            listing_id = cursor.fetchone()[0]

        return JsonResponse({
            'message': 'Property listing created successfully',
            'listing_id': listing_id,
            'property_title': property_title
        })

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
        
        # Base query
        query = """
            SELECT 
                p.id, p.title, p.property_type, p.description, 
                p.location, p.price, p.status, p.created_at,
                u.firstname, u.lastname, u.email, u.phone_number,
                pl.id as listing_id, pl.listing_type, pl.is_active as listing_status,
                pl.created_at as listing_created_at
            FROM core_property p
            JOIN core_userproperty up ON p.id = up.property_id
            JOIN core_user u ON up.owner_id = u.id
            LEFT JOIN ops_propertylisting pl ON up.id = pl.user_property_id
            WHERE up.is_verified = true AND up.is_active = true
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
            query += " AND p.price >= %s"
            params.append(float(min_price))
        if max_price:
            query += " AND p.price <= %s"
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
@require_http_methods(["GET"])
def get_property_detail(request, property_id):
    """Get detailed information about a specific property"""
    try:
        with connections['core'].cursor() as cursor:
            # Get property details
            cursor.execute("""
                SELECT 
                    p.id, p.title, p.property_type, p.description, 
                    p.location, p.price, p.status, p.created_at,
                    u.firstname, u.lastname, u.email, u.phone_number,
                    up.is_verified, up.verification_status,
                    pl.id as listing_id, pl.listing_type, pl.is_active as listing_status,
                    pl.created_at as listing_created_at,
                    pi.image as property_image
                FROM core_property p
                JOIN core_userproperty up ON p.id = up.property_id
                JOIN core_user u ON up.owner_id = u.id
                LEFT JOIN ops_propertylisting pl ON up.id = pl.user_property_id
                LEFT JOIN core_propertyimage pi ON p.id = pi.property_id AND pi.is_active = true
                WHERE p.id = %s AND up.is_active = true
            """, [property_id])
            
            columns = [col[0] for col in cursor.description]
            property_data = dict(zip(columns, cursor.fetchone()))
            
            if not property_data:
                return JsonResponse({'error': 'Property not found'}, status=404)
                
            # Get property documents
            cursor.execute("""
                SELECT id, document_type, file_path, created_at
                FROM core_propertydocument
                WHERE property_id = %s
            """, [property_id])
            
            documents = [dict(zip(['id', 'document_type', 'file_path', 'created_at'], row)) 
                        for row in cursor.fetchall()]
            
            # Get property images
            cursor.execute("""
                SELECT id, image, uploaded_at
                FROM core_propertyimage
                WHERE property_id = %s AND is_active = true
            """, [property_id])
            
            images = [dict(zip(['id', 'image', 'uploaded_at'], row)) 
                     for row in cursor.fetchall()]
            
            property_data['documents'] = documents
            property_data['images'] = images
            
            return JsonResponse(property_data)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)