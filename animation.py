import json
import math

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import matplotlib as mpl
from worker.metrics import TimelineEvents

mpl.use('macosx')

height = 0
width = 0
length = 0
ticks_gap = 20

start_time = 0
duration = 20
fps = 30
frame_rate = 1/fps
total_points = 11888

output_name = "racecar_g10_c1_d1"
input_path = "/Users/hamed/Desktop/racecar_k10_5min/28-Jun-14_23_04/timeline.json"


def set_axis():
    ax.axes.set_xlim3d(left=0, right=length)
    ax.axes.set_ylim3d(bottom=0, top=width)
    ax.axes.set_zlim3d(bottom=0, top=height)
    ax.set_aspect('equal')
    ax.grid(False)
    ax.set_xticks(range(0, length+1, ticks_gap))
    ax.set_yticks(range(0, width+1, ticks_gap))
    ax.set_zticks(range(0, height+1, ticks_gap))


def set_text(t, missing_flss):
    tx.set(text=f"Elapsed time: {int(t)} seconds\nNumber of missing FLSs: {missing_flss}")


px = 1/plt.rcParams['figure.dpi']
fig_width = 1280*px
fig_height = 720*px
fig = plt.figure(figsize=(fig_width, fig_height))
ax = fig.add_subplot(projection='3d')
tx = fig.text(0.1, 0.8, s="", fontsize=16)
line1 = ax.scatter([], [], [])

with open(input_path) as f:
    events = json.load(f)

filtered_events = []
for e in events:
    if e[1] == TimelineEvents.FAIL:
        filtered_events.append(e)
    elif e[1] == TimelineEvents.ILLUMINATE:
        filtered_events.append(e)
        length = max(int(e[2][0]), length)
        width = max(int(e[2][1]), width)
        height = max(int(e[2][2]), height)
length = math.ceil(length / ticks_gap) * ticks_gap
width = math.ceil(width / ticks_gap) * ticks_gap
height = math.ceil(height / ticks_gap) * ticks_gap
points = {}

print(length)
print(width)


def init():
    ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax.zaxis.set_pane_color((0, 0, 0, 0.025))
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
    ax.scatter(xs, ys, zs, c='blue', s=2, alpha=1)
    set_axis()
    set_text(t, total_points - len(coords))
    return line1,


if __name__ == '__main__':
    ani = FuncAnimation(
        fig, update,
        frames=30 * duration,
        init_func=init)

    plt.show()
    # writer = FFMpegWriter(fps=fps)
    # ani.save(f"results/{output_name}.mp4", writer=writer)
