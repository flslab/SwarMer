from dataclasses import dataclass, field
from typing import Any
import threading
import numpy as np

import message


class NetworkThread(threading.Thread):
    def __init__(self, event_queue, context, sock):
        super(NetworkThread, self).__init__()
        self.event_queue = event_queue
        self.context = context
        self.sock = sock
        self.latest_message_id = dict()

    def run(self):
        while True:
            # if self.sock.is_ready():
            msg = self.sock.receive()
            if self.is_message_valid(msg):
                self.latest_message_id[msg.fid] = msg.id
                self.context.log_received_message(msg)
                self.event_queue.put(NetworkThread.prioritize_message(msg))
                if msg.type == message.MessageTypes.STOP:
                    break

    def is_message_valid(self, msg):
        if msg.fid == self.context.fid:
            return False
        if msg.dest_fid != self.context.fid and msg.dest_fid != '*':
            return False
        if msg.dest_swarm_id != self.context.swarm_id and msg.dest_swarm_id != '*':
            return False
        if msg.fid in self.latest_message_id and msg.id < self.latest_message_id[msg.fid]:
            return False
        if msg.type == message.MessageTypes.CHALLENGE_INIT:
            dist = np.linalg.norm(msg.el - self.context.el)
            if dist > msg.range:
                return False
        return True

    @staticmethod
    def prioritize_message(msg):
        if msg.type == message.MessageTypes.STOP or msg.type == message.MessageTypes.THAW_SWARM:
            return PrioritizedItem(0, msg, False)
        if msg.type == message.MessageTypes.SIZE_QUERY or msg.type == message.MessageTypes.SIZE_REPLY:
            return PrioritizedItem(2, msg, False)
        if msg.type == message.MessageTypes.SET_WAITING or msg.type == message.MessageTypes.FOLLOW_MERGE:
            return PrioritizedItem(1, msg, False)
        return PrioritizedItem(3, msg, False)


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    event: Any = field(compare=False)
    stale: bool = field(compare=False)
