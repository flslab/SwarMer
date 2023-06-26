import math
import heapq
import numpy as np
from config import Config
import matplotlib.pyplot as plt


class MetricTypes:
    RECEIVED_MASSAGES = 0
    SENT_MESSAGES = 1
    DROPPED_MESSAGES = 2
    FAILURES = 3


class TimelineEvents:
    DISPATCH = 0
    ILLUMINATE = 1
    STANDBY = 2
    FAIL = 3
    REPLACE = 4


def update_dict_sum(obj, key):
    if key in obj:
        obj[key] += 1
    else:
        obj[key] = 1


def log_msg_hist(hist, msg_type, label, cat):
    key_number = f'{cat}0_num_{label}_{msg_type.name}'
    # key_num_cat = f'{cat}1_cat_num_{label}_{msg_type.get_cat()}'

    update_dict_sum(hist, key_number)
    # update_dict_sum(hist, key_num_cat)


def get_messages_histogram(msgs, label, cat):
    hist = dict()

    for msg_hist in msgs:
        msg_type = msg_hist.value
        log_msg_hist(hist, msg_type, label, cat)

    return hist


def merge_timelines(timelines):
    lists = timelines
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heap.append((lst[0][0], i, 0))
    heapq.heapify(heap)

    merged = []
    while heap:
        val, lst_idx, elem_idx = heapq.heappop(heap)
        merged.append(lists[lst_idx][elem_idx])
        if elem_idx + 1 < len(lists[lst_idx]):
            next_elem = lists[lst_idx][elem_idx + 1][0]
            heapq.heappush(heap, (next_elem, lst_idx, elem_idx + 1))
    gen_charts(merged)
    return merged


def gen_charts(events):
    dispatched = {"t": [0], "y": [0]}
    standby = {"t": [0], "y": [0]}
    illuminating = {"t": [0], "y": [0]}
    failed = {"t": [0], "y": [0]}
    mid_flight = {"t": [0], "y": [0]}

    for t, e in events:
        if e == TimelineEvents.DISPATCH:
            dispatched["t"].append(t)
            dispatched["y"].append(dispatched["y"][-1] + 1)
            mid_flight["t"].append(t)
            mid_flight["y"].append(mid_flight["y"][-1] + 1)
        elif e == TimelineEvents.ILLUMINATE:
            illuminating["t"].append(t)
            illuminating["y"].append(illuminating["y"][-1] + 1)
            mid_flight["t"].append(t)
            mid_flight["y"].append(mid_flight["y"][-1] - 1)
        elif e == TimelineEvents.STANDBY:
            standby["t"].append(t)
            standby["y"].append(standby["y"][-1] + 1)
            mid_flight["t"].append(t)
            mid_flight["y"].append(mid_flight["y"][-1] - 1)
        elif e == TimelineEvents.FAIL:
            failed["t"].append(t)
            failed["y"].append(failed["y"][-1] + 1)
            illuminating["t"].append(t)
            illuminating["y"].append(illuminating["y"][-1] - 1)
        elif e == TimelineEvents.REPLACE:
            mid_flight["t"].append(t)
            mid_flight["y"].append(mid_flight["y"][-1] + 1)
            standby["t"].append(t)
            standby["y"].append(standby["y"][-1] - 1)

    dispatched["t"].append(events[-1][0])
    dispatched["y"].append(dispatched["y"][-1])
    standby["t"].append(events[-1][0])
    standby["y"].append(standby["y"][-1])
    illuminating["t"].append(events[-1][0])
    illuminating["y"].append(illuminating["y"][-1])
    failed["t"].append(events[-1][0])
    failed["y"].append(failed["y"][-1])
    mid_flight["t"].append(events[-1][0])
    mid_flight["y"].append(mid_flight["y"][-1])

    print(dispatched["t"], dispatched["y"])
    plt.step(dispatched["t"], dispatched["y"], where='post', label="Dispatched FLSs")
    plt.step(standby["t"], standby["y"], where='post', label="Standby FLSs")
    plt.step(illuminating["t"], illuminating["y"], where='post', label="Illuminating FLSs")
    plt.step(failed["t"], failed["y"], where='post', label="Failed FLSs")
    plt.step(mid_flight["t"], mid_flight["y"], where='post', label="Mid-flight FLSs")

    # Add a legend
    plt.legend()
    if Config.DEBUG:
        plt.show()
    # else:
    #     plt.savefig(os.path.join(figure_directory, f'{file_name}.jpg'))


class Metrics:
    def __init__(self, history, results_directory, start_time):
        self.results_directory = results_directory
        self.history = history
        self.start_time = start_time
        self.timeline = []
        self.general_metrics = {
            "00_gtl": None,
            "01_is_standby": [],
            "02_group_id": 0,
            "03_radio_range": 0,
            "04_group_members": [],  # (time, set)
            "05_standby_id": [],  # (time, id)
            "10_dispatch_time": -1,
            "12_arrival_time": -1,
            "13_dispatch_duration": -1,
            "30_failure_time": -1,
            "31_replacement_start_time": -1,
            "32_replacement_arrival_time": -1,
            "33_replacement_duration": -1,
            "34_failed_fls_id": -1,
            "20_total_distance_traveled": 0,
            "21_bytes_sent": 0,
            "22_bytes_received": 0,
            "23_num_messages_sent": 0,
            "24_num_messages_received": 0,
            # "A4_num_dropped_messages": 0,
        }
        self.sent_msg_hist = {}
        self.received_msg_hist = {}

    def log_sum(self, key, value):
        self.general_metrics[key] += value

    def log_max(self, key, value):
        self.general_metrics[key] = max(self.general_metrics[key], value)

    def log_min(self, key, value):
        self.general_metrics[key] = min(self.general_metrics[key], value)

    def log_received_msg(self, msg_type, length):
        log_msg_hist(self.received_msg_hist, msg_type, 'received', 'C')
        self.log_sum("24_num_messages_received", 1)
        self.log_sum("22_bytes_received", length)

    def log_sent_msg(self, msg_type, length):
        log_msg_hist(self.sent_msg_hist, msg_type, 'sent', 'B')
        self.log_sum("23_num_messages_sent", 1)
        self.log_sum("21_bytes_sent", length)

    def get_total_distance(self):
        way_points = self.get_location_history()
        total_dist = 0
        for i in range(len(way_points) - 1):
            d = np.linalg.norm(way_points[i+1].value - way_points[i].value)
            total_dist += d

        return total_dist

    def get_total_bytes_sent(self):
        return sum([s.meta["length"] for s in self.get_sent_messages()])

    def get_total_bytes_received(self):
        return sum([s.meta["length"] for s in self.get_received_messages()])

    def get_sent_messages_histogram(self):
        return get_messages_histogram(self.get_sent_messages(), 'sent', 'B')

    def get_received_messages_histogram(self):
        return get_messages_histogram(self.get_received_messages(), 'received', 'C')

    def get_location_history(self):
        return self.history[MetricTypes.LOCATION]

    def get_received_messages(self):
        return self.history[MetricTypes.RECEIVED_MASSAGES]

    def get_sent_messages(self):
        return self.history[MetricTypes.SENT_MESSAGES]

    def get_dropped_messages(self):
        return sum(self.history[MetricTypes.DROPPED_MESSAGES])

    def get_failures(self):
        return self.history[MetricTypes.FAILURES]

    def get_final_report_(self):
        report = {
            "timeline": self.timeline
        }
        report.update(self.general_metrics)
        report.update(self.sent_msg_hist)
        report.update(self.received_msg_hist)
        return report

    def get_final_report(self):
        report = {
            "A4_bytes_sent": sum([s.meta["length"] for s in self.get_sent_messages()]),
            "A4_bytes_received": sum([r.meta["length"] for r in self.get_received_messages()]),
            "A4_num_messages_sent": len(self.get_sent_messages()),
            "A4_num_messages_received": len(self.get_received_messages()),
            "A4_num_dropped_messages": self.get_dropped_messages(),
        }
        report.update(self.get_sent_messages_histogram())
        report.update(self.get_received_messages_histogram())

        return report

    def log_initial_metrics(self, gtl, is_standby, group_id, radio_range, group_members, standby_id,
                            timestamp, dispatch_duration):
        t = timestamp - self.start_time
        self.general_metrics["00_gtl"] = gtl.tolist()
        self.general_metrics["02_group_id"] = group_id
        self.general_metrics["03_radio_range"] = radio_range
        self.general_metrics["10_dispatch_time"] = t
        self.general_metrics["12_arrival_time"] = t + dispatch_duration
        self.general_metrics["13_dispatch_duration"] = dispatch_duration
        self.log_group_members(timestamp, group_members)
        self.log_standby_id(timestamp, standby_id)
        self.log_is_standby(timestamp, is_standby)
        self.timeline.append((t, TimelineEvents.DISPATCH))
        if is_standby:
            self.timeline.append((t + dispatch_duration, TimelineEvents.STANDBY))
        else:
            self.timeline.append((t + dispatch_duration, TimelineEvents.ILLUMINATE))

    def log_group_members(self, timestamp, group_members):
        self.general_metrics["04_group_members"].append((timestamp - self.start_time, tuple(group_members)))

    def log_standby_id(self, timestamp, standby_id):
        self.general_metrics["05_standby_id"].append((timestamp - self.start_time, standby_id))

    def log_is_standby(self, timestamp, is_standby):
        self.general_metrics["01_is_standby"].append((timestamp - self.start_time, is_standby))

    def log_failure_time(self, timestamp):
        t = timestamp - self.start_time
        self.general_metrics["30_failure_time"] = t
        self.timeline.append((t, TimelineEvents.FAIL))

    def log_replacement(self, replacement_time, replacement_duration, failed_fls_id):
        t = replacement_time - self.start_time
        self.general_metrics["31_replacement_start_time"] = t
        self.general_metrics["32_replacement_arrival_time"] = t + replacement_duration
        self.general_metrics["33_replacement_duration"] = replacement_duration
        self.general_metrics["34_failed_fls_id"] = failed_fls_id
        self.timeline.append((t, TimelineEvents.REPLACE))
        self.timeline.append((t + replacement_duration, TimelineEvents.ILLUMINATE))
