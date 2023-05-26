import numpy as np
import threading
from message import Message, MessageTypes
from config import Config
from .types import StateTypes
from worker.network import PrioritizedItem
from itertools import combinations
from utils import write_json


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

    def get_c(self):
        return self.context.c

    def set_w(self, w):
        self.context.w = w

    def set_c(self, c):
        self.context.c = c

    def get_w_v(self, c):
        if len(c):
            w = 0
            els = [self.context.el] + [self.context.neighbors[i].el for i in c]
            for el_i, el_j in combinations(els, 2):
                w += round(1 / np.linalg.norm(el_i - el_j), 4)
            return (round(w, 4),) + tuple(sorted((self.context.fid,) + c))
        return -1,

    def is_proper_v(self, c):
        new_w = self.get_w_v(c)
        weights = [self.context.neighbors[i].w for i in c]
        # if len(self.get_c()) == 0:
        #     print(new_w, weights)
        return all([new_w >= w for w in weights])

    def attr_v(self, c):
        return self.get_w_v(c) if self.is_proper_v(c) else (-1,)

    def start(self):
        self.context.deploy()
        self.enter(StateTypes.SINGLE)
        self.start_timers()

    def handle_discover(self, msg):
        pass

    def set_pair(self, c):
        w = self.get_w_v(c)
        # if w != self.get_w():
        self.set_c(c)
        self.set_w(w)
        self.context.set_pair()

    def handle_stop(self, msg):
        self.cancel_timers()
        min_fid = min(self.get_c() + (self.context.fid,))

        if self.context.fid == min_fid:
            dists = []
            els = [self.context.el] + [self.context.neighbors[i].el for i in self.get_c()]
            for el_i, el_j in combinations(els, 2):
                dists.append(np.linalg.norm(el_i - el_j))
            results = {
                "5 weight": self.get_w()[0],
                "0 clique members": self.get_w()[1:],
                "6 dist between each pair": dists,
                "7 coordinates": [list(el) for el in els],
                "1 min dist": min(dists),
                "2 avg dist": sum(dists)/self.context.k,
                "3 max dist": max(dists),
                "4 total dist": sum(dists)
            }
            write_json(self.context.fid, results, self.metrics.results_directory)

        # if len(self.get_c()):
        #     # self.context.set_pair(self.get_m().el)
        #     print(f"{self.context.fid} is paired with {self.get_c()} w={self.get_w()}")
        #
        # else:
        #     # self.context.set_pair(self.context.el)
        #     print(f"{self.context.fid} is single")

        # if self.context.fid in [2, 4, 8]:
        #     with open(f"results/{self.context.fid}.txt", "w") as f:
        #         f.write("time type from to w m\n")
        #         for i in self.context.history.merge_lists():
        #             f.write(f"{str(i)}\n")
            # print(self.context.history.merge_lists())

    def enter_single_state(self):
        # self.context.set_single()
        c = ()
        if len(self.context.neighbors) >= self.context.k - 1:
            for u in combinations(self.context.neighbors.keys(), self.context.k - 1):
                attr_v_u = self.attr_v(u)
                attr_v_c = self.attr_v(c)
                # print(self.context.fid, u, attr_v_u, c, attr_v_c)
                if attr_v_u > attr_v_c:
                    c = u
            self.set_pair(c)
        # if len(c) == 0:
        self.context.increment_range()
        # print(self.context.radio_range)

        discover_msg = Message(MessageTypes.DISCOVER).to_all()
        self.broadcast(discover_msg)

    def enter(self, state):
        if self.timer_single is not None:
            self.timer_single.cancel()
            self.timer_single = None

        self.leave(self.state)
        self.state = state

        if self.state == StateTypes.SINGLE:
            self.enter_single_state()

        if self.state == StateTypes.SINGLE:
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
        pass

    def drive(self, msg):
        event = msg.type
        self.context.update_neighbor(msg)

        if event == MessageTypes.DISCOVER:
            self.handle_discover(msg)
        elif event == MessageTypes.STOP:
            self.handle_stop(msg)
        elif event == MessageTypes.REENTER_SINGLE_STATE:
            if self.state == StateTypes.SINGLE:
                self.reenter(StateTypes.SINGLE)

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
