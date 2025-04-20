from django.core.management.base import BaseCommand
from ledger.models import Block, SmartContract
from ledger.services import SmartContractService
from django.utils import timezone
import json

def test_ownership_verification():
    # First, let's get an existing property from the blockchain
    latest_block = Block.objects.order_by('-block_number').first()
    if not latest_block:
        print("No properties found in blockchain")
        return
    
    print(f"\nFound property in blockchain:")
    print(f"Property ID: {latest_block.property_id}")
    print(f"Current Owner ID: {latest_block.owner_id}")
    
    # Let's create a verification request
    # We'll use the actual owner ID to test a valid case
    claimed_owner_id = latest_block.owner_id
    requester_id = 999  # Some test requester ID
    
    print(f"\nCreating verification request:")
    print(f"Property ID: {latest_block.property_id}")
    print(f"Claimed Owner ID: {claimed_owner_id}")
    print(f"Requester ID: {requester_id}")
    
    success, message, contract_id = SmartContractService.create_verification_request(
        property_id=latest_block.property_id,
        claimed_owner_id=claimed_owner_id,
        requester_id=requester_id
    )
    
    print(f"\nVerification request result:")
    print(f"Success: {success}")
    print(f"Message: {message}")
    print(f"Contract ID: {contract_id}")
    
    if contract_id:
        # Get the contract and check its status
        contract = SmartContract.objects.get(contract_id=contract_id)
        
        # Force auto-execution since conditions are met
        success, result = contract.auto_execute()
        
        print(f"\nContract auto-execution result:")
        print(f"Success: {success}")
        print(f"Result: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
        
        # Refresh contract from database
        contract.refresh_from_db()
        print(f"\nContract details after execution:")
        print(f"Status: {contract.status}")
        print(f"Type: {contract.contract_type}")
        print(f"Created at: {contract.created_at}")
        print(f"Verification data: {json.dumps(contract.verification_data, indent=2)}")
        print(f"Execution result: {json.dumps(contract.execution_result, indent=2)}")
        
        # Now let's test with a wrong owner ID
        wrong_owner_id = claimed_owner_id + 1
        print(f"\nTesting with wrong owner ID {wrong_owner_id}:")
        success, message, contract_id = SmartContractService.create_verification_request(
            property_id=latest_block.property_id,
            claimed_owner_id=wrong_owner_id,
            requester_id=requester_id
        )
        
        print(f"Success: {success}")
        print(f"Message: {message}")
        print(f"Contract ID: {contract_id}")
        
        if contract_id:
            contract = SmartContract.objects.get(contract_id=contract_id)
            
            # Force auto-execution for wrong owner
            success, result = contract.auto_execute()
            
            print(f"\nContract auto-execution result (wrong owner):")
            print(f"Success: {success}")
            print(f"Result: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
            
            # Refresh contract from database
            contract.refresh_from_db()
            print(f"\nContract details after execution (wrong owner):")
            print(f"Status: {contract.status}")
            print(f"Verification data: {json.dumps(contract.verification_data, indent=2)}")
            print(f"Execution result: {json.dumps(contract.execution_result, indent=2)}")

if __name__ == '__main__':
    test_ownership_verification() 