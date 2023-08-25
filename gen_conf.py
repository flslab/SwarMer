import itertools
import os
import sys

def_general_conf = {
    "THAW_SWARMS": "False",
    "INITIAL_RANGE": "2000",
    "MAX_RANGE": "2000",
    "DROP_PROB_SENDER": "0",
    "DROP_PROB_RECEIVER": "0",
    "STATE_TIMEOUT": "0",
    "SIZE_QUERY_TIMEOUT": "10",
    "DEAD_RECKONING_ANGLE": "0",
    "CHALLENGE_PROB_DECAY": "5",
    "INITIAL_CHALLENGE_PROB": "1",
    "CHALLENGE_LEASE_DURATION": "1",
    "FAILURE_TIMEOUT": "0",
    "FAILURE_PROB": "0",
    "NUMBER_ROUND": "5",
    "ACCELERATION": "6",
    "DECELERATION": "6",
    "MAX_SPEED": "6",
    "DISPLAY_CELL_SIZE": "0.05",
    "HD_TIMOUT": "5",
    "SIZE_QUERY_PARTICIPATION_PERCENT": "1",
    "DECENTRALIZED_SWARM_SIZE": "False",
    "CENTRALIZED_SWARM_SIZE": "False",
    "PROBABILISTIC_ROUND": "False",
    "CENTRALIZED_ROUND": "True",
    "BUSY_WAITING": "False",
    "MIN_ADJUSTMENT": "0",
    "SAMPLE_SIZE": "0",
    "DURATION": "600",
    "READ_FROM_NPY": "0",
    "K": "15",
    "H": "2.2",
    "ETA": "K-1",
    "ETA_STR": "'K-1'",
    "VNS_TIMEOUT": "0.1",
    "MAX_NEIGHBORS": "0",
    "SHAPE": "'chess'",
    "RESULTS_PATH": "'/proj/nova-PG0/hamed/kresults'",
    "DEBUG": "False",
    "FILE_NAME_KEYS": "['K']",
    "DIR_KEYS": "['H', 'ETA_STR']",
    "SERVER_TIMEOUT": "120",
    "PROCESS_JOIN_TIMEOUT": "120",
    "NUM_DISPATCHERS": "1",
    "MULTICAST": "False",
    "TIMELINE_LOG": "False",
    "OPT_SORT": "True",
}

def_test_conf = {
    "ENABLED": "True",
    "NUMBER_OF_FLSS": "90",
    "K": "15",
    "R": "1",
    "H": "2",
    "VNS_TIMEOUT": "0.1",
    "DROP_PROB_SENDER": "0",
    "DROP_PROB_RECEIVER": "0",
    "EXPANSION_TIMEOUT": "0.05",
    "ETA": "K-1",
    "ETA_STR": "'K-1'",
    "FILE_NAME_KEYS": "['K', 'R']",
    "DIR_KEYS": "['H', 'ETA_STR']"
}

general_props = [
    # {
    #     "keys": ["SHAPE", "K"],
    #     "values": [
    #         # {"SHAPE": "'chess'", "K": "3"},
    #         # {"SHAPE": "'chess'", "K": "20"},
    #         {"SHAPE": "'skateboard'", "K": "20"},
    #     ]
    # },
    # {
    #     "keys": ["H"],
    #     "values": ["'rs'"]
    # },
    {
        "keys": ["SHAPE", "K", "H", "ETA", "ETA_STR"],
        "values": [
            # {"H": "'vns'", "VNS_TIMEOUT": "0.04"},
            # {"H": "1", "ETA": "K", "ETA_STR": "'G'", "VNS_TIMEOUT": "0.1"},
            # {"H": "'vns'", "ETA": "K-1", "ETA_STR": "'_'", "VNS_TIMEOUT": "0.1", "K": "3"},
            # {"H": "'vns'", "ETA": "K-1", "ETA_STR": "'_'", "VNS_TIMEOUT": "0.1", "K": "20"},
            # {"H": "2.2", "VNS_TIMEOUT": "0.1", "ETA": "K-1", "ETA_STR": "'_'"},
            {"SHAPE": "'skateboard'", "K": "10", "H": "2.2", "ETA": "K-1", "ETA_STR": "'_'"},  # 0
            {"SHAPE": "'dragon'", "K": "5", "H": "1", "ETA": "K", "ETA_STR": "'G'"},  # 1
            {"SHAPE": "'dragon'", "K": "5", "H": "'rs'", "ETA": "K-1", "ETA_STR": "'G-1'"},  # 2
            {"SHAPE": "'dragon'", "K": "5", "H": "2.2", "ETA": "K-1", "ETA_STR": "'_'"},  # 3
            {"SHAPE": "'dragon'", "K": "10", "H": "1", "ETA": "K", "ETA_STR": "'G'"},  # 4
            {"SHAPE": "'dragon'", "K": "10", "H": "'rs'", "ETA": "K-1", "ETA_STR": "'G-1'"},  # 5
            {"SHAPE": "'dragon'", "K": "10", "H": "2.2", "ETA": "K-1", "ETA_STR": "'_'"},  # 6

            {"SHAPE": "'chess'", "K": "10", "H": "1", "ETA": "K", "ETA_STR": "'G'"},  # 7
            {"SHAPE": "'chess'", "K": "10", "H": "'rs'", "ETA": "K-1", "ETA_STR": "'G-1'"},  # 8

            {"SHAPE": "'dragon'", "K": "5", "H": "'vns'", "ETA": "K-1", "ETA_STR": "'_'"},  # 9
            {"SHAPE": "'dragon'", "K": "10", "H": "'vns'", "ETA": "K-1", "ETA_STR": "'_'"},  # 10
            {"SHAPE": "'chess'", "K": "10", "H": "'vns'", "ETA": "K-1", "ETA_STR": "'_'"},  # 11
        ]
    },
    # {
    #     "keys": ["K"],
    #     "values": ["3"]
    # },
]

test_props = [
    # {
    #     "keys": ["DROP_PROB_SENDER", "DROP_PROB_RECEIVER"],
    #     "values": [
    #         {"DROP_PROB_SENDER": "0", "DROP_PROB_RECEIVER": "0"},  # 0%
    #         {"DROP_PROB_SENDER": "0", "DROP_PROB_RECEIVER": "0.001"},  # 0.1%
    #         {"DROP_PROB_SENDER": "0", "DROP_PROB_RECEIVER": "0.01"},  # 1%
    #         {"DROP_PROB_SENDER": "0", "DROP_PROB_RECEIVER": "0.1"},  # 10%
    #         {"DROP_PROB_SENDER": "0.001", "DROP_PROB_RECEIVER": "0"},  # 0.1%
    #         {"DROP_PROB_SENDER": "0.01", "DROP_PROB_RECEIVER": "0"},  # 1%
    #         {"DROP_PROB_SENDER": "0.1", "DROP_PROB_RECEIVER": "0"},  # 10%
    #         {"DROP_PROB_SENDER": "0.001", "DROP_PROB_RECEIVER": "0.001"},  # 0.1%
    #         {"DROP_PROB_SENDER": "0.01", "DROP_PROB_RECEIVER": "0.01"},  # 1%
    #         {"DROP_PROB_SENDER": "0.1", "DROP_PROB_RECEIVER": "0.1"},  # 10%
    #     ]
    # },
    {
        "keys": ["H", "ETA", "ETA_STR"],
        "values": [
            # {"H": "'vns'", "VNS_TIMEOUT": "0.04"},
            # {"H": "'vns'", "VNS_TIMEOUT": "0.1"},
            # {"H": "2.2", "VNS_TIMEOUT": "0.1", "ETA": "K-1", "ETA_STR": "'_'"},
            {"H": "'rs'", "ETA": "K-1", "ETA_STR": "'K-1'"},
            {"H": "'rs'", "ETA": "K", "ETA_STR": "'K'"},
            {"H": "'rs'", "ETA": "3*K//2", "ETA_STR": "'1.5K'"},
        ]
    },
    {
        "keys": ["K"],
        "values": ["5", "10"]
    },
    {
        "keys": ["R"],
        "values": ["1"]
    },
    # {
    #     "keys": ["H"],
    #     "values": ["2.1"]
    # },
]

if __name__ == '__main__':
    file_name = "config"
    class_name = "Config"
    props = general_props
    def_conf = def_general_conf
    if len(sys.argv) > 1:
        file_name = "test_config"
        class_name = "TestConfig"
        props = test_props
        def_conf = def_test_conf

    props_values = [p["values"] for p in props]
    print(props_values)
    combinations = list(itertools.product(*props_values))
    print(len(combinations))

    if not os.path.exists('experiments'):
        os.makedirs('experiments', exist_ok=True)

    for j in range(len(combinations)):
        c = combinations[j]
        conf = def_conf.copy()
        for i in range(len(c)):
            for k in props[i]["keys"]:
                if isinstance(c[i], dict):
                    conf[k] = c[i][k]
                else:
                    conf[k] = c[i]
        with open(f'experiments/{file_name}{j}.py', 'w') as f:
            f.write(f'class {class_name}:\n')
            for key, val in conf.items():
                f.write(f'    {key} = {val}\n')

