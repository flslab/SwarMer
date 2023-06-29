from enum import Enum


class MessageTypes(Enum):
    STOP = 0
    DISCOVER = 1
    ACCEPT = 2
    BREAK = 3
    BREAK_ACK = 4
    REENTER_SINGLE_STATE = 5
    SEND_BREAK = 6
    QUERY_CLIQUES = 7
    REPLY_CLIQUES = 8
    EXPLORE = 9
    EXPLORE_ACK = 10
    EXPAND_RANGE = 11

    def get_cat(self):
        pass
