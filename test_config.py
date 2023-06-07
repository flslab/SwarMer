class TestConfig:
    ENABLED = True
    NUMBER_OF_FLSS = 12
    K = 3
    R = 100  # ratio of r2 to r1
    H = 1  # heuristic
    ETA = K - 1  # initial eta
    ETA_STR = "k-1"
    FILE_NAME_KEYS = ['K', 'R']
    DIR_KEYS = ['H', 'ETA_STR']


if __name__ == "__main__":
    print(TestConfig.ETA)
