import itertools
import sys

def_general_conf = {
    "THAW_SWARMS": "False",
    "INITIAL_RANGE": "1",
    "MAX_RANGE": "100",
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
    "K": "3",
    "SHAPE": "'butterfly'",
    "RESULTS_PATH": "'results'",
    "FILE_NAME_KEYS": "['K']",
}

def_test_conf = {
    "ENABLED": "True",
    "NUMBER_OF_FLSS": "165",
    "K": "3",
    "RATIO": "100",
    "FILE_NAME_KEYS": "['K', 'RATIO']"
}

general_props = [
    {
        "keys": ["K"],
        "values": ["3", "5", "10"]
    },
    {
        "keys": ["SAMPLE_SIZE", "SHAPE"],
        "values": [{"SAMPLE_SIZE": 94, "SHAPE": "'butterfly'"},
                   {"SAMPLE_SIZE": 100, "SHAPE": "'teapot'"},
                   {"SAMPLE_SIZE": 114, "SHAPE": "'cat'"}]
    },
]

test_props = [
    {
        "keys": ["RATIO"],
        "values": ["1000", "100", "10", "1"]
    },
    {
        "keys": ["K"],
        "values": ["7", "13", "19"]
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

