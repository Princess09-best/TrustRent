#!/usr/bin/env python
"""
Standalone script to test property transfer functionality.
This script simulates API requests to test the property transfer flow.
"""

import os
import sys
import json
import requests

# Base URL for API calls
BASE_URL = "http://localhost:8000/api"

def login(email, password):
    """Login and get authentication token"""
    print(f"Logging in as {email}...")
    response = requests.post(f"{BASE_URL}/login/", json={
        "email": email,
        "password": password
    })
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return None
    
    data = response.json()
    token = data.get("token")
    if not token:
        print("No token in response")
        return None
    
    print("Login successful!")
    return token

def initiate_transfer(token, property_id, new_owner_id):
    """Initiate property transfer"""
    print(f"Initiating transfer of property {property_id} to user {new_owner_id}...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/trustchain/transfer/initiate/", 
                           headers=headers,
                           json={
                               "property_id": property_id,
                               "new_owner_id": new_owner_id
                           })
    
    if response.status_code != 201:
        print(f"Transfer initiation failed: {response.text}")
        return None
    
    data = response.json()
    transfer_id = data.get("transfer_id")
    if not transfer_id:
        print("No transfer ID in response")
        return None
    
    print(f"Transfer initiated with ID: {transfer_id}")
    return transfer_id

def confirm_transfer(token, transfer_id):
    """Confirm property transfer"""
    print(f"Confirming transfer {transfer_id}...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/trustchain/transfer/{transfer_id}/confirm/", 
                            headers=headers)
    
    if response.status_code != 200:
        print(f"Transfer confirmation failed: {response.text}")
        return False
    
    data = response.json()
    print(f"Transfer confirmed: {data.get('message')}")
    print(f"Block number: {data.get('block_number')}")
    print(f"Transaction hash: {data.get('transaction_hash')}")
    print(f"New UserProperty ID: {data.get('new_user_property_id')}")
    return True

def check_transfer_status(token, property_id):
    """Check database status of property transfer"""
    print(f"Checking transfer status for property {property_id}...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/trustchain/transfer/property/{property_id}/db-status/", 
                          headers=headers)
    
    if response.status_code != 200:
        print(f"Status check failed: {response.text}")
        return False
    
    data = response.json()
    print("\nProperty Transfer Status:")
    print(f"Property: {data['property']['title']} ({data['property']['location']})")
    print(f"Current owner: {data['current_ownership']['owner_name']} (ID: {data['current_ownership']['owner_id']})")
    print(f"Blockchain owner: {data['blockchain']['blockchain_owner_id']}")
    print(f"Blockchain consistent: {data['blockchain']['is_consistent']}")
    
    print("\nOwnership History:")
    for record in data['ownership_history']:
        print(f"- {record['owner_name']} (Active: {record['is_active']}, Created: {record['created_at']})")
    
    return data['blockchain']['is_consistent']

def run_test(original_email, original_password, new_email, new_password, property_id):
    """Run the complete property transfer test"""
    # 1. Login as original owner
    original_token = login(original_email, original_password)
    if not original_token:
        return False
    
    # 2. Get new owner ID
    # In a real scenario, the frontend would find this ID based on a user search
    headers = {
        "Authorization": f"Bearer {original_token}"
    }
    
    response = requests.get(f"{BASE_URL}/users/search?email={new_email}", headers=headers)
    if response.status_code != 200:
        print(f"Failed to find new owner: {response.text}")
        # For testing, we'll use a hardcoded ID
        print("Using hardcoded new owner ID")
        new_owner_id = 2  # Adjust this based on your database
    else:
        new_owner_id = response.json()[0]['id']
    
    # 3. Initiate transfer
    transfer_id = initiate_transfer(original_token, property_id, new_owner_id)
    if not transfer_id:
        return False
    
    # 4. Login as new owner
    new_token = login(new_email, new_password)
    if not new_token:
        return False
    
    # 5. Confirm transfer
    if not confirm_transfer(new_token, transfer_id):
        return False
    
    # 6. Check transfer status
    return check_transfer_status(new_token, property_id)

if __name__ == "__main__":
    # Get parameters from command line or use defaults
    original_email = sys.argv[1] if len(sys.argv) > 1 else "original@example.com"
    original_password = sys.argv[2] if len(sys.argv) > 2 else "password123"
    new_email = sys.argv[3] if len(sys.argv) > 3 else "new@example.com"
    new_password = sys.argv[4] if len(sys.argv) > 4 else "password123"
    property_id = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    
    print("Property Transfer Test")
    print("---------------------")
    print(f"Original owner: {original_email}")
    print(f"New owner: {new_email}")
    print(f"Property ID: {property_id}")
    print("---------------------\n")
    
    success = run_test(original_email, original_password, new_email, new_password, property_id)
    
    if success:
        print("\n✅ TEST PASSED: Property transfer completed successfully")
    else:
        print("\n❌ TEST FAILED: Property transfer did not complete properly") 