import queue
import socket
import random
import threading
import sys
import time
import os
from abc import ABC, abstractmethod
import numpy as np

from dispatcher import Dispatcher
from test_config import TestConfig
from config import Config
from constants import Constants
from message import Message, MessageTypes
import worker
import utils
from utils import logger
from utils.file import read_cliques_xlsx
from utils.socket import send_msg


CONFIG = TestConfig if TestConfig.ENABLED else Config


def join_config_properties(conf, props):
    return "_".join(
        f"{k[1] if isinstance(k, tuple) else k}{getattr(conf, k[0] if isinstance(k, tuple) else k)}" for k in
        props)


class DispatchPolicy(ABC):
    @abstractmethod
    def assign(self, **kwargs):
        pass


class PoDPolicy(DispatchPolicy):
    def assign(self, **kwargs):
        ds = kwargs["dispatchers"]

        if len(ds) == 1:
            return ds[0]
        elif len(ds) == 2:
            if ds[0].q.qsize() < ds[1].q.qsize():
                return ds[0]
            return ds[1]

        rand_ds = random.sample(ds, 2)
        if rand_ds[0].q.qsize() < rand_ds[1].q.qsize():
            return rand_ds[0]
        return rand_ds[1]


class RRPolicy(DispatchPolicy):
    def assign(self, **kwargs):
        ds = kwargs["dispatchers"]
        pid = kwargs["pid"]

        return ds[pid % len(ds)]


class ShortestDistancePolicy(DispatchPolicy):
    def assign(self, **kwargs):
        ds = kwargs["dispatchers"]
        coord = kwargs["coord"]

        dispatcher_coords = np.stack([d.coord for d in ds])
        return ds[np.argmin(np.linalg.norm(dispatcher_coords - coord, axis=1))]


class PrimaryNode:
    def __init__(self, N, name):
        self.N = N  # number of secondary servers
        self.name = name
        self.sock = None
        self.client_sockets = []
        self.result_name = None
        self.dir_experiment = None
        self.dir_meta = None
        self.dir_figure = None
        self.start_time = 0
        self.end_time = 0
        self.dispatchers_coords = []
        self.dispatchers = []
        self.groups = []
        self.radio_ranges = []
        self.group_members = {}
        self.group_standby_id = {}
        self.group_standby_coord = {}
        self.group_radio_range = {}
        self.pid = 0
        self.dispatch_policy = PoDPolicy()
        self.num_handled_failures = 0

    def _create_server_socket(self):
        # Experimental artifact to gather theoretical stats for scientific publications.
        self.sock = socket.socket()

    def _bind_server_socket(self):
        logger.info(f"Binding primary node to {Constants.SERVER_ADDRESS}")

        while True:
            try:
                self.sock.bind(Constants.SERVER_ADDRESS)
            except OSError:
                time.sleep(10)
                continue
            break

    def _listen_to_secondary_nodes(self):
        logger.info("Waiting for secondary nodes to connect")

        self.sock.listen(N)
        for i in range(N):
            client, address = self.sock.accept()
            logger.debug(address)
            self.client_sockets.append(client)

    def _setup_results_directory(self):
        if len(CONFIG.FILE_NAME_KEYS):
            result_config = join_config_properties(CONFIG, CONFIG.FILE_NAME_KEYS)
        else:
            result_config = self.name
        self.result_name = f"{Config.SHAPE}_{result_config}"

        if len(CONFIG.DIR_KEYS):
            group_config = join_config_properties(CONFIG, CONFIG.DIR_KEYS)
        else:
            group_config = ""

        self.dir_experiment = os.path.join(Config.RESULTS_PATH, Config.SHAPE, group_config)
        self.dir_meta = os.path.join(self.dir_experiment, self.result_name)
        self.dir_figure = os.path.join(self.dir_experiment, 'figures')

        if not os.path.exists(self.dir_meta):
            os.makedirs(os.path.join(self.dir_meta, 'json'), exist_ok=True)
        if not os.path.exists(self.dir_figure):
            os.makedirs(self.dir_figure, exist_ok=True)

    def _define_dispatcher_coords(self):
        l = 50
        w = 100
        if Config.DISPATCHERS == 1:
            self.dispatchers_coords = np.array([[l / 2, w / 2, 0]])
        elif Config.DISPATCHERS == 3:
            self.dispatchers_coords = np.array([[l / 2, w / 2, 0], [l, w, 0], [0, 0, 0]])
        elif Config.DISPATCHERS == 5:
            self.dispatchers_coords = np.array([[l / 2, w / 2, 0], [l, 0, 0], [0, w, 0], [l, w, 0], [0, 0, 0]])

    def _start_dispatchers(self):
        logger.info(f"Starting {Config.DISPATCHERS} dispatchers")

        for coord in self.dispatchers_coords:
            q = queue.Queue()
            d = Dispatcher(q, Config.DISPATCH_RATE, coord)
            self.dispatchers.append(d)
            d.start()

    def _send_msg_to_all_nodes(self, msg):
        for nid in range(len(self.client_sockets)):
            self._send_msg_to_node(nid, msg)

    def _send_msg_to_node(self, nid, msg):
        send_msg(self.client_sockets[nid], msg)

    def _receive_msg_from_node(self, nid):
        return self.client_sockets[nid].recv(1024)

    def _start_secondary_nodes(self):
        logger.info(f"Starting {N} secondary nodes")
        self.start_time = time.time()
        self._send_msg_to_all_nodes((self.start_time, self.dir_meta))

    def _read_groups(self):
        self.groups, self.radio_ranges = read_cliques_xlsx(os.path.join(self.dir_experiment, f'{Config.INPUT}.xlsx'))
        # self.groups = self.groups[:2]
        # self.radio_ranges = self.radio_ranges[:2]

        single_members = []
        single_indexes = []
        max_dist_singles = 0
        for k in range(len(self.groups)):
            if self.groups[k].shape[0] == 1:
                if len(single_indexes):
                    max_dist_n = np.max(np.linalg.norm(np.stack(single_members) - self.groups[k][0], axis=1))
                    max_dist_singles = max(max_dist_singles, max_dist_n)
                single_members.append(self.groups[k][0])
                single_indexes.append(k)

        # remove single nodes from groups
        for k in reversed(single_indexes):
            self.groups.pop(k)
            self.radio_ranges.pop(k)

        # add single nodes as one group to the groups
        if len(single_members):
            self.groups.append(np.stack(single_members))
            self.radio_ranges.append(max_dist_singles)

    def _assign_dispatcher(self, properties):
        return self.dispatch_policy.assign(dispatchers=self.dispatchers, **properties)

    def _deploy_fls(self, properties):
        nid = properties["fid"] % self.N
        dispatcher = self._assign_dispatcher(properties)
        if properties["el"] is None:
            properties["el"] = dispatcher.coord
        dispatcher.q.put(lambda: self._send_msg_to_node(nid, properties))

    def _deploy_initial_formation(self):
        logger.info("Deploying FLSs")
        for i in range(len(self.groups)):
            group = self.groups[i]
            group_id = self.pid + 1
            self.group_radio_range[group_id] = self.radio_ranges[i]
            self.group_standby_coord[group_id] = None
            self.group_standby_id[group_id] = group_id + len(group)

            if Config.K:
                member_count = group.shape[0]
                sum_x = np.sum(group[:, 0])
                sum_y = np.sum(group[:, 1])
                sum_z = np.sum(group[:, 2])
                stand_by_coord = np.array([sum_x / member_count, sum_y / member_count, sum_z / member_count])
                self.group_standby_coord[group_id] = stand_by_coord

            # deploy group members
            for member_coord in group:
                self.pid += 1
                fls = {
                    "fid": self.pid,
                    "el": member_coord, "gtl": member_coord,
                    "radio_range": self.group_radio_range[group_id],
                    "standby_id": self.group_standby_id[group_id], "group_id": group_id,
                }
                self._deploy_fls(fls)

            # deploy standby
            if Config.K:
                self.pid += 1
                fls = {
                    "fid": self.pid,
                    "el": self.group_standby_coord[group_id], "gtl": self.group_standby_coord[group_id],
                    "radio_range": self.group_radio_range[group_id],
                    "is_standby": True, "group_id": group_id,
                }
                self._deploy_fls(fls)

        logger.info(f"Assigned {self.pid} FLSs to dispatchers")

    def _handle_failures(self):
        logger.info("Started failure handler")

        failure_handling_socket = worker.WorkerSocket()
        failure_handling_socket.sock.settimeout(1)
        while time.time() - self.start_time <= Config.DURATION:
            try:
                msg, _ = failure_handling_socket.receive()
            except socket.timeout:
                continue

            if msg.dest_fid == 0:
                if msg.type == MessageTypes.REPLICA_REQUEST_HUB:
                    self.pid += 1
                    group_id = msg.swarm_id
                    failed_fid = msg.fid
                    is_illuminating = msg.args[0]

                    if is_illuminating:
                        fls = {
                            "fid": self.pid,
                            "el": None, "gtl": msg.gtl,
                            "radio_range": self.group_radio_range[group_id],
                            "standby_id": self.group_standby_id[group_id], "group_id": group_id,
                        }
                        self._deploy_fls(fls)

                    else:
                        self.group_standby_id[group_id] = self.pid

                        # dispatch the new standby fls
                        fls = {
                            "fid": self.pid,
                            "el": None, "gtl": self.group_standby_coord[group_id],
                            "radio_range": self.group_radio_range[group_id],
                            "is_standby": True, "group_id": group_id,
                        }
                        self._deploy_fls(fls)

                        # send the id of the new standby to group members
                        new_standby_msg = Message(MessageTypes.ASSIGN_STANDBY, args=(self.pid,)) \
                            .from_server().to_fls_id("*", group_id)
                        failure_handling_socket.broadcast(new_standby_msg)

                    self.num_handled_failures += 1

        self.end_time = time.time()

    def _stop_dispatchers(self):
        logger.info("Stopping dispatchers")

        for d in self.dispatchers:
            d.stop()
        for d in self.dispatchers:
            d.join()

    def _stop_secondary_nodes(self):
        logger.info("Stopping secondary nodes")

        self._send_msg_to_all_nodes(False)
        client_threads = []
        for nid in range(len(self.client_sockets)):
            t = threading.Thread(target=self._receive_msg_from_node, args=(nid,))
            t.start()
            client_threads.append(t)
        for t in client_threads:
            t.join()

    def _write_results(self):
        logger.info("Writing results")

        utils.write_csv(self.dir_meta, [["num_handled_failures", self.num_handled_failures]], 'metrics')
        utils.create_csv_from_json(self.dir_meta, os.path.join(self.dir_figure, f'{self.result_name}.jpg'))
        utils.write_configs(self.dir_meta, self.start_time)
        utils.combine_csvs(self.dir_meta, self.dir_experiment, "reli_" + self.result_name)

    def stop_experiment(self):
        logger.info("Stopping the experiment")

        self._stop_dispatchers()
        self._stop_secondary_nodes()
        self._write_results()

    def start_experiment(self):
        self._setup_results_directory()
        self._create_server_socket()
        self._bind_server_socket()
        self._listen_to_secondary_nodes()
        self._read_groups()
        self._define_dispatcher_coords()
        self._start_secondary_nodes()
        self._start_dispatchers()
        self._deploy_initial_formation()
        self._handle_failures()


if __name__ == '__main__':
    N = 1
    name = str(int(time.time()))
    if len(sys.argv) > 1:
        N = int(sys.argv[1])
        name = sys.argv[2]

    primary_node = PrimaryNode(N, name)
    primary_node.start_experiment()
    primary_node.stop_experiment()
