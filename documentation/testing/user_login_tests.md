# User Login Testing Documentation

## 1. Overview
The login functionality authenticates users and provides appropriate access based on their role and verification status. The system implements several security measures including password hashing and verification status checks.

### 1.1 Implementation Details
```python
# Key validation rules implemented in core/views.py:
- Email existence validation
- Password verification using Django's check_password
- Verification status check
- Last login timestamp update
- Legacy password hash handling
```

## 2. Test Cases

### 2.1 Unit Tests
Location: `core/tests.py`
```python
class UserLoginTests(TestCase):
    # Test cases covering all authentication scenarios
    # Database isolation ensures clean state for each test
```

### 2.2 API Tests (Postman)

#### 2.2.1 Valid Login (Verified User)
- **Test Case**: Login with valid credentials for a verified user
- **Request**:
```json
{
    "email": "valid.user@example.com",
    "password": "securepassword123"
}
```
- **Expected Response**: 200 OK
- **Expected Data**: 
```json
{
    "message": "Login successful",
    "user_id": "<user_id>",
    "role": "property_owner",
    "is_verified": true
}
```

#### 2.2.2 Unverified User Login
- **Test Case**: Login with valid credentials but unverified account
- **Request**:
```json
{
    "email": "unverified.user@example.com",
    "password": "securepassword123"
}
```
- **Expected Response**: 403 Forbidden
- **Expected Message**: "Account pending verification. Please wait for verification email."

#### 2.2.3 Invalid Email
- **Test Case**: Login with non-existent email
- **Request**:
```json
{
    "email": "nonexistent@example.com",
    "password": "securepassword123"
}
```
- **Expected Response**: 401 Unauthorized
- **Expected Message**: "Invalid email or password"

#### 2.2.4 Invalid Password
- **Test Case**: Login with incorrect password
- **Request**:
```json
{
    "email": "valid.user@example.com",
    "password": "wrongpassword123"
}
```
- **Expected Response**: 401 Unauthorized
- **Expected Message**: "Invalid email or password"

#### 2.2.5 Missing Required Fields
- **Test Case**: Login with missing email or password
- **Request**:
```json
{
    "email": "valid.user@example.com"
}
```
- **Expected Response**: 400 Bad Request
- **Expected Message**: "Email and password required"

## 3. Test Results Summary

### 3.1 Unit Test Results
```bash
python manage.py test core.tests.UserLoginTests -v 2
```
- Total Tests: 5
- Passed: 5
- Failed: 0

### 3.2 API Test Results
- Total Test Cases: 5
- Passed: 5
- Failed: 0

## 4. Security Considerations

### 4.1 Password Security
1. Passwords are hashed using Django's PBKDF2 algorithm
2. Legacy password migration handled automatically
3. No plain text passwords stored or transmitted

### 4.2 Authentication Flow
1. Check email existence
2. Verify password hash
3. Check account verification status
4. Update last login timestamp
5. Return appropriate role and permissions

## 5. Test Data

### 5.1 Test Users
| Email | Password | Role | Status |
|-------|----------|------|--------|
| valid.user@example.com | securepassword123 | property_owner | Verified |
| unverified.user@example.com | securepassword123 | renter | Unverified |

### 5.2 Test Scenarios Matrix
| Scenario | Email | Password | Expected Status | Message |
|----------|-------|----------|-----------------|---------|
| Valid Login | valid.user@example.com | securepassword123 | 200 | Login successful |
| Unverified | unverified.user@example.com | securepassword123 | 403 | Account pending verification |
| Wrong Email | wrong@example.com | securepassword123 | 401 | Invalid email or password |
| Wrong Password | valid.user@example.com | wrongpass | 401 | Invalid email or password |
| Missing Field | valid.user@example.com | - | 400 | Email and password required | 