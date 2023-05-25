from enum import Enum


class MessageTypes(Enum):
    STOP = 0
    DISCOVER = 1
    ACCEPT = 2
    BREAK = 3
    BREAK_ACK = 4
    REENTER_SINGLE_STATE = 5
    SEND_BREAK = 6

    def get_cat(self):
        pass
