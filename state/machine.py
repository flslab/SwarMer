import random
import time

import numpy as np
import threading
from message import Message, MessageTypes
from config import Config
from test_config import TestConfig
from .types import StateTypes
from worker.network import PrioritizedItem
from itertools import combinations
from utils import write_json, dict_hash


class StateMachine:
    def __init__(self, context, sock, metrics, event_queue):
        self.state = None
        self.context = context
        self.metrics = metrics
        self.sock = sock
        self.timer_single = None
        self.timer_failure = None
        self.timer_break_check = None
        self.event_queue = event_queue
        self.last_neighbors_hash = None
        self.eta = TestConfig.ETA
        self.knn = self.context.sorted_neighbors[:self.eta]
        self.is_neighbors_processed = False
        self.solution_eta_idx = -1
        self.max_eta_idx = -1
        self.handled_failure = dict()

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
        dur, dest = self.context.deploy()
        # threading.Timer(dur, self.put_state_in_q, (MessageTypes.MOVE, (dest,))).start()
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
        # stop_msg = Message(MessageTypes.STOP).to_all()
        # self.broadcast(stop_msg)
        self.cancel_timers()

        # print(self.metrics.get_final_report_())

        if not Config.DEBUG:
            write_json(self.context.fid, self.context.metrics.get_final_report_(), self.metrics.results_directory,
                       False)

        # if len(self.get_c()):
        #     # self.context.set_pair(self.get_m().el)
        #     print(f"{self.context.fid} is paired with {self.get_c()} w={self.get_w()} eta={self.eta}")
        #
        # else:
        #     # self.context.set_pair(self.context.el)
        #     print(f"{self.context.fid} is single eta={self.eta}")

        # if self.context.fid in [2, 4, 8]:
        #     with open(f"results/{self.context.fid}.txt", "w") as f:
        #         f.write("time type from to w m\n")
        #         for i in self.context.history.merge_lists():
        #             f.write(f"{str(i)}\n")
            # print(self.context.history.merge_lists())

    def vns_shake(self, c, d):
        u = set(random.sample(c, d))
        n = list(set(self.context.neighbors.keys()) - set(c))
        if len(n) >= len(u):
            u_star = set(random.sample(n, len(u)))
            return tuple((set(c) - u) | u_star)
        return c

    def vns_local_search(self, c):
        for u in c:
            for u_star in list(set(self.context.neighbors.keys()) - set(c)):
                c_prime = tuple((set(c) - {u}) | {u_star})
                if self.attr_v(c_prime) > self.attr_v(c):
                    return c_prime
        return c

    def heuristic_vns(self, c_opt):
        if len(self.context.neighbors.keys()) < self.context.k - 1:
            return (), -1

        start_time = time.time()

        if not len(c_opt):
            c_opt = tuple(random.sample(self.context.neighbors.keys(), self.context.k - 1))

        while time.time() - start_time < 5:
            d = 1
            while d < self.context.k:
                c = self.vns_shake(c_opt, d)
                c_prime = self.vns_local_search(c)
                if self.attr_v(c_prime) > self.attr_v(c_opt):
                    c_opt = c_prime
                    d = 1
                else:
                    d += 1
        return c_opt, -1

    def heuristic_rs(self, c_cur):
        if len(self.context.neighbors.keys()) < self.eta:
            return (), -1
        c = c_cur
        subset = set(c_cur) | set(random.sample(self.context.neighbors.keys(), self.eta))
        for u in combinations(subset, self.context.k - 1):
            if self.attr_v(u) > self.attr_v(c):
                c = u
        return c, -1

    def heuristic_1(self, c):
        if all(n in self.context.neighbors for n in self.knn):
            return tuple(random.sample(self.knn, self.context.k - 1)), self.eta - 1

        return (), self.eta - 1

    def heuristic_2(self, c):
        candidates = []
        last_idx = 0

        # if len(self.context.neighbors) >= self.context.k - 1:
        for i in range(len(self.context.sorted_neighbors)):
            fid = self.context.sorted_neighbors[i]
            if fid in self.context.neighbors:
                c_n = self.context.neighbors[fid].c
                if len(c_n):
                    if self.context.fid in c_n:
                        candidates.append(fid)
                    else:
                        for n in c_n:
                            new_c = tuple(nc for nc in c_n if nc != n) + (fid,)
                            if all(nc in self.context.neighbors for nc in new_c):
                                if self.attr_v(new_c) > self.attr_v(c):
                                    candidates.append(fid)
                                    break
                else:
                    candidates.append(fid)

            if len(candidates) == self.context.k - 1:
                last_idx = i
                break

        # if len(self.context.neighbors) >= self.context.k - 1:
        #     if all(n in self.context.neighbors for n in self.knn):
        #         return tuple(random.sample(self.knn, self.context.k - 1))
        # if len(candidates) >= self.context.k - 1:
        #     return tuple(random.sample(candidates, self.context.k - 1))
        if len(candidates) == self.context.k - 1:
            return tuple(candidates), last_idx
        return (), last_idx

    def enter_single_state_with_heuristic(self):
        c = ()
        if self.is_proper_v(self.get_c()):
            c = self.get_c()

        n_hash = dict_hash(self.context.fid_to_w)
        if n_hash != self.last_neighbors_hash:
            self.last_neighbors_hash = n_hash

            for n in self.context.neighbors.values():
                if self.context.fid in n.c:
                    new_c = tuple(nc for nc in n.c if nc != self.context.fid) + (n.fid,)
                    if all(nc in self.context.neighbors for nc in new_c):
                        if self.attr_v(new_c) > self.attr_v(c):
                            c = new_c
            if TestConfig.H == 1:
                c_prime, last_idx = self.heuristic_1(c)
            elif TestConfig.H == 2:
                c_prime, last_idx = self.heuristic_2(c)
            elif TestConfig.H == 'vns':
                c_prime, last_idx = self.heuristic_vns(c)
            elif TestConfig.H == 'rs':
                c_prime, last_idx = self.heuristic_rs(c)
            self.max_eta_idx = max(self.max_eta_idx, last_idx)
            if self.attr_v(c_prime) > self.attr_v(c):
                c = c_prime
                self.solution_eta_idx = last_idx

            self.set_pair(c)

            discover_msg = Message(MessageTypes.DISCOVER).to_all()
            self.broadcast(discover_msg)

    def enter_single_state(self):
        c = ()
        # n_hash = hash(str([self.context.fid_to_w[n] for n in self.knn if n in self.context.fid_to_w]))
        n_hash = dict_hash(self.context.fid_to_w)

        if n_hash != self.last_neighbors_hash:
            self.last_neighbors_hash = n_hash
            self.knn = self.context.sorted_neighbors[:self.eta]
            # if len(self.context.neighbors) >= self.context.k - 1:
            if all(n in self.context.neighbors for n in self.knn):
                for u in combinations(self.knn, self.context.k - 1):
                    attr_v_u = self.attr_v(u)
                    attr_v_c = self.attr_v(c)
                    if attr_v_u > attr_v_c:
                        c = u
                self.set_pair(c)
                self.is_neighbors_processed = True
        elif self.is_neighbors_processed:
            self.eta += 1
            self.is_neighbors_processed = False
        # else:
        #     if Config.MAX_NEIGHBORS:
        #         if len(self.context.neighbors) < Config.MAX_NEIGHBORS:
        #             self.context.increment_range()
        #     else:
        #         self.context.increment_range()
        #     self.heard = False
            # print(self.context.radio_range)

        discover_msg = Message(MessageTypes.DISCOVER).to_all()
        self.broadcast(discover_msg)

    def fail(self, msg):
        self.put_state_in_q(MessageTypes.STOP)
        self.context.metrics.log_failure_time(time.time(), self.context.is_standby)
        self.send_failure_notification()

    def assign_new_standby(self, msg):
        if not self.context.is_standby:
            self.context.standby_id = msg.args[0]
            self.context.metrics.log_standby_id(time.time(), self.context.standby_id)

    def replace_failed_fls(self, msg):
        self.context.is_standby = False
        c = self.context.group_ids
        self.context.group_ids = (c - {msg.fid}) | {self.context.fid}
        v = msg.el - self.context.el
        timestamp, dur, dest = self.context.move(v)
        # threading.Timer(dur, self.put_state_in_q, (MessageTypes.MOVE, (dest,))).start()
        self.context.log_replacement(timestamp, dur, msg.fid, False, self.context.group_ids, msg.el)
        # print(f"_ {self.context.fid} replaced {msg.fid} in group {msg.swarm_id}
        # new group is {self.context.group_ids}")

    def handle_failure_notification(self, msg):
        if self.context.is_standby:
            self.replace_failed_fls(msg)
        elif msg.fid not in self.handled_failure:
            timestamp = time.time()
            if msg.fid != self.context.standby_id and self.context.standby_id is not None:
                c = self.context.group_ids
                self.context.group_ids = (c - {msg.fid}) | {self.context.standby_id}
                self.context.metrics.log_group_members(timestamp, self.context.group_ids)
            self.context.standby_id = None
            self.context.metrics.log_standby_id(timestamp, None)
        self.handled_failure[msg.fid] = True

    def send_failure_notification(self):
        msg_to_group = Message(MessageTypes.FAILURE_NOTIFICATION).to_swarm(self.context)
        msg_to_server = Message(MessageTypes.FAILURE_NOTIFICATION)
        self.broadcast(msg_to_group)
        self.send_to_server(msg_to_server)

    def set_timer_to_fail(self):
        self.timer_failure = threading.Timer(
            random.random() * Config.FAILURE_TIMEOUT, self.put_state_in_q, (MessageTypes.SHOULD_FAIL,))
        self.timer_failure.start()

    def handle_move(self, msg):
        self.context.set_el(msg.args[0])

    def enter(self, state):
        if self.timer_single is not None:
            self.timer_single.cancel()
            self.timer_single = None

        self.leave(self.state)
        self.state = state

        if self.state == StateTypes.SINGLE:
            self.set_timer_to_fail()

    def reenter(self, state):
        self.enter(state)

    def put_state_in_q(self, event, args=()):
        msg = Message(event, args=args).to_fls(self.context)
        item = PrioritizedItem(1, msg, False)
        self.event_queue.put(item)

    def leave(self, state):
        pass

    def drive_failure_handling(self, msg):
        event = msg.type

        if event == MessageTypes.STOP:
            self.handle_stop(msg)
        elif event == MessageTypes.SHOULD_FAIL:
            self.fail(msg)
        elif event == MessageTypes.FAILURE_NOTIFICATION:
            self.handle_failure_notification(msg)
        elif event == MessageTypes.ASSIGN_STANDBY:
            self.assign_new_standby(msg)
        # elif event == MessageTypes.MOVE:
        #     self.handle_move(msg)

    def drive(self, msg):
        self.drive_failure_handling(msg)
        # event = msg.type
        # self.context.update_neighbor(msg)
        #
        # if event == MessageTypes.DISCOVER:
        #     self.handle_discover(msg)
        # elif event == MessageTypes.STOP:
        #     self.handle_stop(msg)
        # elif event == MessageTypes.REENTER_SINGLE_STATE:
        #     if self.state == StateTypes.SINGLE:
        #         self.reenter(StateTypes.SINGLE)
        # elif event == MessageTypes.SHOULD_FAIL:
        #     self.fail(msg)
        # elif event == MessageTypes.FAILURE_NOTIFICATION:
        #     self.replace_failed_fls(msg)

    def broadcast(self, msg):
        msg.from_fls(self.context)
        length = self.sock.broadcast(msg)
        self.context.log_sent_message(msg, length)

    def send_to_server(self, msg):
        msg.from_fls(self.context).to_server(self.context.sid)
        length = self.sock.broadcast(msg)
        self.context.log_sent_message(msg, length)

    def start_timers(self):
        pass

    def cancel_timers(self):
        if self.timer_single is not None:
            self.timer_single.cancel()
            self.timer_single = None
        if self.timer_failure is not None:
            self.timer_failure.cancel()
            self.timer_failure = None
