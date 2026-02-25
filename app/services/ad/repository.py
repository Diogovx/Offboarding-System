import logging
from contextlib import contextmanager
from typing import Any, Generator

from ldap3 import MODIFY_REPLACE, SUBTREE, Connection
from ldap3.core.exceptions import LDAPException

from app.config import settings
from app.services.ad.constants import (
    LDAP_ATTRS,
    MAX_SEARCH_RESULTS,
    UserAccountControl,
)
from app.services.ad.exceptions import ADConnectionError, ADOperationError
from app.services.ad.utils import escape_ldap_filter

from .connections import get_ldap_connection

logger = logging.getLogger(__name__)


@contextmanager
def ldap_connection() -> Generator[Connection, None, None]:
    """
    Context manager for LDAP connection

    Ensures that the connection is closed after use

    Yields:
    Active LDAP connection

    Raises:
    ADConnectionError: If connection fails
    """
    conn = None
    try:
        conn = get_ldap_connection()
        logger.debug("LDAP connection established.")
        yield conn
    except LDAPException as e:
        logger.error(f"Error connecting to LDAP.: {e}")
        raise ADConnectionError(f"Failed to connect to Active Directory.: {e}")
    finally:
        if conn:
            conn.unbind()
            logger.debug("LDAP connection closed.")


class ADRepository:
    def __init__(self):
        self.base_dn = settings.AD_BASE_DN
        self.disabled_ou = settings.DISABLED_OU

    def search_users(
        self,
        search_filter: str,
        attributes: list[str] | None = None,
        size_limit: int = MAX_SEARCH_RESULTS
    ) -> list[Any]:
        """
        Search for users in Active Directory

        Args:
        search_filter: LDAP filter
        attributes: Attributes to return
        size_limit: Result limit

        Returns:
        List of LDAP entries

        Raises:
        ADOperationError: If search fails
        """
        if attributes is None:
            attributes = LDAP_ATTRS["USER_SEARCH"]

        with ldap_connection() as conn:
            try:
                logger.info(f"Searching users with filter: {search_filter}")

                success = conn.search(
                    search_base=self.base_dn,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=attributes,
                    size_limit=size_limit
                )

                if not success:
                    logger.warning(f"LDAP search failed: {conn.result}")
                    raise ADOperationError(
                        "User search",
                        conn.result.get('description', 'Unknow error')
                    )

                entries = list(conn.entries)
                logger.info(f"Found {len(entries)} user(s)")

                return entries

            except LDAPException as e:
                logger.error(f"LDAP error: {e}")
                raise ADOperationError("User search", str(e))

    def search_by_registration(self, registration: str) -> list[Any]:
        """
        Search for users by registration number (EmployeeID field)

        Args:
        registration: Registration number to search for
        Returns:
        List of users found
        """
        safe_registration = escape_ldap_filter(registration)
        search_filter = (
            f"(&"
            f"(objectClass=user)"
            f"(EmployeeID=*{safe_registration}*)"
            f")"
        )

        return self.search_users(search_filter)

    def search_enabled_users(self) -> list[Any]:
        """
        Search only for enabled users

        Returns:
        List of enabled users
        """
        search_filter = (
            "(&"
            "(objectClass=user)"
            "(!(userAccountControl:1.2.840.113556.1.4.803:=2))"
            ")"
        )

        return self.search_users(search_filter)

    def disable_account(  # noqa: PLR6301
        self,
        dn: str,
        current_uac: int
    ) -> None:
        """
        Disable user account

        Args:
        dn: User's Distinguished Name
        current_uac: Current UserAccountControl

        Raises:

        ADOperationError: If operation fails
        """
        new_uac = current_uac | UserAccountControl.ACCOUNTDISABLE

        with ldap_connection() as conn:
            try:
                logger.info(f"Disabling account: {dn}")

                conn.modify(
                    dn,
                    {'userAccountControl': [(MODIFY_REPLACE, [new_uac])]}
                )

                if conn.result['description'] != 'success':
                    raise ADOperationError(
                        "Disable account",
                        conn.result.get('message', 'Unknown error')
                    )

                logger.info(f"Account successfully disabled.: {dn}")

            except LDAPException as e:
                logger.error(f"Error disabling account: {e}")
                raise ADOperationError("Disable account", str(e))

    def update_description(  # noqa: PLR6301
        self,
        dn: str,
        new_description: str
    ) -> None:
        """
        Update user description

        Args:
        dn: User's Distinguished Name
        new_description: New description

        Raises:
        ADOperationError: If operation fails
        """
        with ldap_connection() as conn:
            try:
                logger.info(f"Updating description: {dn}")

                conn.modify(
                    dn,
                    {'description': [(MODIFY_REPLACE, [new_description])]}
                )

                if conn.result['description'] != 'success':
                    raise ADOperationError(
                        "Update description",
                        conn.result.get('message', 'Unknow error')
                    )

                logger.info(f"Description updated successfully: {dn}")

            except LDAPException as e:
                logger.error(f"Error updating description.: {e}")
                raise ADOperationError("Update description", str(e))

    def move_to_ou(  # noqa: PLR6301
        self,
        dn: str,
        target_ou: str
    ) -> None:
        """
        Move user to another OU

        Args:

        dn: Current Distinguished Name
        target_ou: Destination OU

        Raises:
        ADOperationError: If operation fails
        """
        rdn = dn.split(',', 1)[0]

        with ldap_connection() as conn:
            try:
                logger.info(f"Moving user {dn} to {target_ou}")

                conn.modify_dn(
                    dn,
                    rdn,
                    new_superior=target_ou
                )

                if conn.result['description'] != 'success':
                    raise ADOperationError(
                        "Move User",
                        conn.result.get('message', 'Unknown error')
                    )

                logger.info(f"User successfully moved to: {target_ou}")

            except LDAPException as e:
                logger.error(f"Error moving user.: {e}")
                raise ADOperationError("Move User", str(e))
