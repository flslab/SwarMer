import numpy as np
import threading
from message import Message, MessageTypes
from config import Config
from .types import StateTypes
from worker.network import PrioritizedItem


class StateMachine:
    def __init__(self, context, sock, metrics, event_queue):
        self.state = None
        self.context = context
        self.metrics = metrics
        self.sock = sock
        self.timer_single = None
        self.w = 0
        self.m = None
        self.req_accept = False
        self.event_queue = event_queue

    def compute_w_v(self, u):
        return 1 / np.linalg.norm(self.context.el - u.el)

    def start(self):
        self.context.deploy()
        self.enter(StateTypes.SINGLE)
        self.start_timers()

    def handle_discover(self, msg):
        new_w = self.compute_w_v(msg)
        sender_w = msg.args[0]
        if new_w > self.w and new_w > sender_w:
            self.send_break_msg(self.m)
            self.set_pair(msg)
            self.send_accept_msg(msg, (sender_w, new_w))
            self.enter(StateTypes.PAIRED)

    def handle_accept(self, msg):
        old_w = msg.args[0]
        if old_w != self.w:
            self.send_break_msg(msg)
        else:
            self.req_accept = True
            self.send_break_msg(self.m)
            self.set_pair(msg)
            self.enter(StateTypes.PAIRED)

    def send_break_msg(self, ctx):
        if ctx is not None:
            break_msg = Message(MessageTypes.BREAK).to_fls(ctx)
            self.broadcast(break_msg)

    def send_accept_msg(self, ctx, args):
        accept_msg = Message(MessageTypes.ACCEPT, args=args).to_fls(ctx)
        self.broadcast(accept_msg)

    def set_pair(self, m):
        self.m = m
        self.w = self.compute_w_v(m)

    def handle_stop(self, msg):
        self.cancel_timers()
        if self.m is not None:
            self.context.set_pair(self.m.el)
            print(f"{self.context.fid} is paired with {self.m.fid} w={self.w}")

        else:
            self.context.set_pair(self.context.el)
            print(f"{self.context.fid} is single")

    def handle_break(self, msg):
        if self.m is not None and msg.fid == self.m.fid:
            self.w = 0
            self.m = None
            self.enter(StateTypes.SINGLE)

    def enter_single_state(self):
        self.context.set_single()
        if not self.req_accept:
            self.context.increment_range()

        self.req_accept = False
        m = -1 if self.m is None else self.m.fid
        discover_msg = Message(MessageTypes.DISCOVER, args=(self.w, m)).to_all()
        self.broadcast(discover_msg)

    def enter_paired_state(self):
        self.context.set_paired()
        # m = -1 if self.m is None else self.m.fid
        # discover_msg = Message(MessageTypes.DISCOVER, args=(self.w, m)).to_fls(self.m)
        # self.broadcast(discover_msg)
        # print(f"{self.context.fid} matched to {self.m.fid}, w={self.w}")

    def leave_single_state(self):
        pass

    def leave_paired_state(self):
        pass
        # print(f"{self.context.fid} broke")

    def enter(self, state):
        if self.timer_single is not None:
            self.timer_single.cancel()
            self.timer_single = None

        self.leave(self.state)
        self.state = state

        if self.state == StateTypes.SINGLE:
            self.enter_single_state()
        elif self.state == StateTypes.PAIRED:
            self.enter_paired_state()

        if self.state == StateTypes.SINGLE:
            # rand_time = 0.1 + np.random.random() * Config.STATE_TIMEOUT
            self.timer_single = threading.Timer(
                Config.STATE_TIMEOUT, self.put_state_in_q, (MessageTypes.REENTER_SINGLE_STATE,))
            self.timer_single.start()

    def reenter(self, state):
        self.enter(state)

    def put_state_in_q(self, event):
        msg = Message(event).to_fls(self.context)
        item = PrioritizedItem(1, msg, False)
        self.event_queue.put(item)

    def leave(self, state):
        if state == StateTypes.SINGLE:
            self.leave_single_state()
        elif state == StateTypes.PAIRED:
            self.leave_paired_state()

    def drive(self, msg):
        event = msg.type
        # self.context.update_neighbor(msg)

        if event == MessageTypes.DISCOVER:
            # if self.state == StateTypes.SINGLE:
            self.handle_discover(msg)
        elif event == MessageTypes.ACCEPT:
            self.handle_accept(msg)
        elif event == MessageTypes.STOP:
            self.handle_stop(msg)
        elif event == MessageTypes.BREAK:
            self.handle_break(msg)
        elif event == MessageTypes.REENTER_SINGLE_STATE:
            if self.state == StateTypes.SINGLE:
                self.reenter(StateTypes.SINGLE)

    def broadcast(self, msg):
        msg.from_fls(self.context)
        length = self.sock.broadcast(msg)
        self.context.log_sent_message(msg.type, length)

    def send_to_server(self, msg):
        msg.from_fls(self.context).to_server()
        self.sock.send_to_server(msg)

    def start_timers(self):
        pass

    def cancel_timers(self):
        if self.timer_single is not None:
            self.timer_single.cancel()
            self.timer_single = None
