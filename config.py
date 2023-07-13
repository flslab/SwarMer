class Config:
    INITIAL_RANGE = 2000
    MAX_RANGE = 2000
    DROP_PROB_SENDER = 0
    DROP_PROB_RECEIVER = 0
    DEAD_RECKONING_ANGLE = 0
    FAILURE_TIMEOUT = 60 * 2
    FAILURE_PROB = 0
    ACCELERATION = 1
    DECELERATION = 1
    MAX_SPEED = 3
    DISPLAY_CELL_SIZE = 0.05
    BUSY_WAITING = False
    DURATION = 60 * 1
    K = 5  # if k = 0 no standbys are deployed
    H = 2
    SHAPE = 'racecar'
    RESULTS_PATH = '/proj/nova-PG0/hamed/results'
    DEBUG = False
    FILE_NAME_KEYS = [('DISPATCHERS', 'D'), 'H']
    DIR_KEYS = ['H']
    SERVER_TIMEOUT = 120
    PROCESS_JOIN_TIMEOUT = 120
    DISPATCHERS = 5  # valid values 1 3 5
    DISPATCH_RATE = 1  # valid values 'inf' or a non-zero number
    MULTICAST = True
    INPUT = 'racecar_K:5'
