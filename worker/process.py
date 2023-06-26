import multiprocessing
import queue

import state
from .network import NetworkThread
from .handler import HandlerThread
from .worker_socket import WorkerSocket
from .context import WorkerContext
from .history import History
from .metrics import Metrics


class WorkerProcess(multiprocessing.Process):
    def __init__(self, count, process_id, gtl, el, shared_el, results_directory, k, sorted_neighbors, fid_to_dist,
                 start_time, is_standby=False, group_ids=None, standby_id=0, sid=0, group_id=None):
        super(WorkerProcess, self).__init__()
        self.history = History(4)
        self.metrics = Metrics(self.history, results_directory, start_time)
        self.context = WorkerContext(
            count, process_id, gtl, el, shared_el, self.metrics, k, sorted_neighbors,
            fid_to_dist, is_standby, group_ids, standby_id, sid, group_id)
        self.sock = WorkerSocket()

    def run(self):
        event_queue = queue.Queue()
        state_machine = state.StateMachine(self.context, self.sock, self.metrics, event_queue)

        network_thread = NetworkThread(event_queue, self.context, self.sock)
        handler_thread = HandlerThread(event_queue, state_machine, self.context)
        network_thread.start()
        handler_thread.start()

        handler_thread.join()
        network_thread.stop()
        network_thread.join()
        self.sock.close()
        while not event_queue.empty():
            try:
                event_queue.get(False)
            except queue.Empty:
                continue
            event_queue.task_done()
