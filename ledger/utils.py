import hashlib
from datetime import datetime
from typing import Dict, Union, Optional

def normalize_block_data(data: Dict[str, Union[str, int, datetime, None]]) -> Dict[str, str]:
    """
    Normalizes block data by converting all values to strings in a consistent format.
    This ensures hash calculation remains consistent across the system.
    """
    normalized = {}
    
    # Convert property_id to string and ensure it's not just a number
    if isinstance(data.get('property_id'), int):
        normalized['property_id'] = f"PROP_{data['property_id']}"
    else:
        normalized['property_id'] = str(data.get('property_id', ''))
    
    # Convert owner_id to string
    normalized['owner_id'] = str(data.get('owner_id', ''))
    
    # Handle document_hash (can be None)
    normalized['document_hash'] = str(data.get('document_hash', '')) if data.get('document_hash') else ''
    
    # Convert block_number to string
    normalized['block_number'] = str(data.get('block_number', ''))
    
    # Format timestamp consistently
    timestamp = data.get('timestamp')
    if isinstance(timestamp, datetime):
        normalized['timestamp'] = timestamp.isoformat()
    else:
        normalized['timestamp'] = str(timestamp) if timestamp else ''
    
    return normalized

def calculate_block_hash(data: Dict[str, Union[str, int, datetime, None]]) -> str:
    """
    Calculates a SHA-256 hash for a block using normalized data.
    This is the single source of truth for hash calculation in the system.
    """
    normalized_data = normalize_block_data(data)
    
    # Create a deterministic string representation
    data_string = (
        f"{normalized_data['property_id']}"
        f"{normalized_data['owner_id']}"
        f"{normalized_data['document_hash']}"
        f"{normalized_data['block_number']}"
        f"{normalized_data['timestamp']}"
    )
    
    return hashlib.sha256(data_string.encode()).hexdigest() 