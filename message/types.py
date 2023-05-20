from enum import Enum


class MessageTypes(Enum):
    STOP = 0
    DISCOVER = 1
    ACCEPT = 2
    BREAK = 3
    REENTER_SINGLE_STATE = 4

    def get_cat(self):
        pass
