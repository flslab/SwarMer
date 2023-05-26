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

# mpl.use('macosx')

hd_timer = None
hd_round = []
hd_time = []
should_stop = False


def count_keys(d, k):
    if k in d:
        d[k] += 1
    else:
        d[k] = 1


def set_stop():
    global should_stop
    should_stop = True
    print('will stop next round')


if __name__ == '__main__':
    N = 1
    nid = 0
    experiment_name = str(int(time.time()))
    if len(sys.argv) > 1:
        N = int(sys.argv[1])
        nid = int(sys.argv[2])
        experiment_name = sys.argv[3]

    results_directory = os.path.join(Config.RESULTS_PATH, Config.SHAPE, experiment_name)

    if Config.READ_FROM_NPY:
        with open(f'results/{Config.READ_FROM_NPY}.npy', 'rb') as f:
            point_cloud = np.load(f)
    else:
        mat = scipy.io.loadmat(f'assets/{Config.SHAPE}.mat')
        point_cloud = mat['p']
    # point_cloud = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0],
    #                         [0, 1, 0], [1, 1, 0], [2, 1, 0], [3, 1, 0]])
    #                         [0, 2, 0], [1, 2, 0], [2, 2, 0], [3, 2, 0],
    #                         [0, 3, 0], [1, 3, 0], [2, 3, 0], [3, 3, 0]])

    if Config.SAMPLE_SIZE != 0:
        np.random.shuffle(point_cloud)
        point_cloud = point_cloud[:Config.SAMPLE_SIZE]

    total_count = point_cloud.shape[0]
    h = np.log2(total_count)

    gtl_point_cloud = np.random.uniform(0, 5, size=(total_count, 3))
    sample = np.zeros(Config.K, dtype=np.int32)

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
    # pidx = np.array(node_point_idx)
    # np.random.shuffle(pidx)
    # print(pidx)
    try:
        for i in node_point_idx:
            shm = shared_memory.SharedMemory(create=True, size=sample.nbytes)
            shared_array = np.ndarray(sample.shape, dtype=sample.dtype, buffer=shm.buf)
            shared_array[:] = sample[:]

            shared_arrays.append(shared_array)
            shared_memories.append(shm)
            local_gtl_point_cloud.append(gtl_point_cloud[i])
            p = worker.WorkerProcess(
                count, i + 1, gtl_point_cloud[i], np.array([0, 0, 0]), shm.name, results_directory, Config.K)
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

    start_time = time.time()
    print('waiting for processes ...')

    ser_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ser_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    ser_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    ser_sock.settimeout(.2)

    # last_num = 0
    # num_freeze = 0
    connections = dict()
    while True:
        time.sleep(1)
        visited = {0}
        is_paired = dict()
        for i in range(len(shared_arrays)):
            connections[i+1] = shared_arrays[i]
        for n, c in connections.items():
            if n in visited:
                continue
            visited.add(n)
            n_pairs = []
            for ci in c:
                if ci in visited:
                    continue
                visited.add(ci)
                n_pairs.append(all(c == connections[ci]))
            is_paired[n] = len(n_pairs) and all(n_pairs)

        if len(is_paired) and all(is_paired.values()):
            break
        if count - sum(is_paired.values()) * Config.K <= count % Config.K:
            break

    end_time = time.time()
    stop_message = Message(MessageTypes.STOP).from_server().to_all()
    dumped_stop_msg = pickle.dumps(stop_message)
    ser_sock.sendto(dumped_stop_msg, Constants.BROADCAST_ADDRESS)
    ser_sock.close()
    print("done")

    time.sleep(1)
    for p in processes:
        p.join()

    # visited = set()
    # for c in connections.values():
    #     key = str(c)
    #     if key in visited:
    #         continue
    #     visited.add(key)
    #
    #     xs = [gtl_point_cloud[ci - 1][0] for ci in c]
    #     ys = [gtl_point_cloud[ci - 1][1] for ci in c]
    #     plt.plot(xs + [xs[0]], ys + [ys[0]], '-o')
    # plt.savefig(f'{Config.RESULTS_PATH}/{experiment_name}.jpg')
    # plt.show()

    # if not Config.READ_FROM_NPY and any([v != 2 for v in point_connections.values()]):
    #     with open(f'{Config.RESULTS_PATH}/{experiment_name}.npy', 'wb') as f:
    #         np.save(f, point_cloud)

    for s in shared_memories:
        s.close()
        s.unlink()

    with open(f'results/{Config.SHAPE}_{Config.K}.txt', 'a+') as f:
        f.write(f'{end_time-start_time}\n')
    # utils.plot_point_cloud(np.stack(gtl_point_cloud), None)
