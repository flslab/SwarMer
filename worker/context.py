import time
import numpy as np
from multiprocessing import shared_memory

import velocity
from config import Config
from .metrics import MetricTypes
from .history import History


class WorkerContext:
    def __init__(self, count, fid, gtl, el, shm_name, metrics, k, sorted_neighbors, fid_to_dist):
        self.count = count
        self.fid = fid
        self.gtl = gtl
        self.el = el
        self.swarm_id = self.fid
        self.neighbors = dict()
        self.fid_to_w = dict()
        self.fid_to_dist = fid_to_dist
        self.sorted_neighbors = sorted_neighbors
        self.radio_range = Config.INITIAL_RANGE
        self.max_range = Config.MAX_RANGE
        self.size = 1
        self.anchor = None
        self.query_id = None
        self.challenge_id = None
        self.shm_name = shm_name
        self.set_swarm_id(self.fid)
        self.message_id = 0
        self.alpha = Config.DEAD_RECKONING_ANGLE / 180 * np.pi
        self.metrics = metrics
        self.w = (-1,)
        self.c = ()
        self.k = k
        self.history = History(2)

    def set_pair(self):
        if self.shm_name:
            shared_mem = shared_memory.SharedMemory(name=self.shm_name)
            shared_array = np.ndarray((self.k,), dtype=np.int32, buffer=shared_mem.buf)
            shared_array[:] = sorted([self.fid] + list(self.c))
            shared_mem.close()

    def set_single(self):
        if self.shm_name:
            shared_mem = shared_memory.SharedMemory(name=self.shm_name)
            shared_array = np.ndarray((7,), dtype=np.float64, buffer=shared_mem.buf)
            shared_array[6] = 0
            shared_mem.close()

    def set_swarm_id(self, swarm_id):
        # print(f"{self.fid}({self.swarm_id}) merged into {swarm_id}")
        self.swarm_id = swarm_id
        # if self.shm_name:
        #     shared_mem = shared_memory.SharedMemory(name=self.shm_name)
        #     shared_array = np.ndarray((5,), dtype=np.float64, buffer=shared_mem.buf)
        #     shared_array[3] = self.swarm_id
        #     shared_mem.close()
        # self.history.log(MetricTypes.SWARM_ID, self.swarm_id)

    def set_el(self, el):
        self.el = el
        # if self.shm_name:
        #     shared_mem = shared_memory.SharedMemory(name=self.shm_name)
        #     shared_array = np.ndarray((5,), dtype=np.float64, buffer=shared_mem.buf)
        #     shared_array[:3] = self.el[:]
        #     shared_mem.close()

        # self.history.log(MetricTypes.LOCATION, self.el)

    def set_query_id(self, query_id):
        self.query_id = query_id

    def set_challenge_id(self, challenge_id):
        self.challenge_id = challenge_id

    def set_anchor(self, anchor):
        self.anchor = anchor

    def set_radio_range(self, radio_range):
        self.radio_range = radio_range

    def deploy(self):
        self.move(self.gtl - self.el)
        # if self.shm_name:
        #     shared_mem = shared_memory.SharedMemory(name=self.shm_name)
        #     shared_array = np.ndarray((5,), dtype=np.float64, buffer=shared_mem.buf)
        #     shared_array[4] = 0
        #     shared_mem.close()

    def fail(self):
        self.reset_swarm()
        self.set_el(np.array([.0, .0, .0]))
        self.radio_range = Config.INITIAL_RANGE
        self.anchor = None
        self.query_id = None
        self.challenge_id = None
        self.metrics.log_sum("A5_num_failures", 1)

    def move(self, vector):
        erred_v = self.add_dead_reckoning_error(vector)
        dest = self.el + erred_v
        # self.history.log(MetricTypes.LOCATION, self.el)
        self.metrics.log_sum("A0_total_distance", np.linalg.norm(vector))
        vm = velocity.VelocityModel(self.el, dest)
        vm.solve()
        dur = vm.total_time
        self.log_wait_time(dur)

        if Config.BUSY_WAITING:
            fin_time = time.time() + dur
            while True:
                if time.time() >= fin_time:
                    break
        else:
            time.sleep(dur)

        self.set_el(dest)

    def add_dead_reckoning_error(self, vector):
        if vector[0] or vector[1]:
            i = np.array([vector[1], -vector[0], 0])
        elif vector[2]:
            i = np.array([vector[2], 0, -vector[0]])
        else:
            return vector

        if self.alpha == 0:
            return vector

        j = np.cross(vector, i)
        norm_i = np.linalg.norm(i)
        norm_j = np.linalg.norm(j)
        norm_v = np.linalg.norm(vector)
        i = i / norm_i
        j = j / norm_j
        phi = np.random.uniform(0, 2 * np.pi)
        error = np.sin(phi) * i + np.cos(phi) * j
        r = np.linalg.norm(vector) * np.tan(self.alpha)

        erred_v = vector + np.random.uniform(0, r) * error
        return norm_v * erred_v / np.linalg.norm(erred_v)

    def update_neighbor(self, ctx):
        if ctx.fid:
            self.neighbors[ctx.fid] = ctx
            self.fid_to_w[ctx.fid] = ctx.w

    def increment_range(self):
        if self.radio_range < self.max_range:
            self.set_radio_range(self.radio_range + 1)
            # logger.critical(f"{self.fid} range incremented to {self.radio_range}")
            return True
        else:
            return False

    def reset_range(self):
        self.set_radio_range(Config.INITIAL_RANGE)

    def reset_swarm(self):
        self.set_swarm_id(self.fid)

    def thaw_swarm(self):
        self.reset_swarm()
        self.reset_range()
        self.size = 1
        self.anchor = None
        self.query_id = None
        self.challenge_id = None

    def log_received_message(self, msg, length):
        meta = {"length": length}
        msg_type = msg.type
        self.history.log(MetricTypes.RECEIVED_MASSAGES, msg, meta)
        self.metrics.log_received_msg(msg_type, length)

    def log_dropped_messages(self):
        # self.history.log_sum(MetricTypes.DROPPED_MESSAGES)
        self.metrics.log_sum("A4_num_dropped_messages", 1)

    def log_sent_message(self, msg, length):
        meta = {"length": length}
        msg_type = msg.type
        self.history.log(MetricTypes.SENT_MESSAGES, msg, meta)
        self.metrics.log_sent_msg(msg_type, length)
        self.message_id += 1

    def log_wait_time(self, dur):
        # self.history.log(MetricTypes.WAITS, dur)
        self.metrics.log_sum("A1_num_moved", 1)
        self.metrics.log_sum("A1_total_wait(s)", dur)
        self.metrics.log_max("A1_max_wait(s)", dur)
        self.metrics.log_min("A1_min_wait(s)", dur)
