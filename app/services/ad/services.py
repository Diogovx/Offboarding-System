from typing import Sequence
import logging

from app.models import ADUser, DisableUserRequest
from app.services.ad.repository import ADRepository
from app.services.ad.exceptions import (
    UserNotFoundError,
    MultipleUsersFoundError,
)
from app.services.ad.utils import (
    validate_registration,
    validate_performed_by,
    is_account_enabled,
    build_disabled_description,
)
from app.services.ad.constants import UserAccountControl

logger = logging.getLogger(__name__)


class ADService:
    def __init__(self):
        self.repository = ADRepository()

    def search_users(
        self,
        registration: str | None = None,
        enabled_only: bool = False
    ) -> Sequence[ADUser]:
        """
        Search for users in Active Directory

        Args:

        registration: Registration number to search (optional)
        enabled_only: Return only active users

        Returns:

        List of users found
        """
        logger.info(
            f"Searching users - "
            f"registration={registration}, enabled_only={enabled_only}"
        )

        if registration:

            registration = validate_registration(registration)
            entries = self.repository.search_by_registration(registration)
        elif enabled_only:
            entries = self.repository.search_enabled_users()
        else:
            entries = self.repository.search_users("(objectClass=user)")
        users = [self._entry_to_model(entry) for entry in entries]
        logger.info(f"Returning {len(users)} user(s)")
        return users

    def get_unique_user(self, registration: str) -> ADUser:
        """
        Search for a unique user by registration number

        Args:

        registration: User's registration number

        Returns:

        User found

        Raises:

        UserNotFoundError: If not found
        MultipleUsersFoundError: If multiple users are found
        """
        registration = validate_registration(registration)
        entries = self.repository.search_by_registration(registration)

        if not entries:
            logger.warning(f"User not found: {registration}")
            raise UserNotFoundError(registration)

        if len(entries) > 1:
            logger.warning(
                f"Multiple users found for '{registration}': "
                f"{len(entries)}"
            )
            raise MultipleUsersFoundError(registration, len(entries))

        return self._entry_to_model(entries[0])

    def disable_user(self, request: DisableUserRequest) -> ADUser:
        """
        Disable user in Active Directory and move to Deactivated OU

        Operations performed:
        1. Search for unique user by registration number
        2. Update description field
        3. Disable account (userAccountControl)
        4. Move to Deactivated Accounts OU

        Args:
        request: Deactivation request data

        Returns:
        Deactivated user

        Raises:
        UserNotFoundError: If user not found
        MultipleUsersFoundError: If multiple users are found
        ADOperationError: If operation fails
        """

        registration = validate_registration(request.registration)
        performed_by = validate_performed_by(request.performed_by)

        logger.info(
            f"Initiating user deactivation. - "
            f"registration={registration}, performed_by={performed_by}"
        )

        user = self.get_unique_user(registration)
        logger.info(f"User found: {user.sam_account_name} ({user.name})")

        if not user.enabled:
            logger.warning(
                f"The user is already disabled: {user.sam_account_name}"
            )
            return user

        dn = user.distinguished_name
        current_uac = self._get_uac_from_enabled(user.enabled)

        try:
            new_description = build_disabled_description(
                user.description,
                performed_by
            )

            logger.debug(f"New description: {new_description[:100]}...")
            self.repository.update_description(dn, new_description)

            self.repository.disable_account(dn, current_uac)

            self.repository.move_to_ou(dn, self.repository.disabled_ou)

            logger.info(
                f"User successfully deactivated.: {user.sam_account_name}"
            )

            user.enabled = False
            user.description = new_description

            return user

        except Exception as e:
            logger.error(
                f"Error deactivating user. {user.sam_account_name}: {e}",
                exc_info=True
            )
            raise

    @staticmethod
    def _entry_to_model(entry) -> ADUser:
        """
        Converts LDAP input to a Pydantic model

        Args:

        entry: LDAP Input

        Returns:
        ADUser Model
        """
        uac = int(entry.userAccountControl.value)

        return ADUser(
            name=entry.displayName.value or entry.cn.value,
            sam_account_name=entry.sAMAccountName.value,
            enabled=is_account_enabled(uac),
            distinguished_name=entry.distinguishedName.value,
            description=entry.description.value
            if 'description' in entry else None
        )

    @staticmethod
    def _get_uac_from_enabled(enabled: bool) -> int:
        """
        Rebuilds basic UAC from enabled status

        Args:
        enabled: Whether the account is enabled

        Returns:
        UserAccountControl value
        """
        base_uac = UserAccountControl.NORMAL_ACCOUNT

        if not enabled:
            base_uac |= UserAccountControl.ACCOUNTDISABLE

        return base_uac
