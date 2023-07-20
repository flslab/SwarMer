class Constants:
    # BROADCAST_ADDRESS = ("<broadcast>", 5000)
    # BROADCAST_ADDRESS = ("127.0.0.1", 5000)
    BROADCAST_ADDRESS = ("10.0.1.255", 5000)
    BROADCAST_PORT = 5000
    # SERVER_ADDRESS = ("172.31.94.241", 6000)  # cluster 1
    SERVER_ADDRESS = ("10.0.7.242", 6000)  # cluster 2
    # SERVER_ADDRESS = ("10.0.1.1", 6000)  # cloudlab
    SERVER_PORT = 6000
    WORKER_ADDRESS = ("", 5000)

    # MULTICAST_GROUP_ADDRESS = ('224.3.29.71', 5000)  # cluster 1
    # MULTICAST_GROUP = '224.3.29.71'  # cluster 1

    MULTICAST_GROUP_ADDRESS = ('224.3.29.25', 5000)  # cluster 2 & cloudlab
    MULTICAST_GROUP = '224.3.29.25'  # cluster 2 & cloudlab

    # MULTICAST_GROUP_ADDRESS = ('224.3.29.35', 5000)  # server 1
    # MULTICAST_GROUP = '224.3.29.35'  # server 1

    # MULTICAST_GROUP_ADDRESS = ('224.3.29.45', 5000)  # server 2
    # MULTICAST_GROUP = '224.3.29.45'  # server 2
    #
    # MULTICAST_GROUP_ADDRESS = ('224.3.29.55', 5000)  # server 3
    # MULTICAST_GROUP = '224.3.29.55'  # server 3
