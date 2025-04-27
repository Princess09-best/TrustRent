# TrustRent Frontend Implementation

## Overview

We've implemented a React-based frontend for the TrustRent application that integrates with the existing Django backend. The frontend provides a user interface for managing rental agreements, including creation, signing, viewing, and termination.

## Features Implemented

### Rental Agreement Management
- **Create Rental Agreements**: Property owners can create new rental agreements, specifying property, tenant, dates, and financial terms.
- **Sign Rental Agreements**: Both property owners and tenants can sign agreements using their respective accounts.
- **View Rental Agreement Details**: Users can view comprehensive information about rental agreements, including parties involved, property details, and signature status.
- **List Rental Agreements**: Users can see all their relevant rental agreements with filtering options.
- **Terminate Rental Agreements**: Property owners can terminate active agreements with a reason.

### Navigation and User Experience
- **Responsive Navbar**: Context-aware navigation based on user role.
- **Role-Based Access Control**: Different UI components and actions based on user role.
- **Styled Components**: Consistent styling using ThemeProvider.

## Technical Implementation

### Components Created
1. `RentalAgreementCreate.jsx` - Form for creating new rental agreements
2. `RentalAgreementDetails.jsx` - Detailed view of a rental agreement with signature and termination functionality
3. `RentalAgreementList.jsx` - List view of all rental agreements with filtering
4. `Navbar.jsx` - Navigation component with role-based links

### Integration Points
The frontend interacts with the following backend API endpoints:
- `/api/trustchain/rental/create/` - Create a new rental agreement
- `/api/trustchain/rental/{agreement_id}/` - Fetch a specific rental agreement
- `/api/trustchain/rental/{agreement_id}/sign/` - Sign a rental agreement
- `/api/trustchain/rental/{agreement_id}/terminate/` - Terminate a rental agreement
- `/api/trustchain/rental/` - Fetch all rental agreements 

## How to Run

### Prerequisites
- Node.js (v16+)
- npm or yarn
- Running Django backend (on http://localhost:8000)

### Setup and Run
1. Start the Django backend:
   ```
   python manage.py runserver
   ```

2. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```

3. Start the React development server:
   ```
   npm start
   ```

4. Access the application at http://localhost:3000

## Testing the Rental Agreement Flow

1. **Login as Property Owner**
   - Use owner credentials to log in

2. **Create a Rental Agreement**
   - Navigate to "Rental Agreements"
   - Click "Create New"
   - Fill in the property, tenant, dates, and financial information
   - Submit the form

3. **Sign the Agreement as Owner**
   - View the created agreement
   - Click "Sign Agreement"

4. **Log out and Login as Tenant**
   - Use tenant credentials to log in

5. **Sign the Agreement as Tenant**
   - Navigate to "Rental Agreements"
   - Find and open the pending agreement
   - Click "Sign Agreement"
   - The agreement status should change to "ACTIVE"

6. **View/Terminate Agreement**
   - As owner, you can view active agreements and terminate them if needed
   - As tenant, you can view your active agreements

## Future Enhancements

- Add property browsing capabilities for tenants
- Implement payment tracking and reminders
- Add document upload and attachment functionality
- Implement real-time notifications for agreement status changes
- Add responsive design for mobile users 