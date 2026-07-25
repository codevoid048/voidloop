"""
Validation Utilities for Tracker Backend.

Provides validation functions for business context including phone numbers,
pincodes, GST, PAN, Aadhar, and other common business validations.
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat, PhoneNumberType

from .exceptions import ValidationException, InvalidFormatException


# ============================================================================
# Regular Expression Patterns
# ============================================================================

# Indian postal code
PINCODE_PATTERN = re.compile(r'^[1-9]\d{5}$')  # 6 digits, not starting with 0

# GST number pattern
GST_PATTERN = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')

# PAN number pattern
PAN_PATTERN = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')

# Aadhar number pattern
AADHAR_PATTERN = re.compile(r'^[2-9]{1}[0-9]{3}[0-9]{4}[0-9]{4}$')

# Name patterns
NAME_PATTERN = re.compile(r'^[A-Za-z\s\.\-\']{2,50}$')  # Letters, spaces, dots, hyphens, apostrophes

# Email pattern (RFC 5322 compliant)
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Password patterns
PASSWORD_PATTERNS = {
    'has_uppercase': re.compile(r'[A-Z]'),
    'has_lowercase': re.compile(r'[a-z]'),
    'has_digit': re.compile(r'\d'),
    'has_special': re.compile(r'[!@#$%^&*()_+\-=\[\]{};\'\"\\|,.<>\/?]'),
}


# ============================================================================
# Phone Number Validation
# ============================================================================

def validate_mobile_number(mobile: str, country: str = 'IN') -> Dict[str, Any]:
    """
    Validate mobile number.

    Args:
        mobile: Mobile number to validate
        country: Two-letter ISO country code used as default region when
            number is not provided in international format.

    Returns:
        Dictionary with validation result and normalized number

    Example:
        result = validate_mobile_number('+14155552671')
        # Returns: {'valid': True, 'normalized': '+14155552671', ...}
    """
    if not mobile:
        return {'valid': False, 'error': 'Mobile number is required'}

    clean_mobile = mobile.strip()
    default_region = None if clean_mobile.startswith('+') else country.upper()

    try:
        parsed = phonenumbers.parse(clean_mobile, default_region)
    except NumberParseException:
        return {'valid': False, 'error': 'Invalid mobile number format'}

    if not phonenumbers.is_possible_number(parsed):
        return {'valid': False, 'error': 'Mobile number is not possible'}

    if not phonenumbers.is_valid_number(parsed):
        return {'valid': False, 'error': 'Mobile number is not valid'}

    phone_type = phonenumbers.number_type(parsed)
    allowed_types = {PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE_OR_MOBILE}
    if phone_type not in allowed_types:
        return {'valid': False, 'error': 'Only mobile phone numbers are allowed'}

    normalized = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)

    return {
        'valid': True,
        'normalized': normalized,
        'country_code': f"+{parsed.country_code}",
        'national_number': str(parsed.national_number),
        'carrier': None,
    }


def normalize_mobile(mobile: str, country: str = 'IN') -> str:
    """
    Normalize mobile number to standard format.

    Args:
        mobile: Mobile number to normalize
        country: Two-letter ISO country code used as default region when
            number is not provided in international format.

    Returns:
        Normalized mobile number

    Raises:
        ValidationException: If mobile number is invalid
    """
    result = validate_mobile_number(mobile, country)
    if not result['valid']:
        raise ValidationException(message=f"Invalid mobile number: {result['error']}")
    return result['normalized']


# ============================================================================
# Pincode Validation
# ============================================================================

def validate_pincode(pincode: str) -> Dict[str, Any]:
    """
    Validate Indian pincode.

    Args:
        pincode: Pincode to validate

    Returns:
        Dictionary with validation result and location info
    """
    if not pincode:
        return {'valid': False, 'error': 'Pincode is required'}

    clean_pincode = pincode.strip()

    if not PINCODE_PATTERN.match(clean_pincode):
        return {
            'valid': False,
            'error': 'Pincode must be 6 digits and cannot start with 0'
        }

    # Basic region mapping (first digit indicates region)
    region_map = {
        '1': 'Northern',
        '2': 'Northern',
        '3': 'Western',
        '4': 'Southern',
        '5': 'Southern',
        '6': 'Eastern',
        '7': 'Eastern',
        '8': 'Eastern',
        '9': 'Army Postal Service',
    }

    first_digit = clean_pincode[0]
    region = region_map.get(first_digit, 'Unknown')

    return {
        'valid': True,
        'pincode': clean_pincode,
        'region': region,
        'serviceable': True,  # Could integrate with shipping service
    }


# ============================================================================
# GST Number Validation
# ============================================================================

def validate_gst_number(gst: str) -> Dict[str, Any]:
    """
    Validate Indian GST number.

    Args:
        gst: GST number to validate

    Returns:
        Dictionary with validation result and extracted info
    """
    if not gst:
        return {'valid': False, 'error': 'GST number is required'}

    clean_gst = gst.strip().upper()

    if not GST_PATTERN.match(clean_gst):
        return {
            'valid': False,
            'error': 'Invalid GST number format'
        }

    # Extract components
    state_code = clean_gst[:2]
    pan = clean_gst[2:12]
    entity_code = clean_gst[12]
    checksum = clean_gst[14]

    # Validate state code
    valid_state_codes = [f"{i:02d}" for i in range(1, 38)]  # 01-37 are valid
    if state_code not in valid_state_codes:
        return {'valid': False, 'error': 'Invalid state code in GST number'}

    return {
        'valid': True,
        'gst_number': clean_gst,
        'state_code': state_code,
        'pan_number': pan,
        'entity_code': entity_code,
        'checksum': checksum,
    }


# ============================================================================
# PAN Number Validation
# ============================================================================

def validate_pan_number(pan: str) -> Dict[str, Any]:
    """
    Validate Indian PAN number.

    Args:
        pan: PAN number to validate

    Returns:
        Dictionary with validation result and extracted info
    """
    if not pan:
        return {'valid': False, 'error': 'PAN number is required'}

    clean_pan = pan.strip().upper()

    if not PAN_PATTERN.match(clean_pan):
        return {
            'valid': False,
            'error': 'PAN must be 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)'
        }

    # Extract info from PAN structure
    # 4th character indicates entity type
    entity_types = {
        'P': 'Individual',
        'F': 'Firm/LLP',
        'C': 'Company',
        'H': 'HUF',
        'A': 'Association of Persons',
        'T': 'Trust',
        'B': 'Body of Individuals',
        'G': 'Government',
        'J': 'Artificial Judicial Person',
        'L': 'Local Authority',
    }

    entity_code = clean_pan[3]
    entity_type = entity_types.get(entity_code, 'Unknown')

    return {
        'valid': True,
        'pan_number': clean_pan,
        'entity_type': entity_type,
        'entity_code': entity_code,
    }


# ============================================================================
# Email Validation
# ============================================================================

def validate_email_address(email: str) -> Dict[str, Any]:
    """
    Enhanced email validation using regex pattern.

    Args:
        email: Email address to validate

    Returns:
        Dictionary with validation result and normalized email
    """
    if not email:
        return {'valid': False, 'error': 'Email address is required'}

    clean_email = email.strip().lower()

    if not EMAIL_PATTERN.match(clean_email):
        return {
            'valid': False,
            'error': 'Invalid email address format'
        }

    # Basic additional checks
    if len(clean_email) > 254:  # RFC 5321 limit
        return {
            'valid': False,
            'error': 'Email address is too long (max 254 characters)'
        }

    local_part, domain = clean_email.rsplit('@', 1)

    if len(local_part) > 64:  # RFC 5321 limit
        return {
            'valid': False,
            'error': 'Email local part is too long (max 64 characters)'
        }

    # Check for consecutive dots
    if '..' in clean_email:
        return {
            'valid': False,
            'error': 'Email cannot contain consecutive dots'
        }

    return {
        'valid': True,
        'email': clean_email,
        'local': local_part,
        'domain': domain,
        'normalized': clean_email,
    }


# ============================================================================
# Password Validation
# ============================================================================

def validate_password_strength(password: str, min_length: int = 8) -> Dict[str, Any]:
    """
    Validate password strength.

    Args:
        password: Password to validate
        min_length: Minimum password length

    Returns:
        Dictionary with validation result and strength score
    """
    if not password:
        return {'valid': False, 'error': 'Password is required', 'score': 0}

    errors = []
    score = 0

    # Length check
    if len(password) < min_length:
        errors.append(f'Password must be at least {min_length} characters long')
    else:
        score += 1

    # Character type checks
    if PASSWORD_PATTERNS['has_uppercase'].search(password):
        score += 1
    else:
        errors.append('Password must contain at least one uppercase letter')

    if PASSWORD_PATTERNS['has_lowercase'].search(password):
        score += 1
    else:
        errors.append('Password must contain at least one lowercase letter')

    if PASSWORD_PATTERNS['has_digit'].search(password):
        score += 1
    else:
        errors.append('Password must contain at least one digit')

    if PASSWORD_PATTERNS['has_special'].search(password):
        score += 1
    else:
        errors.append('Password must contain at least one special character')

    # Additional length bonus
    if len(password) >= 12:
        score += 1

    # Determine strength level
    if score <= 2:
        strength = 'Weak'
    elif score <= 3:
        strength = 'Fair'
    elif score <= 4:
        strength = 'Good'
    else:
        strength = 'Strong'

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'score': score,
        'strength': strength,
        'max_score': 6,
    }


# ============================================================================
# Name Validation
# ============================================================================

def validate_person_name(name: str, min_length: int = 2, max_length: int = 50) -> Dict[str, Any]:
    """
    Validate person name.

    Args:
        name: Name to validate
        min_length: Minimum name length
        max_length: Maximum name length

    Returns:
        Dictionary with validation result and normalized name
    """
    if not name:
        return {'valid': False, 'error': 'Name is required'}

    clean_name = name.strip()

    if len(clean_name) < min_length:
        return {'valid': False, 'error': f'Name must be at least {min_length} characters'}

    if len(clean_name) > max_length:
        return {'valid': False, 'error': f'Name must be no more than {max_length} characters'}

    if not NAME_PATTERN.match(clean_name):
        return {
            'valid': False,
            'error': 'Name can only contain letters, spaces, dots, hyphens, and apostrophes'
        }

    # Normalize name (title case)
    normalized_name = ' '.join(word.capitalize() for word in clean_name.split())

    return {
        'valid': True,
        'name': clean_name,
        'normalized': normalized_name,
    }


# ============================================================================
# Business Validation
# ============================================================================

def validate_price(price: Any, min_price: Decimal = Decimal('0'), max_price: Optional[Decimal] = None) -> Dict[str, Any]:
    """
    Validate price value.

    Args:
        price: Price to validate
        min_price: Minimum allowed price
        max_price: Maximum allowed price

    Returns:
        Dictionary with validation result and normalized price
    """
    try:
        if isinstance(price, str):
            decimal_price = Decimal(price.strip())
        else:
            decimal_price = Decimal(str(price))
    except (InvalidOperation, ValueError, TypeError):
        return {'valid': False, 'error': 'Invalid price format'}

    if decimal_price < min_price:
        return {'valid': False, 'error': f'Price must be at least ₹{min_price}'}

    if max_price and decimal_price > max_price:
        return {'valid': False, 'error': f'Price cannot exceed ₹{max_price}'}

    # Check for reasonable decimal places (max 2 for currency)
    if decimal_price.as_tuple().exponent < -2:
        return {'valid': False, 'error': 'Price can have at most 2 decimal places'}

    return {
        'valid': True,
        'price': decimal_price,
        'formatted': f"₹{decimal_price:,.2f}",
    }


def validate_quantity(quantity: Any, min_qty: int = 1, max_qty: int = 1000) -> Dict[str, Any]:
    """
    Validate quantity value.

    Args:
        quantity: Quantity to validate
        min_qty: Minimum allowed quantity
        max_qty: Maximum allowed quantity

    Returns:
        Dictionary with validation result and normalized quantity
    """
    try:
        int_qty = int(quantity)
    except (ValueError, TypeError):
        return {'valid': False, 'error': 'Quantity must be a whole number'}

    if int_qty < min_qty:
        return {'valid': False, 'error': f'Minimum quantity is {min_qty}'}

    if int_qty > max_qty:
        return {'valid': False, 'error': f'Maximum quantity is {max_qty}'}

    return {
        'valid': True,
        'quantity': int_qty,
    }


def validate_discount_percentage(discount: Any) -> Dict[str, Any]:
    """
    Validate discount percentage.

    Args:
        discount: Discount percentage to validate

    Returns:
        Dictionary with validation result
    """
    try:
        decimal_discount = Decimal(str(discount))
    except (InvalidOperation, ValueError, TypeError):
        return {'valid': False, 'error': 'Invalid discount format'}

    if decimal_discount < 0:
        return {'valid': False, 'error': 'Discount cannot be negative'}

    if decimal_discount > 100:
        return {'valid': False, 'error': 'Discount cannot exceed 100%'}

    return {
        'valid': True,
        'discount': decimal_discount,
        'formatted': f"{decimal_discount}%",
    }


# ============================================================================
# Date Validation
# ============================================================================

def validate_age(birth_date: date, min_age: int = 18, max_age: int = 120) -> Dict[str, Any]:
    """
    Validate age based on birth date.

    Args:
        birth_date: Date of birth
        min_age: Minimum age required
        max_age: Maximum age allowed

    Returns:
        Dictionary with validation result and calculated age
    """
    if not isinstance(birth_date, date):
        return {'valid': False, 'error': 'Invalid birth date'}

    today = date.today()

    if birth_date > today:
        return {'valid': False, 'error': 'Birth date cannot be in the future'}

    # Calculate age
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1

    if age < min_age:
        return {'valid': False, 'error': f'Minimum age is {min_age} years'}

    if age > max_age:
        return {'valid': False, 'error': f'Maximum age is {max_age} years'}

    return {
        'valid': True,
        'age': age,
        'birth_date': birth_date,
    }


# ============================================================================
# Convenience Functions
# ============================================================================

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that all required fields are present and not empty.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Returns:
        List of missing field names
    """
    missing_fields = []

    for field in required_fields:
        value = data.get(field)
        if value is None or value == '' or (isinstance(value, str) and value.strip() == ''):
            missing_fields.append(field)

    return missing_fields


def validate_choice_field(value: Any, choices: List[Any], field_name: str = 'field') -> Dict[str, Any]:
    """
    Validate that value is one of the allowed choices.

    Args:
        value: Value to validate
        choices: List of allowed choices
        field_name: Name of the field (for error messages)

    Returns:
        Dictionary with validation result
    """
    if value not in choices:
        return {
            'valid': False,
            'error': f'{field_name} must be one of: {", ".join(map(str, choices))}'
        }

    return {
        'valid': True,
        'value': value,
    }


# ============================================================================
# Exception Raising Validators
# ============================================================================

def ensure_valid_mobile(mobile: str, country: str = 'IN') -> str:
    """Validate mobile and return normalized version, raise exception if invalid."""
    return normalize_mobile(mobile, country)


def ensure_valid_pincode(pincode: str) -> str:
    """Validate pincode and return it, raise exception if invalid."""
    result = validate_pincode(pincode)
    if not result['valid']:
        raise ValidationException(message=result['error'])
    return result['pincode']


def ensure_valid_email(email: str) -> str:
    """Validate email and return normalized version, raise exception if invalid."""
    result = validate_email_address(email)
    if not result['valid']:
        raise ValidationException(message=result['error'])
    return result['normalized']


def ensure_valid_gst(gst: str) -> str:
    """Validate GST number and return it, raise exception if invalid."""
    result = validate_gst_number(gst)
    if not result['valid']:
        raise ValidationException(message=result['error'])
    return result['gst_number']


def ensure_valid_pan(pan: str) -> str:
    """Validate PAN number and return it, raise exception if invalid."""
    result = validate_pan_number(pan)
    if not result['valid']:
        raise ValidationException(message=result['error'])
    return result['pan_number']