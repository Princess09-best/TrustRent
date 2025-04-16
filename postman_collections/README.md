# TrustRent API Test Suite

This directory contains Postman collections for testing the TrustRent API endpoints. The test suite covers user registration, login, property management, listing, and detail endpoints.

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)
- Newman CLI (`npm install -g newman`)
- Django development server running on `http://localhost:8000`

## Test Collections

1. **User Registration Tests** (`user_registration_tests.json`)
   - Tests user registration with valid and invalid data
   - Covers required fields, email format, password strength, etc.

2. **User Login Tests** (`user_login_tests.json`)
   - Tests user login with valid and invalid credentials
   - Covers successful login, invalid email/password, etc.

3. **Property Management Tests** (`property_management_tests.json`)
   - Tests property creation, document upload, image upload, and verification
   - Covers successful operations and error cases

4. **Property Listing Tests** (`property_listing_tests.json`)
   - Tests listing creation, update, retrieval, and deactivation
   - Covers successful operations and error cases

5. **Property Detail Tests** (`property_detail_tests.json`)
   - Tests property detail retrieval
   - Covers successful retrieval and various error scenarios

## Setup

1. Install dependencies:
   ```bash
   npm install -g newman
   ```

2. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

3. Verify the server is running at `http://localhost:8000`

## Running Tests

### Using the Test Runner

The test runner script (`test_runner.js`) executes all collections in sequence:

```bash
node postman_collections/test_runner.js
```

### Running Individual Collections

To run a specific collection:

```bash
npx newman run postman_collections/<collection_name>.json --env-var "base_url=http://localhost:8000"
```

## Test Data

The test suite uses the following environment variables:

- `base_url`: Base URL for the API (default: `http://localhost:8000`)
- `auth_token`: JWT token for authenticated requests
- `property_id`: ID of a test property
- `listing_id`: ID of a test listing
- `unverified_property_id`: ID of an unverified property
- `inactive_property_id`: ID of an inactive property
- `unavailable_property_id`: ID of an unavailable property
- `inactive_listing_property_id`: ID of a property with inactive listings

## Test Results

The test runner provides detailed output for each collection, including:

- Request and response details
- Test assertions and results
- Error messages and stack traces
- Summary statistics

## Troubleshooting

1. **404 Errors**
   - Verify the Django server is running
   - Check the base URL configuration
   - Verify the API endpoints are correctly defined

2. **Authentication Errors**
   - Verify the auth token is valid
   - Check token expiration
   - Ensure proper token format

3. **Test Failures**
   - Check the test assertions
   - Verify the expected response format
   - Review the error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add or modify test cases
4. Update the documentation
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 