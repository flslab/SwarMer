import socket
import pickle
import threading
import time

import stop
from config import Config
from constants import Constants
import worker
from utils import logger


class SecondaryNode:
    def __init__(self):
        self.sock = None
        self.start_time = 0
        self.dir_meta = ''
        self.processes = dict()
        self.should_stop = False
        self.failure_handler_thread = None

    def _connect_to_primary(self):
        logger.info("Connecting to the primary node")

        self.sock = socket.socket()
        while True:
            try:
                self.sock.connect(Constants.SERVER_ADDRESS)
            except OSError:
                time.sleep(10)
                continue
            break

    def _wait_for_start_command(self):
        logger.info("Waiting for the start command from the primary node")

        start_cmd = self.sock.recv(1024)
        self.start_time, self.dir_meta = pickle.loads(start_cmd)

    def _handle_deployments(self):
        while True:
            msg = pickle.loads(self.sock.recv(1024))

            if not msg:
                break
            else:
                p = worker.WorkerProcess(start_time=self.start_time, dir_meta=self.dir_meta, **msg)
                p.start()
                self.processes[msg["fid"]] = p

    def _handle_failures(self):
        # to join the processes of failed FLSs
        error_handling_socket = worker.WorkerSocket()
        error_handling_socket.sock.settimeout(1)
        while self.should_stop:
            try:
                msg, _ = error_handling_socket.receive()
            except socket.timeout:
                continue

            if msg.fid in self.processes:
                self.processes.pop(msg.fid).join()

    def _start_failure_handler_thread(self):
        self.failure_handler_thread = threading.Thread(target=self._handle_failures)
        self.failure_handler_thread.start()

    def _stop_failure_handler_thread(self):
        self.should_stop = True
        self.failure_handler_thread.join()

    def _ack_primary_node(self):
        self.sock.sendall(pickle.dumps(True))

    def _stop_processes(self):
        logger.info("Stopping FLS processes")

        stop.stop_all()

        for p in self.processes.values():
            if p.is_alive():
                p.join(Config.PROCESS_JOIN_TIMEOUT)

        for p in self.processes.values():
            if p.is_alive():
                p.terminate()

    def start_node(self):
        self._connect_to_primary()
        self._wait_for_start_command()
        self._handle_deployments()

    def stop_node(self):
        self._stop_failure_handler_thread()
        self._ack_primary_node()
        self._stop_processes()


if __name__ == '__main__':
    node = SecondaryNode()
    node.start_node()
    node.stop_node()
