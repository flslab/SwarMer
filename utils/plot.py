import math

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.animation as animation
from multiprocessing import shared_memory
import numpy as np
import scipy
from matplotlib import rcParams, pylab
from matplotlib import ticker


# mpl.use('macosx')


def plot_point_cloud(ptcld):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.scatter(ptcld[:, 0], ptcld[:, 1], ptcld[:, 2])
    plt.show()


def update(num, graph, shm_name, count):
    shared_mem = shared_memory.SharedMemory(name=shm_name)
    shared_array = np.ndarray((count, 3), dtype=np.float64, buffer=shared_mem.buf)
    # print(graph._offsets3d)
    graph._offsets3d = (shared_array[:, 0], shared_array[:, 1], shared_array[:, 2])
    return graph,


def quad():
    # pylab.rcParams['xtick.major.pad'] = '1'
    # pylab.rcParams['ytick.major.pad'] = '1'
    # pylab.rcParams['ztick.major.pad'] = '8'
    shapes = ['chess', 'dragon', 'skateboard', 'racecar']
    title_offset = [-.25, -.25, -.02, -.02]
    shapes_labels = ['a) Chess piece\n454 points', 'b) Dragon\n760 points', 'c) Skateboard\n1,727 points', 'd) Race car\n11,894 points']
    fig = plt.figure(figsize=(5, 5))

    for i, shape in enumerate(shapes):
        mat = scipy.io.loadmat(f'../assets/{shapes[i]}.mat')
        ptcld = mat['p']

        ticks_gap = 10
        length = math.ceil(np.max(ptcld[:, 0]) / ticks_gap) * ticks_gap
        width = math.ceil(np.max(ptcld[:, 1]) / ticks_gap) * ticks_gap
        height = math.ceil(np.max(ptcld[:, 2]) / ticks_gap) * ticks_gap
        ax = fig.add_subplot(2, 2, i + 1, projection='3d', proj_type='ortho')
        ax.scatter(ptcld[:, 0], ptcld[:, 1], ptcld[:, 2], c='blue', s=1, alpha=1, edgecolors='none')
        ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax.zaxis.set_pane_color((0, 0, 0, 0.025))
        ax.view_init(elev=16, azim=137, roll=0)
        ax.axes.set_xlim3d(left=1, right=length)
        ax.axes.set_ylim3d(bottom=1, top=width)
        ax.axes.set_zlim3d(bottom=1, top=height)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(length))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(width))
        ax.zaxis.set_major_locator(ticker.MultipleLocator(height))
        ax.set_aspect('equal')
        ax.grid(False)
        # ax.set_xticks(range(0, length + 1, length))
        # ax.set_yticks(range(0, width + 1, width))
        # ax.set_zticks(range(0, height + 1, height))
        ax.tick_params(pad=-2)
        ax.tick_params(axis='x', pad=-6)
        ax.tick_params(axis='y', pad=-6)
        ax.set_title(shapes_labels[i], y=title_offset[i])

    plt.margins(x=0, y=0)
    plt.tight_layout()
    # plt.show()
    plt.savefig(f'/Users/hamed/Desktop/4_shapes.png', dpi=300)


def p_rs(F, G, eta):
    return math.comb(F - 1 - (G - 1), eta - (G - 1)) / math.comb(F - 1, eta)


def rs_probability():
    fig = plt.figure(figsize=[4, 3])
    ax = fig.add_subplot()

    # RS probability, SZ=G-1, y-axis is the P, x-axis is G 2, to 10 or 15
    xs = [2, 3, 5, 6, 7, 8, 9, 10]
    ys_30 = [p_rs(F=30, G=g, eta=g-1) for g in xs]
    ys_60 = [p_rs(F=60, G=g, eta=g-1) for g in xs]
    ys_90 = [p_rs(F=90, G=g, eta=g-1) for g in xs]

    ax.plot(xs, ys_30)
    ax.plot(xs, ys_60)
    ax.plot(xs, ys_90, color='tab:purple')
    plt.text(xs[-1]-1, ys_30[-1]*4, 'F=30', color='tab:blue')
    plt.text(xs[-1]-1, ys_60[-1]*8, 'F=60', color='tab:orange')
    plt.text(xs[-1]-1, ys_90[-1]*10, 'F=90', color='tab:purple')
    ax.set_yscale('log')
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.set_ylim([1e-13, 1])
    ax.set_ylabel('Probability', loc='top', rotation=0, labelpad=-50)
    ax.set_xlabel('G', loc='right')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    plt.tight_layout()
    # plt.show()
    plt.savefig('/Users/hamed/Desktop/rs_prop_f30_f60_f90_g.png', dpi=300)


def rs_probability_2():
    fig = plt.figure(figsize=[4, 3])
    ax = fig.add_subplot()

    # RS probability, SZ=G-1, y-axis is the P, x-axis is G 2, to 10 or 15
    xs = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    ys_3 = [p_rs(F=f, G=3, eta=3-1) for f in xs]
    ys_5 = [p_rs(F=f, G=5, eta=5-1) for f in xs]
    ys_10 = [p_rs(F=f, G=10, eta=10-1) for f in xs]

    ax.plot(xs, ys_3)
    ax.plot(xs, ys_5)
    ax.plot(xs, ys_10, color='tab:purple')
    plt.text(xs[-1] - 10, ys_3[-1] * 4, 'G=3', color='tab:blue')
    plt.text(xs[-1] - 10, ys_5[-1] * 5, 'G=5', color='tab:orange')
    plt.text(xs[-1] - 10, ys_10[-1] * 7, 'G=10', color='tab:purple')
    ax.set_yscale('log')
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    # ax.yaxis.set_major_locator(ticker.MultipleLocator(lambda x: x*10))

    # y_formatter = ticker.FixedFormatter(["-1e7", "111", "007", "xkcd"])
    y_locator = ticker.FixedLocator([1e-13, 1e-11, 1e-9, 1e-7, 1e-5, 1e-3, 1e-1, 1])
    # ax.yaxis.set_major_formatter(y_formatter)
    ax.yaxis.set_major_locator(y_locator)

    ax.set_ylim([1e-13, 10])
    ax.set_ylabel('Probability', loc='top', rotation=0, labelpad=-50)
    ax.set_xlabel('F', loc='right')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    plt.tight_layout()
    # plt.show()
    plt.savefig('/Users/hamed/Desktop/rs_prop_g3_g5_g10_f.png', dpi=300)


if __name__ == '__main__':
    rcParams['font.family'] = 'Times New Roman'
    mpl.use('macosx')
    rs_probability_2()
