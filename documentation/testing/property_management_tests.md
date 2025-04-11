# Property Management Tests

## Test Environment Setup
- Test database: test_trustrent_core_db
- Test user credentials:
  - Land Commission Representative:
    - Email: lc.rep@landcomm.go.ke
    - Password: securepass123
  - Regular User:
    - Email: john.doe@example.com
    - Password: userpass123

## Test Cases

### 1. Property Creation
#### Test: Successful Property Creation
- **Method**: POST
- **Endpoint**: /api/property/create/
- **Request Body**:
```json
{
    "title": "Test Property",
    "description": "A test property listing",
    "location": "Test Location",
    "property_type": "LAND",
    "price": 1000000
}
```
- **Expected Response**: 201 Created
- **Expected Data**: Property ID and success message

#### Test: Missing Required Fields
- **Method**: POST
- **Endpoint**: /api/property/create/
- **Request Body**: Missing title/location
- **Expected Response**: 400 Bad Request
- **Expected Data**: Error message indicating missing fields

### 2. Document Upload
#### Test: Valid Document Upload
- **Method**: POST
- **Endpoint**: /api/property/upload-document/
- **Request Body**: Multipart form with PDF file
- **Expected Response**: 201 Created
- **Expected Data**: Document ID and success message

#### Test: Invalid Document Type
- **Method**: POST
- **Endpoint**: /api/property/upload-document/
- **Request Body**: Multipart form with TXT file
- **Expected Response**: 400 Bad Request
- **Expected Data**: Error message about invalid document type

### 3. Unverified Properties List
#### Test: Land Commission Rep Access
- **Method**: GET
- **Endpoint**: /api/property/unverified/
- **Headers**: Authentication token for LC Rep
- **Expected Response**: 200 OK
- **Expected Data**: List of unverified properties

#### Test: Regular User Access
- **Method**: GET
- **Endpoint**: /api/property/unverified/
- **Headers**: Authentication token for regular user
- **Expected Response**: 403 Forbidden
- **Expected Data**: Error message about insufficient permissions

### 4. Property Verification
#### Test: Successful Verification
- **Method**: POST
- **Endpoint**: /api/property/verify/
- **Headers**: Authentication token for LC Rep
- **Request Body**:
```json
{
    "property_id": "test_property_id"
}
```
- **Expected Response**: 200 OK
- **Expected Data**: Success message

#### Test: Unauthorized Verification
- **Method**: POST
- **Endpoint**: /api/property/verify/
- **Headers**: Authentication token for regular user
- **Expected Response**: 403 Forbidden
- **Expected Data**: Error message about insufficient permissions

### 5. Property Rejection
#### Test: Successful Rejection
- **Method**: POST
- **Endpoint**: /api/property/reject/
- **Headers**: Authentication token for LC Rep
- **Request Body**:
```json
{
    "property_id": "test_property_id",
    "rejection_reason": "Invalid documentation"
}
```
- **Expected Response**: 200 OK
- **Expected Data**: Success message

#### Test: Missing Rejection Reason
- **Method**: POST
- **Endpoint**: /api/property/reject/
- **Headers**: Authentication token for LC Rep
- **Request Body**: Missing rejection_reason
- **Expected Response**: 400 Bad Request
- **Expected Data**: Error message about missing reason

## Running the Tests
```bash
python manage.py test core.tests.PropertyManagementTests -v 2
```

## Test Data Cleanup
- All test data is automatically cleaned up after test execution
- Test database is destroyed after completion 