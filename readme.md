--User Stories--

User Management Module (UMM)
1.	US-UMM-001 - User Registration and Authentication
•	As a property owner, I want to register and authenticate securely using multi-factor authentication, so that I can manage my properties safely.
•	As a renter or buyer, I want to create an account and verify my identity securely, so that I can rent or buy properties with confidence.
2.	US-UMM-002 - Role-Based Access Control (RBAC)
•	As a system administrator, I want to enforce role-based access control, so that users have access only to the functionalities relevant to their role.
3.	US-UMM-003 - Identity Verification for Property Owners
o	As a property owner, I want to verify my identity using government-issued documents, so that I can list properties without fraudulent concerns.
o	As a renter or buyer, I want to be assured that the property owners are verified, so that I can trust the listings.*
4.	US-UMM-004 - Client Reputation and Review System
•	As a property owner, I want to view the rental history and reputation score of potential tenants, so that I can make informed decisions.
•	As a renter or buyer, I want to leave and receive reviews after transactions, so that I can build a trustworthy profile over time.

Property Management Module (PMM)
5.	US-PMM-001 - Property Ownership Registration on Blockchain
•	As a property owner, I want to register my property on a blockchain ledger, so that ownership rights are immutable and transparent.
•	As a buyer, I want to verify property ownership on the blockchain before making a purchase, so that I can avoid fraudulent transactions.
6.	US-PMM-002 - Property Listing for Sale and Rental
•	As a property owner, I want to list my property for rent or sale, so that I can attract potential renters or buyers.
•	As a renter or buyer, I want to browse listed properties with complete details, so that I can make informed decisions.
7.	US-PMM-003 - Ownership Verification via Smart Contracts
•	As a buyer, I want to verify the ownership of a property via smart contracts, so that I can ensure the seller is legitimate.
8.	US-PMM-004 - Property Ownership Transfer
•	As a property owner, I want to transfer ownership rights securely via the blockchain when selling my property, so that the records remain immutable.
•	As a buyer, I want to receive proof of ownership transfer on the blockchain, so that I can confirm my legal rights over the property.


Rental Management Module (RMM)
9.	US-RMM-001 - Rental Agreement via Smart Contracts
•	As a property owner, I want rental agreements to be automatically created and enforced via smart contracts, so that both parties follow the agreed terms.*(future implementation*legal validity)
•	As a renter, I want my rental agreement to be securely stored on the blockchain, so that I have proof of my lease terms.
10.	US-RMM-002 - Tenant Rental History Tracking
•	As a property owner, I want to access the rental history of a property, so that I can verify the previous tenants.
•	As a renter, I want my rental history to be recorded, so that I can prove my past rental experiences for future transactions.
11.	US-RMM-003 - Consensus-Based Rental Verification
•	As a renter, I want to verify the legitimacy of a new rental claim using feedback from previous tenants, so that I can avoid rental scams.
•	As a previous renter, I want to confirm whether I rented a property from the listed owner, so that I can help prevent fraud.
12.	US-RMM-004 - Property Return and Condition Verification
•	As a renter, I want to document the property's condition upon moving in and moving out, so that I can avoid disputes over damages.
•	As a property owner, I want to verify the condition of my property after a tenant moves out, so that I can assess any damages fairly.

*assumption of property validity and no land commission issues or litigation issues( recommended path) or verification from Lands commission(complications of political interactions, future works implementation)


--System Requirements--
Functional requirements describe what the system should do — based on your user stories, here they are grouped by module:

1. User Management Module (UMM)
FR1: The system shall allow users (property owners, renters, buyers) to register and log in using multi-factor authentication.

FR2: The system shall enforce role-based access control (RBAC) to restrict functionalities based on user roles.

FR3: The system shall enable property owners to upload government-issued ID for identity verification.

FR4: The system shall allow renters and buyers to view verification status of property owners.

FR5: The system shall maintain a review and rating system for renters and owners after transactions.

FR6: The system shall provide a view of tenant rental history for property owners.

2. Property Management Module (PMM)
FR7: The system shall allow verified property owners to register property ownership on a blockchain ledger.

FR8: The system shall allow users to browse listed properties with details such as location, price, and verification status.

FR9: The system shall enable ownership verification through smart contracts.

FR10: The system shall allow secure ownership transfer of properties through smart contracts.

FR11: The system shall provide buyers with immutable proof of ownership transfer.

3. Rental Management Module (RMM)
FR12: The system shall generate rental agreements using smart contracts and store them on the blockchain. (future legal implementation)

FR13: The system shall allow tenants and owners to record and view property rental history.

FR14: The system shall allow former tenants to verify rental claims through consensus feedback.

FR15: The system shall allow users to upload and access documentation of property conditions during check-in and check-out.