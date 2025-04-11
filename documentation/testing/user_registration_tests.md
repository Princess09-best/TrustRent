# User Registration Testing Documentation

## 1. Overview
The user registration functionality allows new users to create accounts with the following roles:
- Property Owner
- Renter

Note: Land Commission Representative role is restricted and can only be assigned by an administrator.

### 1.1 Implementation Details
```python
# Key validation rules implemented in core/views.py:
- Email format validation using Django's validate_email
- Phone number validation (Ghana format: +233XXXXXXXXX)
- Password strength (minimum 8 characters)
- Role validation (property_owner, renter)
- ID type validation (Ghana Card, Passport)
- ID value format validation based on type
```

## 2. Test Cases

### 2.1 Unit Tests
Location: `core/tests.py`
```python
class UserRegistrationTests(TestCase):
    # Test cases covering all validation scenarios
    # Database isolation ensures clean state for each test
```

### 2.2 API Tests (Postman)

#### 2.2.1 Valid Registration
- **Test Case**: Register user with valid data
- **Request**:
```json
{
    "firstname": "John",
    "lastname": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "password": "securepassword123",
    "role": "property_owner",
    "id_type": "Ghana Card",
    "id_value": "GHA-123456789-0"
}
```
- **Expected Response**: 201 Created
- **Actual Response**: 201 Created
- **Result**: ✅ PASS

#### 2.2.2 Email Validation
- **Test Case**: Register with invalid email format
- **Request**:
```json
{
    "email": "invalid-email",
    // ... other valid fields
}
```
- **Expected Response**: 400 Bad Request
- **Expected Message**: "Invalid email format"
- **Actual Response**: 400 Bad Request
- **Actual Message**: "Invalid email format"
- **Result**: ✅ PASS

#### 2.2.3 Phone Number Validation
- **Test Case**: Register with invalid phone number
- **Request**:
```json
{
    "email": "test.phone@example.com",
    "phone_number": "123",
    // ... other valid fields
}
```
- **Expected Response**: 400 Bad Request
- **Expected Message**: "Invalid phone number format. Use format: +233XXXXXXXXX"
- **Actual Response**: 400 Bad Request
- **Actual Message**: "Invalid phone number format. Use format: +233XXXXXXXXX"
- **Result**: ✅ PASS

#### 2.2.4 Password Validation
- **Test Case**: Register with invalid password
- **Request**:
```json
{
    "firstname": "John",
    "lastname": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "password": "123",
    "role": "property_owner",
    "id_type": "Ghana Card",
    "id_value": "GHA-123456789-0"
}
```
- **Expected Response**: 400 Bad Request
- **Expected Message**: "Password must be at least 8 characters"
- **Actual Response**: 400 Bad Request
- **Actual Message**: "Password must be at least 8 characters"
- **Result**: ✅ PASS

#### 2.2.5 ID Type Validation
- **Test Case**: Register with invalid ID type
- **Request**:
```json
{
    "firstname": "John",
    "lastname": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "password": "securepassword123",
    "role": "property_owner",
    "id_type": "invalid_type",
    "id_value": "GHA-123456789-0"
}
```
- **Expected Response**: 400 Bad Request
- **Expected Message**: "Invalid ID type. Must be one of: Ghana Card, Passport"
- **Actual Response**: 400 Bad Request
- **Actual Message**: "Invalid ID type. Must be one of: Ghana Card, Passport"
- **Result**: ✅ PASS

#### 2.2.6 ID Value Format Validation
- **Test Case**: Register with invalid ID value format
- **Request**:
```json
{
    "firstname": "John",
    "lastname": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+233123456789",
    "password": "securepassword123",
    "role": "property_owner",
    "id_type": "Ghana Card",
    "id_value": "invalid-format"
}
```
- **Expected Response**: 400 Bad Request
- **Expected Message**: "Invalid ID value format"
- **Actual Response**: 400 Bad Request
- **Actual Message**: "Invalid ID value format"
- **Result**: ✅ PASS

#### 2.2.7 Role Validation
- **Test Case**: Register with invalid role
- **Request**:
```json
{
    "firstname": "John",
    "lastname": "Doe",
    "email": "role.test@example.com",
    "phone_number": "+233123456789",
    "password": "securepassword123",
    "role": "invalid_role",
    "id_type": "Ghana Card",
    "id_value": "GHA-123456789-0"
}
```
- **Expected Response**: 400 Bad Request
- **Expected Message**: "Invalid role. Must be one of: property_owner, renter"
- **Actual Response**: 400 Bad Request
- **Actual Message**: "Invalid role. Must be one of: property_owner, renter"
- **Result**: ✅ PASS

[Additional test cases to be documented as executed...]

## 3. Test Results Summary

### 3.1 Unit Test Results
```bash
python manage.py test core.tests.UserRegistrationTests -v 2
```
- Total Tests: 8
- Passed: 8
- Failed: 0

### 3.2 API Test Results
- Total Test Cases: 8
- Passed: 8
- Failed: 0

## 4. Issues and Resolutions

### 4.1 Known Issues
1. **Issue**: Email uniqueness causing false negatives in test cases
   - **Resolution**: Use unique email addresses for each test case
   - **Implementation**: Updated Postman collection with unique emails

### 4.2 Improvements Made
1. Added proper validation for Ghana Card and Passport formats
2. Implemented comprehensive error messages
3. Added CORS headers for OPTIONS requests

## 5. Test Data

### 5.1 Valid Test Data
```json
{
    "firstname": "Test",
    "lastname": "User",
    "email": "test.user@example.com",
    "phone_number": "+233123456789",
    "password": "securepassword123",
    "role": "property_owner",
    "id_type": "Ghana Card",
    "id_value": "GHA-123456789-0"
}
```

### 5.2 Test Scenarios Matrix
| Field | Valid Input | Invalid Input | Error Message |
|-------|------------|---------------|---------------|
| email | user@example.com | invalid-email | Invalid email format |
| phone_number | +233123456789 | 123 | Invalid phone number format |
| password | securepassword123 | 123 | Password must be at least 8 characters |
| role | property_owner, renter | invalid_role | Invalid role. Must be one of: property_owner, renter |
| id_value (Ghana Card) | GHA-123456789-0 | 123 | Invalid Ghana Card format | 