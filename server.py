import queue
import socket
import pickle
import random
from threading import Thread

import numpy as np
from multiprocessing import shared_memory
import scipy.io
import time
import os
import struct
import stop
from dispatcher import Dispatcher
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
from utils.file import read_cliques_xlsx

# mpl.use('macosx')

should_stop = False
client_processes = dict()
IS_CLUSTER_SERVER = None
IS_CLUSTER_CLIENT = None


def set_stop():
    global should_stop
    should_stop = True
    print('will stop next round')


def query_cliques_client(connection):
    query_msg = Message(MessageTypes.QUERY_CLIQUES)
    connection.sendall(pickle.dumps(query_msg))
    data = recv_msg(connection)
    message = pickle.loads(data)
    # print(message.args[0], message.args[1])
    return message.args[0], message.args[1]  # cliques, connections


def stop_client(connection):
    stop_msg = Message(MessageTypes.STOP)
    connection.sendall(pickle.dumps(stop_msg))
    # data = connection.recv(2048)
    # message = pickle.loads(data)
    # return message.args[0]


def aggregate_cliques(indexes, sh_arrays):
    all_cliques = dict()
    all_connections = dict()
    for k in indexes:
        all_connections[k + 1] = sh_arrays[k]
        clique_key = ".".join([str(clique) for clique in sh_arrays[k]])
        if clique_key in all_cliques:
            all_cliques[clique_key] += 1
        else:
            all_cliques[clique_key] = 1

    return all_cliques, all_connections


def get_shape_floor_center(arr):
    length = arr.shape[0]
    sum_x = np.sum(arr[:, 0])
    sum_y = np.sum(arr[:, 1])
    return np.array([sum_x / length, sum_y / length, 0])


def get_shape_floor_radius(arr, center):
    arr_projected_floor = np.copy(arr)
    arr_projected_floor[:, 2] = 0
    return np.max(np.linalg.norm(arr_projected_floor - center, axis=1))


def get_dispatchers_for_shape(shape, num_dispatchers=1):
    if num_dispatchers == 1:
        return [np.array([0.0, 0.0, 0.0])]

    center = get_shape_floor_center(shape)
    r = get_shape_floor_radius(shape, center)
    dispatcher_coordinates = []
    for k in range(num_dispatchers):
        phi = 2 * np.pi * k / num_dispatchers
        dispatcher_coordinates.append(center + np.array([r * np.cos(phi), r * np.sin(phi), 0]))
    return dispatcher_coordinates


def assign_dispatcher(fid, dispatchers):
    return dispatchers[fid % len(dispatchers)]


def assign_closest_dispatcher(ds, coord):
    dispatcher_coords = np.stack([d.coord for d in ds])
    return ds[np.argmin(np.linalg.norm(dispatcher_coords - coord, axis=1))]


def send_msg(sock, msg):
    # Prefix each message with a 4-byte big-endian unsigned integer (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)


def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def assign_dispatcher_po2(ds):
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


def select_dispatcher(ds, coord):
    return assign_dispatcher_po2(ds)
    # return assign_closest_dispatcher(ds, coord)


def request_dispatcher(p, client_sock):
    # client runs this
    client_processes[p.fid] = p
    send_msg(client_sock, pickle.dumps((p.fid, p.gtl.tolist())))


def handle_dispatcher_assignments(client_sock, processes_dict):
    # client runs this
    while True:
        ser_msg = recv_msg(client_sock)
        if not ser_msg:
            continue
        ser_msg = pickle.loads(ser_msg)
        if ser_msg:
            fid, dispatcher_coord = ser_msg
            p = client_processes.pop(fid)
            p.el = np.array(dispatcher_coord)
            processes_dict[fid] = p
            p.start()
        else:
            send_msg(client_sock, pickle.dumps(False))
            break


def handle_dispatcher_requests(client_sock, ds):
    # server runs this
    while True:
        cl_msg = recv_msg(client_sock)
        if not cl_msg:
            continue
        cl_msg = pickle.loads(cl_msg)
        if cl_msg:
            fid, gtl = cl_msg
            # print(fid, gtl)
            disp = select_dispatcher(ds, gtl)
            disp.q.put(lambda: send_msg(client_sock, pickle.dumps((fid, disp.coord.tolist()))))
        else:
            break


def dispatch_fls(p, client_socket, dispatchers, member_coord, processes_id):
    if IS_CLUSTER_CLIENT:
        request_dispatcher(p, client_socket)
    else:
        dispatcher = select_dispatcher(dispatchers, member_coord)
        p.el = dispatcher.coord
        dispatcher.q.put(p)
        processes_id[pid] = p


error_handling = True

if __name__ == '__main__':
    N = 1
    nid = 0
    experiment_name = str(int(time.time()))
    if len(sys.argv) > 1:
        N = int(sys.argv[1])
        nid = int(sys.argv[2])
        experiment_name = sys.argv[3]

    IS_CLUSTER_SERVER = N != 1 and nid == 0
    IS_CLUSTER_CLIENT = N != 1 and nid != 0

    if IS_CLUSTER_SERVER:
        # Experimental artifact to gather theoretical stats for scientific publications.
        ServerSocket = socket.socket()
        while True:
            try:
                ServerSocket.bind(Constants.SERVER_ADDRESS)
            except OSError:
                time.sleep(10)
                continue
            break
        ServerSocket.listen(N-1)

        clients = []
        for i in range(N-1):
            client, address = ServerSocket.accept()
            print(address)
            clients.append(client)

    client_socket = None
    if IS_CLUSTER_CLIENT:
        client_socket = socket.socket()
        while True:
            try:
                client_socket.connect(Constants.SERVER_ADDRESS)
            except OSError:
                time.sleep(10)
                continue
            break
        server_msg = client_socket.recv(1024)
        start_time = pickle.loads(server_msg)

    K = TestConfig.K if TestConfig.ENABLED else Config.K
    FILE_NAME_KEYS = TestConfig.FILE_NAME_KEYS if TestConfig.ENABLED else Config.FILE_NAME_KEYS

    dir_name = None
    if not Config.DEBUG:
        from datetime import datetime

        current_date_time = datetime.now().strftime("%H:%M:%S_%m:%d:%Y")
        if len(FILE_NAME_KEYS):
            CONFIG = TestConfig if TestConfig.ENABLED else Config
            keys = "_".join(f"{k}:{CONFIG.__getattribute__(CONFIG, k)}" for k in FILE_NAME_KEYS)
        else:
            keys = current_date_time
        file_name = f"{Config.SHAPE}_{keys}"

        if len(TestConfig.DIR_KEYS):
            dir_name = "_".join(f"{k}:{TestConfig.__getattribute__(TestConfig, k)}" for k in TestConfig.DIR_KEYS)

    main_dir = Config.RESULTS_PATH if dir_name is None else os.path.join(Config.RESULTS_PATH, Config.SHAPE, dir_name)
    results_directory = os.path.join(main_dir, file_name if file_name is not None else experiment_name)
    shape_directory = main_dir
    figure_directory = os.path.join(shape_directory, 'figures')
    if not Config.DEBUG:
        if not os.path.exists(results_directory):
            os.makedirs(os.path.join(results_directory, 'json'), exist_ok=True)
        if not os.path.exists(figure_directory):
            os.makedirs(figure_directory, exist_ok=True)

    # if TestConfig.ENABLED:
    #     r2 = 1
    #     r1 = r2 * TestConfig.R
    #     n1 = TestConfig.NUMBER_OF_FLSS // K
    #     n2 = K
    #
    #     points = []
    #     for i in range(n1):
    #         theta = i * 2 * np.pi / n1
    #         c1 = [r1 * np.cos(theta), r1 * np.sin(theta), 0]
    #         for j in range(n2):
    #             alpha = theta + j * 2 * np.pi / n2
    #             point = [c1[0] + r2 * np.cos(alpha), c1[1] + r2 * np.sin(alpha), j]
    #             points.append(point)
    #
    #     # for i in range(n2):
    #     #     theta = i * 2 * np.pi / n2
    #     #
    #     #     for j in range(n1):
    #     #         alpha = theta + j * (np.pi / 2) / n1
    #     #         point = [(r2 + TestConfig.RATIO * j / n1) * np.cos(alpha), (r2 + TestConfig.RATIO * j / n1) * np.sin(alpha), 0]
    #     #         points.append(point)
    #
    #     point_cloud = np.array(points)
    #
    # else:
    #     if Config.READ_FROM_NPY:
    #         with open(f'results/{Config.READ_FROM_NPY}.npy', 'rb') as f:
    #             point_cloud = np.load(f)
    #     else:
    #         mat = scipy.io.loadmat(f'assets/{Config.SHAPE}.mat')
    #         point_cloud = mat['p']
    #
    #     if Config.SAMPLE_SIZE != 0:
    #         np.random.shuffle(point_cloud)
    #         point_cloud = point_cloud[:Config.SAMPLE_SIZE]
    #
    # total_count = point_cloud.shape[0]
    # # h = np.log2(total_count)
    #
    # gtl_point_cloud = np.random.uniform(0, 5, size=(total_count, 3))
    # sample = np.zeros(K, dtype=np.int32)
    #
    # node_point_idx = []
    # for i in range(total_count):
    #     if i % N == nid:
    #         node_point_idx.append(i)
    #     gtl_point_cloud[i] = np.array([point_cloud[i][0], point_cloud[i][1], point_cloud[i][2]])
    #
    # count = len(node_point_idx)
    # # print(count)

    count = 0

    # dispatchers = get_dispatchers_for_shape(None)
    l = 50
    w = 100
    if Config.DISPATCHERS == 1:
        dispatchers_coords = np.array([[l/2, w/2, 0]])
    elif Config.DISPATCHERS == 3:
        dispatchers_coords = np.array([[l/2, w/2, 0], [l, w, 0], [0, 0, 0]])
    elif Config.DISPATCHERS == 5:
        dispatchers_coords = np.array([[l/2, w/2, 0], [l, 0, 0], [0, w, 0], [l, w, 0], [0, 0, 0]])
    # dispatchers = np.array(Config.DISPATCHERS)

    dispatchers = []
    if nid == 0:
        for coord in dispatchers_coords:
            q = queue.Queue()
            d = Dispatcher(q, Config.DISPATCH_RATE, coord)
            dispatchers.append(d)
            d.start()

    # processes = []
    # shared_arrays = dict()
    # shared_memories = dict()

    # local_gtl_point_cloud = []
    # pidx = np.array(node_point_idx)
    # np.random.shuffle(pidx)
    # print(pidx)

    # knn_idx, knn_dists = utils.knn(gtl_point_cloud)

    processes_id = dict()

    if IS_CLUSTER_CLIENT:
        dispatcher_handler_thread = Thread(target=handle_dispatcher_assignments, args=(client_socket, processes_id))
        dispatcher_handler_thread.start()

    if IS_CLUSTER_SERVER:
        dispatch_request_handler_threads = []
        for client in clients:
            dt = Thread(target=handle_dispatcher_requests, args=(client, dispatchers))
            dt.start()
            dispatch_request_handler_threads.append(dt)

    start_time = time.time()
    if IS_CLUSTER_SERVER:
        for client in clients:
            client.sendall(pickle.dumps(start_time))

    try:
        # failure handling
        group_map = {}
        group_standby_id = {}
        group_standby_coord = {}
        group_radio_range = {}
        i = 0
        if error_handling:
            groups, radio_ranges = read_cliques_xlsx(os.path.join(shape_directory, f'{Config.INPUT}.xlsx'))
            # groups, radio_ranges = read_cliques_xlsx("/Users/hamed/Desktop/chess/k5/chess_K:5_02_Jul_17_41_43.xlsx")
            # groups = groups[:3]
            # radio_ranges = radio_ranges[:3]
            # "/Users/hamed/Documents/Holodeck/SwarMerPy/results/20-Jun-11_14_58/results/racecar/H:2/agg.xlsx")
            # print(radio_ranges)
            # exit()
            # print(groups)
            # print(radio_ranges)
            single_members = []
            single_indexes = []
            max_dist_singles = 0
            for k in range(len(groups)):
                if groups[k].shape[0] == 1:
                    # print(groups[k])
                    if len(single_indexes):
                        max_dist_n = np.max(np.linalg.norm(np.stack(single_members) - groups[k][0], axis=1))
                        max_dist_singles = max(max_dist_singles, max_dist_n)
                    single_members.append(groups[k][0])
                    single_indexes.append(k)

            for k in reversed(single_indexes):
                groups.pop(k)
                radio_ranges.pop(k)

            if len(single_members):
                groups.append(np.stack(single_members))
                radio_ranges.append(max_dist_singles)

            # print(groups)
            # print(radio_ranges)
            # exit()

            for j in range(len(groups)):
                if j % N == nid:
                    group = groups[j]
                    group_id = N * (i + 1) + nid
                    group_ids = list(range(group_id, group_id + N * len(group), N))
                    if Config.C == 1:
                        standby_id = group_ids[-1] + N
                        group_standby_id[group_id] = standby_id
                        length = group.shape[0]
                        sum_x = np.sum(group[:, 0])
                        sum_y = np.sum(group[:, 1])
                        sum_z = np.sum(group[:, 2])
                        stand_by_coord = np.array([sum_x / length, sum_y / length, sum_z / length])
                        group_standby_coord[group_id] = stand_by_coord
                    else:
                        standby_id = None
                    group_map[group_id] = set(group_ids)
                    group_radio_range[group_id] = radio_ranges[j]

                    # dispatch group members
                    for member_coord in group:
                        i += 1
                        pid = N * i + nid

                        p = worker.WorkerProcess(
                            count, pid, member_coord, None, None, results_directory,
                            start_time, standby_id=standby_id, sid=-nid,
                            group_id=group_id, radio_range=group_radio_range[group_id])

                        dispatch_fls(p, client_socket, dispatchers, member_coord, processes_id)

                    # dispatch standby
                    if Config.C == 1:
                        i += 1
                        pid = N * i + nid
                        p = worker.WorkerProcess(
                            count, pid, stand_by_coord, None, None, results_directory,
                            start_time, is_standby=True, sid=-nid,
                            group_id=group_id, radio_range=group_radio_range[group_id])

                        dispatch_fls(p, client_socket, dispatchers, stand_by_coord, processes_id)
            # print(group_map)
            # print(group_standby_id)
            # print(group_standby_coord)
            print(i)
            # exit()
    except OSError as e:
        print(e)
        for p in processes_id.values():
            p.terminate()
        # for s in shared_memories:
        #     s.close()
        #     s.unlink()
        exit()

    # gtl_point_cloud = local_gtl_point_cloud

    print('waiting for processes ...')

    freeze_counter = 0
    last_hash = None

    if error_handling:
        error_handling_socket = worker.WorkerSocket()
        while True:
            msg, _ = error_handling_socket.receive()
            if msg.dest_fid == -nid:
                if msg.type == MessageTypes.REPLICA_REQUEST:
                    i += 1
                    pid = i * N + nid
                    group_id = msg.swarm_id
                    failed_fid = msg.fid
                    is_illuminating = msg.args[0]

                    if is_illuminating:
                        p = worker.WorkerProcess(
                            count, pid, msg.gtl, None, None, results_directory,
                            start_time, sid=-nid,
                            group_id=group_id, radio_range=group_radio_range[group_id])

                        dispatch_fls(p, client_socket, dispatchers, msg.gtl, processes_id)

                    else:
                        previous_standby = group_standby_id[group_id]
                        group_standby_id[group_id] = pid

                        # dispatch the new standby fls
                        p = worker.WorkerProcess(
                            count, pid, group_standby_coord[group_id], None, None, results_directory,
                            start_time, is_standby=True, sid=-nid,
                            group_id=group_id, radio_range=group_radio_range[group_id])

                        dispatch_fls(p, client_socket, dispatchers, group_standby_coord[group_id], processes_id)

                        # send the id of the new standby to group members
                        new_standby_msg = Message(MessageTypes.ASSIGN_STANDBY, args=(pid,)) \
                            .from_server(-nid).to_fls_id("*", group_id)
                        error_handling_socket.broadcast(new_standby_msg)

                        # send the notification to the previous standby of this group
                        # error_handling_socket.broadcast(msg.to_fls_id(previous_standby, group_id))
                    processes_id.pop(failed_fid).join()
            if time.time() - start_time > Config.DURATION:
                break

    end_time = time.time()

    if nid == 0:
        stop.stop_all()
    print("done")

    time.sleep(1)

    if IS_CLUSTER_CLIENT:
        dispatcher_handler_thread.join()

    if IS_CLUSTER_SERVER:
        print("waiting for dispatcher handlers")

        for client in clients:
            send_msg(client, pickle.dumps(False))
        for dt in dispatch_request_handler_threads:
            dt.join()

        for i in range(N - 1):
            # stop_client(clients[i])
            clients[i].close()
        ServerSocket.close()

    if nid == 0:
        print("waiting for dispatchers")
        for d in dispatchers:
            d.q.put(False)
            d.join()

    for p in processes_id.values():
        print("waiting for flss")
        p.join(Config.PROCESS_JOIN_TIMEOUT)
        if p.is_alive():
            break

    for p in processes_id.values():
        if p.is_alive():
            p.terminate()

    # if nid == 0:
    #     visited = set()
    #     fig = plt.figure()
    #     ax = fig.add_subplot(projection='3d')
    #     for c in connections.values():
    #         key = str(c)
    #         if key in visited:
    #             continue
    #         visited.add(key)
    #
    #         xs = [gtl_point_cloud[ci - 1][0] for ci in c]
    #         ys = [gtl_point_cloud[ci - 1][1] for ci in c]
    #         zs = [gtl_point_cloud[ci - 1][2] for ci in c]
    #         ax.plot3D(xs + [xs[0]], ys + [ys[0]], zs + [zs[0]], '-o')
    #     # plt.savefig(f'{Config.RESULTS_PATH}/{experiment_name}.jpg')
    #     if Config.DEBUG:
    #         plt.show()
    #     else:
    #         plt.savefig(os.path.join(figure_directory, f'{file_name}.jpg'))

    # if not Config.READ_FROM_NPY and any([v != 2 for v in point_connections.values()]):
    #     with open(f'{Config.RESULTS_PATH}/{experiment_name}.npy', 'wb') as f:
    #         np.save(f, point_cloud)

    if not Config.DEBUG and nid == 0:
        if IS_CLUSTER_SERVER:
            time.sleep(120)
        utils.create_csv_from_json(results_directory, os.path.join(figure_directory, f'{file_name}.jpg'))
        utils.write_configs(results_directory, current_date_time)
        utils.combine_csvs(results_directory, shape_directory, "reli_" + file_name)
    if Config.DEBUG:
        utils.create_csv_from_json(results_directory, os.path.join(figure_directory, 'debug.jpg'))


    # for s in shared_memories.values():
    #     s.close()
    #     s.unlink()

    # utils.plot_point_cloud(np.stack(gtl_point_cloud), None)
