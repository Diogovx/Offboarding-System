from enum import Enum, IntEnum

class EmailActions(str, Enum):
    CONSULT = "consultado"
    ACTIVATE = "ativado"
    DISABLE = "desativado"

    @classmethod
    def get_by_id(cls, action_id: int):
       
        mapping = {1: cls.CONSULT, 2: cls.ACTIVATE, 3: cls.DISABLE}
        return mapping.get(action_id, cls.CONSULT)