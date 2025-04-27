# TrustRent Frontend

This is the frontend application for TrustRent, a blockchain-based property rental platform. The frontend interacts with the Django backend API and provides a user interface for property owners and seekers.

## Features

- **User Authentication**
  - Registration
  - Login
  - Role-based access control

- **Property Management**
  - Create and manage property listings (for property owners)
  - View property details

- **Rental Agreement Management**
  - Create rental agreements (for property owners)
  - Sign rental agreements (for both property owners and seekers)
  - View agreement details
  - Terminate agreements (for property owners)
  - Track agreement status

## Getting Started

### Prerequisites

- Node.js (v16+)
- npm or yarn
- Running TrustRent backend server

### Installation

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```
   or
   ```
   yarn install
   ```

### Running the Application

1. Make sure the Django backend is running (typically on http://localhost:8000)

2. Start the frontend development server:
   ```
   npm start
   ```
   or
   ```
   yarn start
   ```

3. The application will be available at http://localhost:3000

## API Integration

The frontend is configured to proxy API requests to the Django backend running on http://localhost:8000. This is set up in the `package.json` file with the `"proxy"` field.

## Project Structure

- `src/` - Source code directory
  - `App.js` - Main application component with routing
  - `index.js` - Application entry point
  - `Navbar.jsx` - Navigation component
  - `Login.jsx` / `Register.jsx` - Authentication components
  - `OwnerCreateProperty.jsx` - Property creation component
  - `RentalAgreementCreate.jsx` - Component for creating rental agreements
  - `RentalAgreementDetails.jsx` - Component for viewing and signing rental agreements
  - `RentalAgreementList.jsx` - Component for listing all rental agreements

## Authentication Flow

1. Users register with their email, password, and role
2. Admin verifies user accounts
3. Users log in to access role-specific features
4. JWT tokens are stored in localStorage for authenticated requests

## Development

### Adding New Features

1. Create new component files in the `src/` directory
2. Update `App.js` to include new routes
3. Add any necessary API calls to interact with the backend

### Styling

The application uses Styled Components for styling. The theme is defined in `index.js` and can be extended as needed.

## Troubleshooting

- If you see API errors, ensure the backend server is running
- Check that the proxy setting in package.json matches your backend URL
- For authentication issues, clear localStorage and log in again

## License

This project is part of the TrustRent platform and is subject to its licensing terms.
