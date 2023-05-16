from enum import Enum


class MessageTypes(Enum):
    STOP = 0
    DISCOVER = 1
    ACCEPT = 2
    ACK = 3
    BREAK = 4
    THAW = 5

    def get_cat(self):
        pass
