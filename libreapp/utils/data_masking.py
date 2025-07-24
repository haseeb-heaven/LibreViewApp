"""Data masking utilities for sensitive information."""
from typing import Any, Dict, Protocol

class DataMasker(Protocol):
    """Protocol for sensitive data masking"""
    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]: ...

class DefaultDataMasker:
    """Default implementation of data masking"""
    
    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive data in dictionaries.
        
        Args:
            data: Dictionary containing potentially sensitive data
            
        Returns:
            Dictionary with sensitive data masked
        """
        if not isinstance(data, dict):
            return data
            
        masked_data = data.copy()
        sensitive_fields = [
            'token', 'email', 'password', 'firstName', 'lastName', 
            'username', 'Authorization'
        ]
        
        for key, value in masked_data.items():
            if key in sensitive_fields and value:
                masked_data[key] = f"{str(value)[:3]}...{str(value)[-4:]}" if len(str(value)) > 8 else "****"
            elif isinstance(value, dict):
                masked_data[key] = self.mask_sensitive_data(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self.mask_sensitive_data(item) if isinstance(item, dict) else item 
                    for item in value
                ]
                
        return masked_data
