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
    FAILURE_DETECTED = 9
    REPLICA_REQUEST = 10
    REPLICA_REQUEST_HUB = 13
    ASSIGN_STANDBY = 11
    STANDBY_FAILED = 14
    MOVE = 12

    def get_cat(self):
        pass
