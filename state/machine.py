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
        self.w = -1
        self.m = None
        self.delta = 0.01
        self.max_delta = 0.1
        self.req_accept = False
        self.verified = False

    @staticmethod
    def get_w(u, v):
        return 1 / np.linalg.norm(u.el - v.el)

    def double_delta(self):
        new_delta = self.delta * 2
        if new_delta <= self.max_delta:
            self.delta = new_delta

    def start(self):
        self.context.deploy()
        self.enter(StateTypes.SINGLE)
        self.start_timers()

    def clear_group(self):
        self.m = None
        self.w = -1

    def confirm_group(self):
        self.verified = True
        print(f"{self.context.fid} matched to {self.m.fid}, w={self.w}")

    def set_group(self, w, m):
        self.w = w
        self.m = m

    def handle_init(self, msg):
        sender_w = msg.args[0]
        sender_m = msg.args[1]
        w_to_sender = StateMachine.get_w(self.context, msg)
        if self.m is not None:
            m = self.m.fid
        else:
            m = -1

        # xmitter_wv > -1 and xmitter_wv == W_To_Xmitter and Self.FID > xmitter_mv
        if sender_w > -1 and sender_w == w_to_sender and self.context.fid > sender_m:
            self.clear_group()
        # xmitter_wv > W_To_Xmitter & & mv == Xmitter & & xmitter_mv != Self.FID
        if sender_w > w_to_sender and m == msg.fid and sender_m != self.context.fid:
            self.clear_group()
        # mv == Xmitter_mv & & Wv == Xmitter.wv & & verified == true
        if self.context.fid == sender_m and m == msg.fid and self.w == sender_w and self.verified is True:
            self.double_delta()
        # mv == Xmitter_mv & & Wv == Xmitter.wv & & verified == false & & W_To_Xmitter == Wv
        if self.context.fid == sender_m and m == msg.fid and self.w == sender_w and self.verified is False and\
                w_to_sender == self.w:
            self.confirm_group()
        # W_To_Xmitter > Wv & & W_To_Xmitter > xmitter_wv & & (mv == -1 | | Self.FID <= xmitter_mv
        if w_to_sender > self.w and w_to_sender > sender_w and (m == -1 or self.context.fid <= sender_m):
            self.set_group(w_to_sender, msg)

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

    def enter_single_state(self):
        if self.m is not None:
            m = self.m.fid
        else:
            m = -1
        discover_msg = Message(MessageTypes.INIT, args=(self.w, m)).to_all()
        self.broadcast(discover_msg)

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

        self.timer_single = threading.Timer(self.delta, self.reenter, (StateTypes.SINGLE,))
        self.timer_single.start()

    def reenter(self, state):
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
        elif event == MessageTypes.STOP:
            self.handle_stop(msg)
        elif event == MessageTypes.THAW:
            self.handle_thaw(msg)

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
