# API Architecture

## RESTful API Design Principles

TrustRent's API architecture follows REST principles, emphasizing stateless client-server communication, resource-based endpoints, and standard HTTP methods. The API is designed to be intuitive, consistent, and self-documenting, making it easy for frontend clients to interact with the backend services.

### Resource Hierarchy

The API follows a logical hierarchy that reflects the business domain:

1. **User Resources**
   ```
   GET    /api/users/                  # List users
   POST   /api/users/                  # Create user
   GET    /api/users/{id}/            # Get user details
   PUT    /api/users/{id}/            # Update user
   GET    /api/users/{id}/properties/  # List user's properties
   GET    /api/users/{id}/documents/   # List user's documents
   ```

2. **Property Resources**
   ```
   GET    /api/properties/                    # List properties
   POST   /api/properties/                    # Create property
   GET    /api/properties/{id}/              # Get property details
   PUT    /api/properties/{id}/              # Update property
   GET    /api/properties/{id}/documents/     # Get property documents
   POST   /api/properties/{id}/verify/        # Verify property
   GET    /api/properties/{id}/transactions/  # Property transaction history
   ```

3. **Listing Resources**
   ```
   GET    /api/listings/                # List all listings
   POST   /api/listings/                # Create listing
   GET    /api/listings/{id}/          # Get listing details
   PUT    /api/listings/{id}/          # Update listing
   POST   /api/listings/{id}/review/    # Submit listing review
   GET    /api/listings/search/         # Search listings
   ```

4. **Transaction Resources**
   ```
   GET    /api/transactions/                  # List transactions
   POST   /api/transactions/                  # Create transaction
   GET    /api/transactions/{id}/            # Get transaction details
   GET    /api/transactions/{id}/status/      # Check transaction status
   POST   /api/transactions/{id}/verify/      # Verify transaction
   ```

### Request/Response Patterns

1. **Standard Response Format**
   ```json
   {
     "status": "success",
     "code": 200,
     "data": {
       "resource": {
         "id": "123",
         "type": "property",
         "attributes": {
           "title": "Modern Apartment",
           "location": "City Center",
           "price": 250000
         }
       },
       "metadata": {
         "created_at": "2024-01-20T10:00:00Z",
         "updated_at": "2024-01-20T10:00:00Z"
       }
     },
     "message": "Operation successful",
     "links": {
       "self": "/api/properties/123",
       "documents": "/api/properties/123/documents",
       "transactions": "/api/properties/123/transactions"
     }
   }
   ```

2. **Error Response Format**
   ```json
   {
     "status": "error",
     "code": 400,
     "message": "Validation failed",
     "errors": [
       {
         "field": "price",
         "code": "invalid_amount",
         "message": "Price must be greater than zero"
       }
     ]
   }
   ```

### Authentication Flow

1. **Login Process**
   ```
   POST /api/auth/login
   {
     "email": "user@example.com",
     "password": "secure_password"
   }

   Response:
   {
     "access_token": "eyJ0eXAi...",
     "refresh_token": "eyJ0eXAi...",
     "expires_in": 3600
   }
   ```

2. **Token Refresh**
   ```
   POST /api/auth/refresh
   {
     "refresh_token": "eyJ0eXAi..."
   }

   Response:
   {
     "access_token": "eyJ0eXAi...",
     "expires_in": 3600
   }
   ```

### Query Parameters

1. **Filtering**
   ```
   GET /api/properties?type=apartment&price_min=100000&price_max=300000
   GET /api/listings?status=active&location=city_center
   ```

2. **Pagination**
   ```
   GET /api/properties?page=2&per_page=20
   
   Response:
   {
     "data": [...],
     "pagination": {
       "current_page": 2,
       "per_page": 20,
       "total_pages": 5,
       "total_items": 98
     }
   }
   ```

3. **Sorting**
   ```
   GET /api/properties?sort=price:desc,created_at:desc
   GET /api/listings?sort=views:desc
   ```

### API Versioning

Version control is implemented in the URL path:

```
/api/v1/properties/
/api/v2/properties/
```

Changes between versions are documented in the API changelog, with clear migration guides for clients.

### Security Implementation

1. **Authentication Header**
   ```
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   ```

2. **Rate Limiting**
   ```
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 95
   X-RateLimit-Reset: 1640995200
   ```

3. **CORS Headers**
   ```
   Access-Control-Allow-Origin: *
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE
   Access-Control-Allow-Headers: Content-Type, Authorization
   ```

### Blockchain Integration Endpoints

1. **Property Verification**
   ```
   POST /api/blockchain/verify-property
   {
     "property_id": "123",
     "document_hash": "0x123..."
   }
   ```

2. **Transaction Recording**
   ```
   POST /api/blockchain/record-transaction
   {
     "property_id": "123",
     "buyer_id": "456",
     "transaction_details": {...}
   }
   ```

This API architecture provides a robust, secure, and scalable interface for client applications while maintaining clear documentation and consistent patterns throughout the system. 