import threading
import time
from message import MessageTypes
from state import StateTypes


class HandlerThread(threading.Thread):
    def __init__(self, event_queue, state_machine, context):
        super(HandlerThread, self).__init__()
        self.event_queue = event_queue
        self.state_machine = state_machine
        self.context = context

    def run(self):
        self.state_machine.start()
        while True:
            item = self.event_queue.get()
            if item.stale:
                continue

            event = item.event
            # self.context.log_received_message(event, 0)
            self.state_machine.drive(event)
            if event.type == MessageTypes.STOP or event.type == MessageTypes.FAILURE_DETECTED:
                break

            # self.flush_queue()

    def flush_queue(self):
        with self.event_queue.mutex:
            for item in self.event_queue.queue:
                t = item.event.type
                if t == MessageTypes.BREAK or t == MessageTypes.STOP or MessageTypes.REENTER_SINGLE_STATE:
                    item.stale = False
                else:
                    item.stale = True

    def flush_all(self):
        with self.event_queue.mutex:
            for item in self.event_queue.queue:
                item.stale = True
