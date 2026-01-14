from enum import Enum


class EmailActions(str, Enum):
    CONSULT = "consult"
    ACTIVATE = "activate"
    DISABLE = "disable"

    @classmethod
    def get_by_id(cls, action_id: int):

        mapping = {1: cls.CONSULT, 2: cls.ACTIVATE, 3: cls.DISABLE}
        return mapping.get(action_id, cls.CONSULT)
