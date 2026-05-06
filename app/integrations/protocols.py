from typing import Protocol


class UserManagerProtocol(Protocol):
    """
    Contract for integrations that manage the
    lifecycle of users in external systems.
    """
    def search_user(self, registration: str): ...
    def activate_user(self, registration: str): ...
    def deactivate_user(self, registration: str): ...


class AssetManagerProtocol(Protocol):
    """
    Contract for integrations that manage the
    assets in external systems.
    """
    def search_assets_by_user(self, registration: str): ...
    def checkin_asset(self, asset_id: str): ...
    def checkout_asset(self, asset_id: str, user_id: str): ...
