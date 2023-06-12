class TestConfig:
    ENABLED = True
    NUMBER_OF_FLSS = 12
    K = 4
    R = 10  # ratio of r2 to r1
    H = 'vns'  # heuristic 1, 2, vns, rs
    ETA = 2 * K - 1  # initial eta
    ETA_STR = "2*k-1"
    FILE_NAME_KEYS = ['K', 'R']
    DIR_KEYS = ['H', 'ETA_STR']


if __name__ == "__main__":
    print(TestConfig.ETA)
