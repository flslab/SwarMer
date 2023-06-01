import socket
import pickle
import numpy as np
from multiprocessing import shared_memory
import scipy.io
import time
import os

from test_config import TestConfig
from config import Config
from constants import Constants
from message import Message, MessageTypes
import worker
import utils
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl

from utils import dict_hash

# mpl.use('macosx')

test = True
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
    shape_directory = os.path.join(Config.RESULTS_PATH, Config.SHAPE)
    if not Config.DEBUG:
        if not os.path.exists(results_directory):
            os.makedirs(os.path.join(results_directory, 'json'), exist_ok=True)

    K = TestConfig.K if TestConfig.ENABLED else Config.K

    if TestConfig.ENABLED:
        r2 = 1
        r1 = r2 * TestConfig.RATIO
        n1 = TestConfig.NUMBER_OF_FLSS // K
        n2 = K

        points = []
        for i in range(n1):
            theta = i * 2 * np.pi / n1
            c1 = [r1 * np.cos(theta), r1 * np.sin(theta), 0]
            for j in range(n2):
                alpha = j * 2 * np.pi / n2
                point = [c1[0] + r2 * np.cos(alpha), c1[1] + r2 * np.sin(alpha), 0]
                points.append(point)

        point_cloud = np.array(points)

    else:
        if Config.READ_FROM_NPY:
            with open(f'results/{Config.READ_FROM_NPY}.npy', 'rb') as f:
                point_cloud = np.load(f)
        else:
            mat = scipy.io.loadmat(f'assets/{Config.SHAPE}.mat')
            point_cloud = mat['p']

        if Config.SAMPLE_SIZE != 0:
            np.random.shuffle(point_cloud)
            point_cloud = point_cloud[:Config.SAMPLE_SIZE]

    total_count = point_cloud.shape[0]
    h = np.log2(total_count)

    gtl_point_cloud = np.random.uniform(0, 5, size=(total_count, 3))
    sample = np.zeros(K, dtype=np.int32)

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

    knn_idx, knn_dists = utils.knn(gtl_point_cloud)

    try:
        for i in node_point_idx:
            shm = shared_memory.SharedMemory(create=True, size=sample.nbytes)
            shared_array = np.ndarray(sample.shape, dtype=sample.dtype, buffer=shm.buf)
            shared_array[:] = i+1

            shared_arrays.append(shared_array)
            shared_memories.append(shm)
            local_gtl_point_cloud.append(gtl_point_cloud[i])

            sorted_neighbors = knn_idx[i][1:] + 1
            fid_to_dist = dict(zip(sorted_neighbors, knn_dists[i][1:]))

            p = worker.WorkerProcess(
                count, i + 1, gtl_point_cloud[i], gtl_point_cloud[i], shm.name, results_directory,
                K, sorted_neighbors.tolist(), fid_to_dist)
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

    # gtl_point_cloud = local_gtl_point_cloud

    start_time = time.time()
    print('waiting for processes ...')

    # last_num = 0
    # num_freeze = 0
    # connections = dict()
    # while True:
    #     time.sleep(1)
    #     visited = {0}
    #     is_paired = dict()
    #     for i in range(len(shared_arrays)):
    #         connections[i+1] = shared_arrays[i]
    #     for n, c in connections.items():
    #         if n in visited:
    #             continue
    #         visited.add(n)
    #         n_pairs = []
    #         for ci in c:
    #             if ci in visited:
    #                 continue
    #             visited.add(ci)
    #             n_pairs.append(all(c == connections[ci]))
    #         is_paired[n] = len(n_pairs) and all(n_pairs)
    #
    #     if len(is_paired) and all(is_paired.values()):
    #         break
    #     if count - sum(is_paired.values()) * K == count % K:
    #         break

    freeze_counter = 0
    last_hash = None
    while True:
        time.sleep(1)
        cliques = dict()
        for i in range(len(shared_arrays)):
            key = ".".join([str(c) for c in shared_arrays[i]])
            if key in cliques:
                cliques[key] += 1
            else:
                cliques[key] = 1

        clique_sizes = filter(lambda x: x == K, cliques.values())
        single_sizes = filter(lambda x: x == 1, cliques.values())
        d_hash = dict_hash(cliques)
        if d_hash == last_hash:
            freeze_counter += 1
        else:
            freeze_counter = 0

        if freeze_counter == 10:
            break
        last_hash = d_hash
        if len(list(clique_sizes)) == count // K and len(list(single_sizes)) == count % K:
            print(cliques)
            break

    connections = dict()
    for i in range(len(shared_arrays)):
        connections[i+1] = shared_arrays[i]

    end_time = time.time()
    stop_message = Message(MessageTypes.STOP).from_server().to_all()
    dumped_stop_msg = pickle.dumps(stop_message)
    ser_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ser_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    ser_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    ser_sock.sendto(dumped_stop_msg, Constants.BROADCAST_ADDRESS)
    ser_sock.close()
    print("done")

    time.sleep(1)
    for p in processes:
        p.join(30)
        if p.is_alive():
            break

    for p in processes:
        if p.is_alive():
            p.terminate()

    # print(connections)
    visited = set()
    for c in connections.values():
        key = str(c)
        if key in visited:
            continue
        visited.add(key)

        xs = [gtl_point_cloud[ci - 1][0] for ci in c]
        ys = [gtl_point_cloud[ci - 1][1] for ci in c]
        plt.plot(xs + [xs[0]], ys + [ys[0]], '-o')
    # plt.savefig(f'{Config.RESULTS_PATH}/{experiment_name}.jpg')
    if Config.DEBUG:
        plt.show()
    else:
        plt.savefig(f'{Config.RESULTS_PATH}/{experiment_name}.jpg')

    # if not Config.READ_FROM_NPY and any([v != 2 for v in point_connections.values()]):
    #     with open(f'{Config.RESULTS_PATH}/{experiment_name}.npy', 'wb') as f:
    #         np.save(f, point_cloud)

    if not Config.DEBUG:
        utils.create_csv_from_json(results_directory, end_time-start_time)
        utils.write_configs(results_directory)
        utils.combine_csvs(results_directory, shape_directory)

    for s in shared_memories:
        s.close()
        s.unlink()

    # utils.plot_point_cloud(np.stack(gtl_point_cloud), None)
