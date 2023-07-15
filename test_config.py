class TestConfig:
    ENABLED = True
    NUMBER_OF_FLSS = 16
    K = 4
    R = 10  # ratio of r2 to r1
    H = 2  # heuristic 1, 2, vns, rs
    DROP_PROB_SENDER = 0
    DROP_PROB_RECEIVER = 0
    ETA = K - 1  # initial eta only effective for h:1 and h:rs
    ETA_STR = "k-1"
    FILE_NAME_KEYS = ['K', 'R']
    DIR_KEYS = ['H']


if __name__ == "__main__":
    print(TestConfig.ETA)
