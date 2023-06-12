class TestConfig:
    ENABLED = True
    NUMBER_OF_FLSS = 165
    K = 3
    R = 10  # ratio of r2 to r1
    H = 2  # heuristic 1, 2, vns, rs
    ETA = K - 1  # initial eta
    ETA_STR = "k-1"
    FILE_NAME_KEYS = ['K', 'R']
    DIR_KEYS = ['H', 'ETA_STR']


if __name__ == "__main__":
    print(TestConfig.ETA)
