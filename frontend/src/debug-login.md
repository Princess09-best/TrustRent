# Debugging the Login Flow

## Current Issues
- Login API appears to work (returns a token) but redirection isn't happening
- The user profile API endpoint may not be properly configured

## Steps to Debug

### 1. Verify Token Storage
After login, check if the token is being stored correctly:
1. Log in with valid credentials
2. Open browser dev tools (F12)
3. Go to Application tab > Local Storage
4. Check if `token` exists with a valid JWT value

### 2. Check Network Requests
Watch the network requests in dev tools:
1. Log in with valid credentials
2. In dev tools, go to Network tab
3. Filter by "Fetch/XHR"
4. Look for:
   - `/api/user/login/` - Should return 200 with token
   - `/api/users/profile/` - Should return user data

### 3. Using Development Mode

Development mode is enabled (`isDevelopment = true` in App.js), which means:
- The app will create a mock user based on the role selector
- You can see all parts of the application without real authentication
- The red bar at the top indicates you're in development mode

### 4. Backend API Endpoints

Based on server logs, these endpoints are working:
- ✅ `/api/user/login/` - Returns JWT token
- ✅ `/api/user/register/` - Creates new user

But these endpoints may not exist:
- ❌ `/api/users/profile/` - User profile endpoint not found

### 5. Quick Fix for Testing

1. Use development mode (already enabled)
2. If you need to test with real authentication:
   - Make sure your backend has a `/api/users/profile/` endpoint
   - Check the JWT token format in localStorage

## Console Commands for Debugging

Add these to your browser console to debug login issues:

```javascript
// Check if token exists
console.log("Token:", localStorage.getItem('token'));

// Try a manual API request
fetch('/api/users/profile/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})
.then(response => {
  console.log("Status:", response.status);
  return response.text();
})
.then(text => console.log("Response:", text))
.catch(err => console.error("Error:", err));
``` 