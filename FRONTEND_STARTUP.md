# Starting and Testing the TrustRent Frontend

Follow these step-by-step instructions to start and test the TrustRent frontend application.

## Prerequisites

1. Make sure you have Node.js and npm installed:
   ```
   node --version
   npm --version
   ```

2. Make sure the Django backend is set up and migrations are applied

## Starting the Backend Server

1. Activate your Python virtual environment (if using one):
   ```
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Start the Django backend server:
   ```
   python manage.py runserver
   ```

3. Verify the server is running by visiting http://localhost:8000 in your browser

## Starting the Frontend Server

1. Open a new terminal window (keep the backend server running)

2. Navigate to the frontend directory:
   ```
   cd frontend
   ```

3. Install dependencies (if not already installed):
   ```
   npm install
   ```

4. Start the frontend development server:
   ```
   npm start
   ```

5. The React application should automatically open in your browser at http://localhost:3000

## Testing the Rental Agreement Flow

### As a Property Owner

1. **Log in as a Property Owner**
   - Use an owner account that exists in your database
   - If needed, create a new owner account and verify it

2. **Navigate to Rental Agreements**
   - Click on "Rental Agreements" in the navigation bar
   - You should see a list of existing agreements (if any)
   - Click "Create New" to create a new rental agreement

3. **Create a Rental Agreement**
   - Select a property from the dropdown (must be owned by the current user)
   - Select a tenant from the dropdown
   - Set start and end dates
   - Enter monthly rent and security deposit amounts
   - Click "Create Rental Agreement"
   - You should be redirected to the agreement details page

4. **Sign the Agreement as Owner**
   - On the agreement details page, click "Sign Agreement"
   - The owner signature status should update to "Signed"

### As a Tenant

1. **Log out and Log in as a Tenant**
   - Log out from the owner account
   - Log in using the tenant account that was selected in the rental agreement

2. **Navigate to Rental Agreements**
   - Click on "Rental Agreements" in the navigation bar
   - You should see the pending agreement in the list
   - Click on the agreement to view details

3. **Sign the Agreement as Tenant**
   - On the agreement details page, click "Sign Agreement"
   - The tenant signature status should update to "Signed"
   - The agreement status should change to "ACTIVE"

### Testing Termination (as Owner)

1. **Log back in as the Property Owner**

2. **Navigate to the Active Agreement**
   - Find the active agreement in the list
   - Click on it to view details

3. **Terminate the Agreement**
   - Click "Terminate Agreement"
   - Enter a reason for termination when prompted
   - The agreement status should change to "TERMINATED"

## Troubleshooting

### Backend Connection Issues
- Ensure the Django backend is running on port 8000
- Check that CORS settings are enabled in Django settings.py
- Verify the proxy setting in frontend/package.json is set to "http://localhost:8000"

### Authentication Issues
- Clear browser cookies and localStorage
- Ensure your JWT tokens are valid
- Check the browser console for API errors

### Data Loading Issues
- Verify that your database has the necessary data (properties, users with correct roles)
- Check API responses in the browser's Network tab
- Look at the Django server terminal for backend errors 