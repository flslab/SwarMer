class TestConfig:
    ENABLED = False
    NUMBER_OF_FLSS = 12
    K = 3
    R = 1  # ratio of r2 to r1
    H = 2.2  # heuristic 1, 2.1, 2.2, vns, rs
    VNS_TIMEOUT = 0.1
    DROP_PROB_SENDER = 0
    DROP_PROB_RECEIVER = 0
    EXPANSION_TIMEOUT = 0.05
    ETA = K - 1  # initial eta only effective for h:1 and h:rs
    ETA_STR = "k-1"
    FILE_NAME_KEYS = ['K', 'R']
    DIR_KEYS = ['H']
