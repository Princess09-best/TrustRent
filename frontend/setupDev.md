# TrustRent Development Setup

## Running the Application

### Backend Setup
1. Make sure your PostgreSQL database is running
2. Navigate to the root directory (where manage.py is located)
3. Activate your virtual environment:
   ```
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```
4. Run the Django server:
   ```
   python manage.py runserver
   ```
   The server will start at http://127.0.0.1:8000

### Frontend Setup
1. Navigate to the frontend directory
2. Install dependencies (if not already done):
   ```
   npm install
   ```
3. Start the React development server:
   ```
   npm start
   ```
   The frontend will be available at http://localhost:3000

## Development Mode

To bypass authentication during development:
1. In `App.js`, set `isDevelopment = true`
2. Use the role selector at the top of the page to change user roles
3. This lets you preview any page without needing to log in

## API Endpoints

The frontend is configured to proxy API requests to the Django backend. Use relative paths for API calls:

```javascript
// Correct
const response = await axios.post('/api/user/login/', data);

// Incorrect - don't use absolute URLs
const response = await axios.post('http://127.0.0.1:8000/api/user/login/', data);
```

## Common Issues

1. **Authentication Errors**: Make sure token is stored correctly in localStorage
2. **CORS Issues**: Ensure Django CORS settings allow requests from localhost:3000
3. **Proxy Not Working**: Restart the React development server after changing package.json

## User Flows

1. **Registration**: New users register and await verification (if needed)
2. **Login**: Users login and are directed to the role-specific dashboard
3. **Dashboard**: Shows role-specific actions and statistics
4. **Role-Based Access**: Different user roles have access to different features:
   - Admin: Verify users, create admin accounts
   - Land Representative: Manage and verify properties
   - Property Owner: Create properties, manage rental agreements
   - Property Seeker: View and apply for properties, manage agreements 