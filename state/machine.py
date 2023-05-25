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
        self.timer_break_check = None
        self.req_accept = False
        self.event_queue = event_queue
        self.break_check = dict()

    def get_w(self):
        return self.context.w

    def get_m_fid(self):
        return -1 if self.context.m is None else self.context.m.fid

    def get_m(self):
        return self.context.m

    def set_w(self, w):
        self.context.w = w

    def set_m(self, m):
        self.context.m = m

    def compute_w_v(self, u):
        return 1 / np.linalg.norm(self.context.el - u.el)

    def start(self):
        self.context.deploy()
        self.enter(StateTypes.SINGLE)
        self.start_timers()

    def handle_discover(self, msg):
        new_w = self.compute_w_v(msg)
        current_w = self.get_w()
        sender_w = msg.w
        if new_w > current_w and new_w > sender_w:
            # if self.get_m_fid() > 0:
            #     print(f"fid {self.context.fid} accepted {msg.fid} and broke up with {self.get_m_fid()}."
            #           f"(current_w={current_w}, new_w={new_w}).")
            # else:
            #     print(f"fid {self.context.fid} accepted {msg.fid}."
            #           f"(current_w={current_w}, new_w={new_w}).")
            self.send_break_msg(self.get_m())
            self.set_pair(msg)
            self.send_accept_msg(msg, (sender_w, new_w))
            self.enter(StateTypes.PAIRED)

    def handle_accept(self, msg):
        current_w = self.get_w()
        new_w = self.compute_w_v(msg)
        sender_w = msg.w

        if self.get_m_fid() == msg.fid:
            return

        if new_w <= current_w:
            self.send_break_msg(msg)
            # print(f"fid {self.context.fid} broke up with {msg.fid}.")
        else:
            # if self.get_m_fid() > 0:
            #     print(f"fid {self.context.fid} accepted {msg.fid} and broke up with {self.get_m_fid()}"
            #           f"(current_w={current_w}, new_w={new_w}).")
            # else:
            #     print(f"fid {self.context.fid} accepted {msg.fid}"
            #           f"(current_w={current_w}, new_w={new_w}).")
            self.req_accept = True
            self.send_break_msg(self.get_m())
            self.set_pair(msg)
            self.enter(StateTypes.PAIRED)

    def send_break_msg(self, ctx):
        if ctx is not None:
            self.break_check[ctx.fid] = ctx
            break_msg = Message(MessageTypes.BREAK).to_fls(ctx)
            self.broadcast(break_msg)

            if Config.ENABLE_BREAK_ACK:
                self.start_break_check_timer()

    def start_break_check_timer(self):
        if self.timer_break_check is None:
            self.timer_break_check = threading.Timer(
                Config.STATE_TIMEOUT, self.put_state_in_q, (MessageTypes.SEND_BREAK,))
            self.timer_break_check.start()

    def send_break_msgs(self):
        if len(self.break_check):
            for m in self.break_check.values():
                break_msg = Message(MessageTypes.BREAK).to_fls(m)
                self.broadcast(break_msg)

            if Config.ENABLE_BREAK_ACK:
                self.start_break_check_timer()
        else:
            self.timer_break_check = None

    def send_accept_msg(self, ctx, args):
        accept_msg = Message(MessageTypes.ACCEPT, args=args).to_fls(ctx)
        self.broadcast(accept_msg)

    def set_pair(self, m):
        self.set_m(m)
        self.set_w(self.compute_w_v(m))

    def handle_stop(self, msg):
        self.cancel_timers()
        if self.get_m() is not None:
            self.context.set_pair(self.get_m().el)
            print(f"{self.context.fid} is paired with {self.get_m_fid()} w={self.get_w()}")

        else:
            self.context.set_pair(self.context.el)
            print(f"{self.context.fid} is single")

        # if self.context.fid in [2, 4, 8]:
        #     with open(f"results/{self.context.fid}.txt", "w") as f:
        #         f.write("time type from to w m\n")
        #         for i in self.context.history.merge_lists():
        #             f.write(f"{str(i)}\n")
            # print(self.context.history.merge_lists())

    def handle_break(self, msg):
        if msg.fid == self.get_m_fid():
            # print(f"_fid {self.context.fid} broke up with {msg.fid}")
            self.set_w(-1)
            self.set_m(None)
            if Config.ENABLE_BREAK_ACK:
                break_ack_msg = Message(MessageTypes.BREAK_ACK).to_fls(msg)
                self.broadcast(break_ack_msg)
            self.enter(StateTypes.SINGLE)

    def handle_break_ack(self, msg):
        # self.break_check.remove(msg.fid)
        if msg.fid in self.break_check:
            self.break_check.pop(msg.fid)

    def enter_single_state(self):
        self.context.set_single()
        if not self.req_accept:
            self.context.increment_range()

        self.req_accept = False
        discover_msg = Message(MessageTypes.DISCOVER).to_all()
        self.broadcast(discover_msg)

    def enter_paired_state(self):
        self.context.set_paired()
        # m = -1 if self.m is None else self.m.fid
        # discover_msg = Message(MessageTypes.DISCOVER, args=(self.get_w(), m)).to_fls(self.m)
        # self.broadcast(discover_msg)
        # print(f"{self.context.fid} matched to {self.m.fid}, w={self.get_w()}")

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
        self.context.update_neighbor(msg)

        if event == MessageTypes.DISCOVER:
            # if self.state == StateTypes.SINGLE:
            self.handle_discover(msg)
        elif event == MessageTypes.ACCEPT:
            self.handle_accept(msg)
        elif event == MessageTypes.STOP:
            self.handle_stop(msg)
        elif event == MessageTypes.BREAK:
            self.handle_break(msg)
        elif event == MessageTypes.BREAK_ACK:
            self.handle_break_ack(msg)
        elif event == MessageTypes.REENTER_SINGLE_STATE:
            if self.state == StateTypes.SINGLE:
                self.reenter(StateTypes.SINGLE)
        elif event == MessageTypes.SEND_BREAK:
            self.send_break_msgs()

    def broadcast(self, msg):
        msg.from_fls(self.context)
        length = self.sock.broadcast(msg)
        self.context.log_sent_message(msg, length)

    def send_to_server(self, msg):
        msg.from_fls(self.context).to_server()
        self.sock.send_to_server(msg)

    def start_timers(self):
        pass

    def cancel_timers(self):
        if self.timer_single is not None:
            self.timer_single.cancel()
            self.timer_single = None
