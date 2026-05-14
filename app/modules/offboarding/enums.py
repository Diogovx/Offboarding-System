from enum import StrEnum


class OffboardingSystem(StrEnum):
    """Represents the external systems involved in the offboarding process."""

    NETWORK = "Network"
    INTOUCH = "InTouch"
    EQUIPMENT = "Equipamentos"
    ACCESS = "Acesso"
