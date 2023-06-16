import socket
from message import Message, MessageTypes
from constants import Constants
import pickle


def stop_all():
    stop_msg = Message(MessageTypes.STOP).from_server().to_all()
    dumped_stop_msg = pickle.dumps(stop_msg)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(dumped_stop_msg, Constants.BROADCAST_ADDRESS)
    sock.close()


if __name__ == '__main__':
    stop_all()
