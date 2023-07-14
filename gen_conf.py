import itertools
import sys

def_general_conf = {
    "INITIAL_RANGE": "2000",
    "MAX_RANGE": "2000",
    "DROP_PROB_SENDER": "0",
    "DROP_PROB_RECEIVER": "0",
    "DEAD_RECKONING_ANGLE": "0",
    "FAILURE_TIMEOUT": "60 * 2",
    "FAILURE_PROB": "0",
    "ACCELERATION": "1",
    "DECELERATION": "1",
    "MAX_SPEED": "3",
    "DISPLAY_CELL_SIZE": "0.05",
    "BUSY_WAITING": "False",
    "DURATION": "60 * 10",
    "K": "20",
    "H": "2",
    "SHAPE": "'racecar'",
    "RESULTS_PATH": "'/proj/nova-PG0/hamed/results'",
    "DEBUG": "False",
    "FILE_NAME_KEYS": "['K', ('DISPATCHERS', 'D'), ('DISPATCH_RATE', 'R'), ('FAILURE_TIMEOUT', 'T')]",
    "DIR_KEYS": "['H']",
    "SERVER_TIMEOUT": "120",
    "PROCESS_JOIN_TIMEOUT": "120",
    "DISPATCHERS": "1",
    "DISPATCH_RATE": "'inf'",
    "MULTICAST": "True",
    "INPUT": "'racecar_K20'"
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
        "keys": ["DISPATCH_RATE"],
        "values": ["1", "'inf'"]
    },
    {
        "keys": ["K", "INPUT"],
        "values": [
            # {"K": "0", "INPUT": "'chess_K3'"},
            {"K": "3", "INPUT": "'racecar_K3'"},
            # {"K": "20", "INPUT": "'chess_K20'"},
        ]
    },
    {
        "keys": ["DISPATCHERS"],
        "values": ["5"]
    },
    {
        "keys": ["FAILURE_TIMEOUT"],
        "values": ["30", "120"]
        # "values": ["1", "3", "6", "30", "60", "120", "600"]
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

