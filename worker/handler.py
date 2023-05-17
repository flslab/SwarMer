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
            if isinstance(item.event, StateTypes):
                self.state_machine.reenter(item.event)
                continue

            if item.stale:
                continue

            event = item.event
            if event.type == MessageTypes.THAW:
                self.flush_all()

            self.state_machine.drive(event)
            if event.type == MessageTypes.STOP:
                break

            # self.flush_queue()

    def flush_queue(self):
        with self.event_queue.mutex:
            for item in self.event_queue.queue:
                t = item.event.type
                if t == MessageTypes.BREAK or t == MessageTypes.STOP:
                    item.stale = False
                else:
                    item.stale = True

    def flush_all(self):
        with self.event_queue.mutex:
            for item in self.event_queue.queue:
                item.stale = True
