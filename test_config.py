class TestConfig:
    ENABLED = False
    NUMBER_OF_FLSS = 60
    K = 5
    R = 1  # ratio of r2 to r1
    H = 2  # heuristic 1, 2, vns, rs
    ETA = K - 1  # initial eta only effective for h:1 and h:rs
    ETA_STR = "k-1"
    FILE_NAME_KEYS = ['K']
    DIR_KEYS = ['H']


if __name__ == "__main__":
    print(TestConfig.ETA)
