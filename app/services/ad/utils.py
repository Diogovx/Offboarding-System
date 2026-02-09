import re
from typing import Any
from app.services.ad.constants import UserAccountControl
from app.services.ad.exceptions import InvalidInputError


def escape_ldap_filter(value: str) -> str:
    """
    Escapes special characters in LDAP filters

    Prevents LDAP Injection by escaping dangerous characters

    Args:

    value: Value to be escaped

    Returns:
    Safe escaped value for use in LDAP filters

    Reference:

    RFC 4515 - LDAP: String Representation of Search Filters
    """
    replacements = {
        '*': r'\2a',
        '(': r'\28',
        ')': r'\29',
        '\\': r'\5c',
        '\x00': r'\00',
    }

    for char, escaped in replacements.items():
        value = value.replace(char, escaped)

    return value


def validate_registration(registration: str | None = None) -> str:
    """
    Validates registration format

    Args:

    registration: Registration to be validated

    Returns:
    Registration validated

    Raises:
    InvalidInputError: If invalid format
    """
    max_character = 50
    if not registration:
        raise InvalidInputError("registration", "It cannot be empty.")

    if len(registration) > max_character:
        raise InvalidInputError("registration", "Maximum 50 characters")

    if not re.match(r'^[a-zA-Z0-9_()-]+$', registration):
        raise InvalidInputError(
            "registration",
            "Only letters, numbers, hyphens, and underscores are allowed."
        )

    return registration


def validate_performed_by(performed_by: str) -> str:
    """
    Validates 'performed_by' field

Args:

    performed_by: Name of the performer

    Returns:
    Validated name

    Raises:
    InvalidInputError: If invalid format
    """
    max_character = 100
    if not performed_by:
        raise InvalidInputError("performed_by", "It cannot be empty")

    if len(performed_by) > max_character:
        raise InvalidInputError("performed_by", "Maximum 100 caracters")

    return performed_by.strip()


def is_account_enabled(uac: int) -> bool:
    """
    Checks if the account is enabled by the UserAccountControl

    Args:

    uac: Value of the userAccountControl

    Returns:
    True if the account is enabled
    """
    return not bool(uac & UserAccountControl.ACCOUNTDISABLE)


def build_disabled_description(
    old_description: str | None,
    performed_by: str,
    system_name: str = "Dismissal Assistant System"
) -> str:
    """
    Creates a new description for a disabled account

    Args:

    old_description: Previous description

    performed_by: Performed by

    system_name: System name

    Returns:

    New description

    Raises:

    InvalidInputError: If the description exceeds the limit
    """
    base = old_description or ""
    suffix = f" | Desativado por {performed_by} ({system_name})"
    new_description = base + suffix

    return new_description
