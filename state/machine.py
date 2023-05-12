import time

import numpy as np
import threading
from message import Message, MessageTypes
from config import Config
from .types import StateTypes


class StateMachine:
    def __init__(self, context, sock, metrics):
        self.state = None
        self.context = context
        self.metrics = metrics
        self.sock = sock
        self.timer_single = None
        self.w = 0
        self.m = None
        self.req_accept = False

    @staticmethod
    def get_w(u, v):
        return 1 / np.linalg.norm(u.el - v.el)

    def start(self):
        self.context.deploy()
        self.enter(StateTypes.SINGLE)
        self.start_timers()

    def handle_init(self, msg):
        new_w = StateMachine.get_w(self.context, msg)
        sender_w = msg.args[0]
        if new_w > self.w and new_w > sender_w:
            if self.m is not None:
                break_msg = Message(MessageTypes.BREAK).to_fls(self.m)
                self.broadcast(break_msg)

            self.m = msg
            self.w = new_w

            accept_msg = Message(MessageTypes.ACCEPT, args=(sender_w, new_w)).to_fls(msg)
            self.broadcast(accept_msg)
            self.enter(StateTypes.MARRIED)

    def handle_accept(self, msg):
        old_w = msg.args[0]
        new_w = StateMachine.get_w(self.context, msg)
        if old_w != self.w:
            break_msg = Message(MessageTypes.BREAK).to_fls(msg)
            self.broadcast(break_msg)
            return

        if new_w > self.w:
            self.req_accept = True
            if self.m is not None:
                break_msg = Message(MessageTypes.BREAK).to_fls(self.m)
                self.broadcast(break_msg)

            self.m = msg
            self.w = new_w
            self.enter(StateTypes.MARRIED)
        else:
            break_msg = Message(MessageTypes.BREAK).to_fls(msg)
            self.broadcast(break_msg)

    def handle_thaw(self, msg):
        self.cancel_timers()
        self.enter(StateTypes.SINGLE)
        self.w = 0
        self.m = None
        self.start_timers()

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
        if not self.req_accept:
            self.context.increment_range()

        self.req_accept = False
        challenge_msg = Message(MessageTypes.INIT, args=(self.w,)).to_all()
        self.broadcast(challenge_msg)

    def enter_married_state(self):
        print(f"{self.context.fid} matched to {self.m.fid}, w={self.w}")

    def leave_single_state(self):
        pass

    def leave_married_state(self):
        print(f"{self.context.fid} broke")

    def enter(self, state):
        if self.timer_single is not None:
            self.timer_single.cancel()
            self.timer_single = None

        self.leave(self.state)
        self.state = state

        if self.state == StateTypes.SINGLE:
            self.enter_single_state()
        elif self.state == StateTypes.MARRIED:
            self.enter_married_state()

        if self.state != StateTypes.MARRIED:
            rand_time = 0.1 + np.random.random() * Config.STATE_TIMEOUT
            self.timer_single = threading.Timer(rand_time, self.reenter, (StateTypes.SINGLE,))
            self.timer_single.start()

    def reenter(self, state):
        if self.state != StateTypes.MARRIED:
            self.enter(state)

    def leave(self, state):
        if state == StateTypes.SINGLE:
            self.leave_single_state()
        elif state == StateTypes.MARRIED:
            self.leave_married_state()

    def drive(self, msg):
        event = msg.type
        # self.context.update_neighbor(msg)

        if event == MessageTypes.INIT:
            self.handle_init(msg)
        elif event == MessageTypes.ACCEPT:
            self.handle_accept(msg)
        elif event == MessageTypes.STOP:
            self.handle_stop(msg)
        elif event == MessageTypes.THAW:
            self.handle_thaw(msg)

        if self.state == StateTypes.MARRIED:
            if event == MessageTypes.BREAK:
                self.handle_break(msg)

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
