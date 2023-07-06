import itertools
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
    "FAILURE_TIMEOUT": "60 * 2",
    "FAILURE_PROB": "0",
    "NUMBER_ROUND": "5",
    "ACCELERATION": "1",
    "DECELERATION": "1",
    "MAX_SPEED": "3",
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
    "DURATION": "60 * 1",
    "READ_FROM_NPY": "0",
    "K": "20",
    "MAX_NEIGHBORS": "0",
    "SHAPE": "'racecar'",
    "RESULTS_PATH": "'/proj/nova-PG0/hamed/results'",
    "DEBUG": "False",
    "FILE_NAME_KEYS": "['C', 'K', 'DISPATCHERS', 'FAILURE_TIMEOUT']",
    "SERVER_TIMEOUT": "120",
    "PROCESS_JOIN_TIMEOUT": "120",
    "DISPATCHERS": "1",
    "C": "1",
    "MULTICAST": "True",
    "INPUT": "'dragon_K:20'"
}

def_test_conf = {
    "ENABLED": "True",
    "NUMBER_OF_FLSS": "165",
    "K": "3",
    "R": "100",
    "H": "1",
    "ETA": "K-1",
    "ETA_STR": "'K-1'",
    "FILE_NAME_KEYS": "['H', 'K', 'R']",
    "DIR_KEYS": "['H']"
}

general_props = [
    {
        "keys": ["C", "K", "INPUT"],
        "values": [
            {"C": "0", "K": "3", "INPUT": "'racecar_K:3'"},
            {"C": "1", "K": "3", "INPUT": "'racecar_K:3'"},
            {"C": "1", "K": "5", "INPUT": "'racecar_K:5'"},
            {"C": "1", "K": "10", "INPUT": "'racecar_K:10'"},
            {"C": "1", "K": "20", "INPUT": "'racecar_K:20'"},
        ]
    },
    {
        "keys": ["DISPATCHERS"],
        "values": ["1", "3", "5"]
    },
    {
        "keys": ["FAILURE_TIMEOUT"],
        "values": ["1", "3", "6", "30", "60", "120", "600"]
    }
    # {
    #     "keys": ["SHAPE"],
    #     "values": ["'racecar'", "'skateboard'"]
    # }
    # {
    #     "keys": ["SAMPLE_SIZE", "SHAPE"],
    #     "values": [{"SAMPLE_SIZE": 94, "SHAPE": "'butterfly'"},
    #                {"SAMPLE_SIZE": 100, "SHAPE": "'teapot'"},
    #                {"SAMPLE_SIZE": 114, "SHAPE": "'cat'"}]
    # },
]
#
# test_props = [
#     {
#         "keys": ["H", "ETA", "ETA_STR"],
#         "values": [
#             {"H": "'vns'", "ETA": "K-1", "ETA_STR": "'K-1'"},
#             {"H": "'rs'", "ETA": "K-1", "ETA_STR": "'K-1'"},
#             {"H": "'rs'", "ETA": "K", "ETA_STR": "'K'"},
#             {"H": "'rs'", "ETA": "3*K//2", "ETA_STR": "'1.5K'"},
#                    ]
#     },
#     {
#         "keys": ["K"],
#         "values": ["3", "5", "11"]
#     },
#     {
#         "keys": ["R"],
#         "values": ["1000", "100", "10", "1"]
#     },
# ]


test_props = [
    {
        "keys": ["H"],
        "values": ["2", "'vns'"]
    },
    {
        "keys": ["K"],
        "values": ["11", "15"]
    },
    {
        "keys": ["R"],
        "values": ["10", "1"]
    },
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

