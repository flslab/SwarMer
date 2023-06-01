import numpy as np
from scipy.spatial import distance


def knn(points, k=1):
    d = distance.squareform(distance.pdist(points))
    closest = np.argsort(d, axis=1)
    return closest, np.take_along_axis(d, closest, 1)


if __name__ == "__main__":
    pts = np.random.rand(200, 3)
    print(np.round(pts, 1))

    idx, dist = knn(pts, 4)
    print(np.round(idx, 1))
    print(np.round(dist, 1))

