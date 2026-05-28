import re
from typing import Any, Dict, Union

PII_PATTERNS = {
    "email": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "***@***.***"),
    "phone": (r'\b[6-9]\d{9}\b', "**********"),
    "phone_formatted": (r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', "***-***-****"),
    "pan": (r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', "XXXXX****X"),
    "aadhar": (r'\b\d{4}\s\d{4}\s\d{4}\b', "XXXX XXXX XXXX"),
    "account": (r'\b\d{9,18}\b', lambda m: "X"*(len(m.group())-4) + m.group()[-4:]),
}

ROLE_MASK_LEVELS = {
    "ADVISOR": ["email", "phone", "phone_formatted"],
    "OPERATIONS": ["pan", "aadhar"],
    "COMPLIANCE": [],  # Compliance sees everything
    "ADMIN": [],
}

def mask_value(value: str, role: str = "ADVISOR") -> str:
    patterns_to_mask = ROLE_MASK_LEVELS.get(role, ["email", "phone", "phone_formatted"])
    result = str(value)
    for pattern_name in patterns_to_mask:
        if pattern_name in PII_PATTERNS:
            pattern, replacement = PII_PATTERNS[pattern_name]
            if callable(replacement):
                result = re.sub(pattern, replacement, result)
            else:
                result = re.sub(pattern, replacement, result)
    return result

def mask_dict(data: Dict, role: str = "ADVISOR") -> Dict:
    if role == "COMPLIANCE":
        return data
    masked = {}
    sensitive_fields = {"email", "phone", "pan", "aadhar", "account_number", "password"}
    for key, value in data.items():
        if key in sensitive_fields and role != "COMPLIANCE":
            if isinstance(value, str):
                masked[key] = mask_value(value, role)
            else:
                masked[key] = "****"
        elif isinstance(value, dict):
            masked[key] = mask_dict(value, role)
        elif isinstance(value, list):
            masked[key] = [mask_dict(item, role) if isinstance(item, dict) else item for item in value]
        else:
            masked[key] = value
    return masked

def mask_response(data: Any, role: str = "ADVISOR") -> Any:
    if isinstance(data, dict):
        return mask_dict(data, role)
    elif isinstance(data, list):
        return [mask_dict(item, role) if isinstance(item, dict) else item for item in data]
    return data