import json

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import matplotlib as mpl
from worker.metrics import TimelineEvents

mpl.use('macosx')


def set_axis():
    ax.axes.set_xlim3d(left=0, right=99.999)
    ax.axes.set_ylim3d(bottom=0, top=99.999)
    ax.axes.set_zlim3d(bottom=0, top=99.999)
    ax.set_aspect('equal')


fig = plt.figure()
ax = fig.add_subplot(projection='3d')
line1 = ax.scatter([], [], [], 'ro')
set_axis()

with open("/Users/hamed/Desktop/dragon_k10_2m/27-Jun-15_42_50/timeline.json") as f:
    events = json.load(f)

start_time = 0
fps = 30
frame_rate = 1/fps
filtered_events = list(filter(lambda e: e[1] == TimelineEvents.ILLUMINATE or e[1] == TimelineEvents.FAIL, events))
points = {}


def init():
    ax.axes.set_xlim3d(left=0, right=99.999)
    ax.axes.set_ylim3d(bottom=0, top=99.999)
    ax.axes.set_zlim3d(bottom=0, top=99.999)
    ax.set_aspect('equal')
    return line1,


def update(frame):
    t = start_time + frame * frame_rate
    while len(filtered_events):
        # print(t)
        event_time = filtered_events[0][0]
        if event_time <= t:
            event = filtered_events.pop(0)
            event_type = event[1]
            fls_id = event[-1]
            if event_type == TimelineEvents.ILLUMINATE:
                points[fls_id] = event[2]
            else:
                points.pop(fls_id)
        else:
            t += frame_rate
            break
    coords = points.values()
    ax.clear()
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    zs = [c[2] for c in coords]
    ax.scatter(xs, ys, zs, 'o')
    set_axis()
    return line1,


if __name__ == '__main__':
    ani = FuncAnimation(
        fig, update,
        frames=30 * 120,
        init_func=init)

    plt.show()
    # writer = FFMpegWriter(fps=fps)
    # ani.save("./test.mp4", writer=writer)
