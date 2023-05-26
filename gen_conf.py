import itertools


def_conf = {
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
}

props = [
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


if __name__ == '__main__':
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
        with open(f'experiments/config{j}.py', 'w') as f:
            f.write('class Config:\n')
            for key, val in conf.items():
                f.write(f'    {key} = {val}\n')

