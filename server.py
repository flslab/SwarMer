import socket
import pickle
import numpy as np
from multiprocessing import shared_memory
import scipy.io

from config import Config
from constants import Constants
from message import Message, MessageTypes
import worker
import utils
import bag


if __name__ == '__main__':
    count = Config.NUMBER_POINTS
    np.random.default_rng(1)
    mat = scipy.io.loadmat('cat.mat')
    gtl_point_cloud = mat['p']
    # gtl_point_cloud = np.random.uniform(0, 30, size=(count, 3))
    # gtl_point_cloud = np.array([[0, 0, 1], [0, 0, 2], [5, 5, 1], [5, 5, 2]])
    # el_point_cloud = gtl_point_cloud + np.random.randint(2, size=(count, 3))

    shm = shared_memory.SharedMemory(create=True, size=gtl_point_cloud.nbytes)
    shared_array = np.ndarray(gtl_point_cloud.shape, dtype=gtl_point_cloud.dtype, buffer=shm.buf)

    processes = []
    for i in range(count):
        p = worker.WorkerProcess(count, i + 1, gtl_point_cloud[i], np.array([0, 0, 0]), shm.name)
        p.start()
        processes.append(p)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server_sock.bind(Constants.SERVER_ADDRESS)
    fin_message_sent = False
    final_point_cloud = np.zeros([count, 3])
    fin_processes = np.zeros(count)
    flight_path = {}

    # utils.plot_point_cloud(el_point_cloud, shared_el)

    while True:
        data, _ = server_sock.recvfrom(2048)
        msg = pickle.loads(data)

        if msg.type == MessageTypes.FIN and not fin_message_sent:
            stop_message = Message(MessageTypes.STOP).from_server().to_all()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.2)
            sock.sendto(pickle.dumps(stop_message), Constants.BROADCAST_ADDRESS)
            sock.close()
            fin_message_sent = True
            continue

        final_point_cloud[msg.fid - 1] = msg.el
        flight_path[msg.fid - 1] = msg.args[0]
        fin_processes[msg.fid - 1] = 1

        if np.sum(fin_processes) == count:
            break

    server_sock.close()

    # print(shared_array)

    for p in processes:
        p.join()

    print(f"hd: {utils.hausdorff_distance(shared_array, gtl_point_cloud)}")
    # print(flight_path)
    # print(flight_path.values())
    print("writing bag file...")
    msgs = [bag.generate_msg_flight_path(path) for path in flight_path.values()]
    bag.write_msgs_bag(msgs, 'test.bag')

    # bag = rosbag.Bag('test.bag')
    # for topic, msg, t in bag.read_messages(topics=['topic']):
    #     print(msg)
    # bag.close()

    shm.close()
    shm.unlink()
