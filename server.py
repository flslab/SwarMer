import socket
import pickle
import numpy as np
from multiprocessing import shared_memory
import scipy.io
import time
import os
from config import Config
from constants import Constants
from message import Message, MessageTypes
import worker
import utils
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.use('macosx')

hd_timer = None
hd_round = []
hd_time = []
should_stop = False


def set_stop():
    global should_stop
    should_stop = True
    print('will stop next round')


def compute_hd(sh_arrays, gtl):
    hd_t = utils.hausdorff_distance(np.stack(sh_arrays), gtl)
    print(f"__hd__ {hd_t}")
    return hd_t


def compute_swarm_size(sh_arrays):
    swarm_counts = {}
    for arr in sh_arrays:
        swarm_id = arr[3]
        if swarm_id in swarm_counts:
            swarm_counts[swarm_id] += 1
        else:
            swarm_counts[swarm_id] = 1
    return swarm_counts


if __name__ == '__main__':
    N = 1
    nid = 0
    experiment_name = str(int(time.time()))
    if len(sys.argv) > 1:
        N = int(sys.argv[1])
        nid = int(sys.argv[2])
        experiment_name = sys.argv[3]

    results_directory = os.path.join(Config.RESULTS_PATH, Config.SHAPE, experiment_name)
    shape_directory = os.path.join(Config.RESULTS_PATH, Config.SHAPE)
    if not os.path.exists(results_directory):
        os.makedirs(os.path.join(results_directory, 'json'), exist_ok=True)
    mat = scipy.io.loadmat(f'assets/{Config.SHAPE}.mat')
    point_cloud = mat['p']
    # point_cloud = np.array([[0, 0, 0], [5, 0, 0], [0, 20, 0], [5, 20, 0]])

    if Config.SAMPLE_SIZE != 0:
        np.random.shuffle(point_cloud)
        point_cloud = point_cloud[:Config.SAMPLE_SIZE]

    total_count = point_cloud.shape[0]
    h = np.log2(total_count)

    gtl_point_cloud = np.random.uniform(0, 5, size=(total_count, 3))
    sample = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    node_point_idx = []
    for i in range(total_count):
        if i % N == nid:
            node_point_idx.append(i)
            gtl_point_cloud[i] = np.array([point_cloud[i][0], point_cloud[i][1], point_cloud[i][2]])

    count = len(node_point_idx)
    print(count)

    processes = []
    shared_arrays = []
    shared_memories = []

    local_gtl_point_cloud = []
    try:
        for i in node_point_idx:
            shm = shared_memory.SharedMemory(create=True, size=sample.nbytes)
            shared_array = np.ndarray(sample.shape, dtype=sample.dtype, buffer=shm.buf)
            shared_array[:] = sample[:]

            shared_arrays.append(shared_array)
            shared_memories.append(shm)
            local_gtl_point_cloud.append(gtl_point_cloud[i])
            p = worker.WorkerProcess(count, i + 1, gtl_point_cloud[i], np.array([0, 0, 0]), shm.name, results_directory)
            p.start()
            processes.append(p)
    except OSError as e:
        print(e)
        for p in processes:
            p.terminate()
        for s in shared_memories:
            s.close()
            s.unlink()
        exit()

    gtl_point_cloud = local_gtl_point_cloud

    fin_message_sent = False
    final_point_cloud = np.zeros([count, 3])
    fin_processes = np.zeros(count)
    metrics = {}

    # compute_hd(shared_arrays, gtl_point_cloud)

    num_round = 0
    max_rounds = Config.NUMBER_ROUND
    round_time = [time.time()]
    swarms_metrics = []

    print('waiting for processes ...')

    ser_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ser_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    ser_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    ser_sock.settimeout(.2)

    while True:
        time.sleep(1)
        if sum([sha[6] for sha in shared_arrays]) == count:
            break

    stop_message = Message(MessageTypes.STOP).from_server().to_all()
    dumped_stop_msg = pickle.dumps(stop_message)
    ser_sock.sendto(dumped_stop_msg, Constants.BROADCAST_ADDRESS)
    ser_sock.close()
    print("done")

    time.sleep(1)
    for p in processes:
        p.join()

    for sha in shared_arrays:
        # print(sha)
        # print([sha[0], sha[3]], [sha[1], sha[4]])
        plt.plot([sha[0], sha[3]], [sha[1], sha[4]], '-o')
    plt.show()

    # utils.plot_point_cloud(np.stack(gtl_point_cloud), None)

