# Requirements to Architecture Component Mapping

| Requirement | Architecture Component | Justification |
|------------|----------------------|---------------|
| User Registration and Authentication (US-UMM-001) | - JWT Authentication<br>- User Management Module<br>- Default DB | Ensures secure user authentication and session management with multi-factor support and persistent user data storage |
| Role-Based Access Control (US-UMM-002) | - RBAC Middleware<br>- Core DB<br>- API Layer | Enforces access control at middleware level, stores role configurations in Core DB, and applies permissions across all API endpoints |
| Identity Verification (US-UMM-003) | - Document Management Module<br>- File Storage<br>- Core DB | Handles document uploads, verification, and secure storage of government IDs while maintaining user-document relationships |
| Reputation System (US-UMM-004) | - Core DB<br>- Ops DB<br>- API Layer | Stores review data, calculates reputation scores, and provides API endpoints for review management |
| Property Registration on Blockchain (US-PMM-001) | - Blockchain Core<br>- Smart Contract Engine<br>- Chain Ledger | Records immutable property ownership on blockchain with smart contract validation |
| Property Listing Management (US-PMM-002) | - Listing Management Module<br>- Ops DB<br>- File Storage | Manages property listings, stores property details and media, handles search functionality |
| Ownership Verification (US-PMM-003) | - Smart Contract Engine<br>- Property Validator<br>- Blockchain Core | Validates property ownership through smart contracts and blockchain records |
| Property Ownership Transfer (US-PMM-004) | - Smart Contract Engine<br>- Property Chain<br>- Block Management | Executes ownership transfers via smart contracts with blockchain validation and recording |
| Rental Agreements (US-RMM-001) | - Agreement Management Module<br>- Smart Contract Engine<br>- Chain Ledger | Creates and manages rental agreements as smart contracts with blockchain-based storage |
| Rental History Tracking (US-RMM-002) | - Ops DB<br>- Core DB<br>- API Layer | Maintains comprehensive rental history records linked to both properties and users |
| Consensus-Based Verification (US-RMM-003) | - Consensus Module<br>- Blockchain Core<br>- API Layer | Implements verification system using blockchain consensus mechanisms |
| Property Condition Verification (US-RMM-004) | - Document Management Module<br>- File Storage<br>- Ops DB | Handles property condition documentation, photo storage, and condition report management |

Note: This mapping demonstrates how each functional requirement is supported by specific architectural components, ensuring complete coverage of system requirements through the implemented architecture. 



