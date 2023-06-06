import os
import json
import csv
import shutil

from config import Config
from test_config import TestConfig
import pandas as pd
import glob


def write_json(fid, results, directory):
    with open(os.path.join(directory, 'json', f"{fid:05}.json"), "w") as f:
        json.dump(results, f)


def create_csv_from_json(directory, duration):
    if not os.path.exists(directory):
        return

    headers_set = set()
    rows = []

    json_dir = os.path.join(directory, 'json')
    filenames = os.listdir(json_dir)
    filenames.sort()

    for filename in filenames:
        if filename.endswith('.json'):
            with open(os.path.join(json_dir, filename)) as f:
                try:
                    data = json.load(f)
                    headers_set = headers_set.union(set(list(data.keys())))
                except json.decoder.JSONDecodeError:
                    print(filename)

    headers = list(headers_set)
    headers.sort()
    rows.append(['fid'] + headers)

    weights = []
    min_dists = []
    avg_dists = []
    max_dists = []
    for filename in filenames:
        if filename.endswith('.json'):
            with open(os.path.join(json_dir, filename)) as f:
                try:
                    data = json.load(f)
                    fid = filename.split('.')[0]
                    row = [fid] + [data[h] if h in data else 0 for h in headers]
                    rows.append(row)
                    weights.append(data['5 weight'])
                    min_dists.append(data['1 min dist'])
                    avg_dists.append(data['2 avg dist'])
                    max_dists.append(data['3 max dist'])
                except json.decoder.JSONDecodeError:
                    print(filename)

    with open(os.path.join(directory, 'cliques.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)

    pair_weights = list(filter(lambda x: x != -1, weights))
    pair_min_dists = list(filter(lambda x: x != 0, min_dists))
    pair_avg_dists = list(filter(lambda x: x != 0, avg_dists))
    pair_max_dists = list(filter(lambda x: x != 0, max_dists))

    metrics_rows = [["metric", "value"],
                    ["duration", duration],
                    ["min min_dists", min(pair_min_dists)],
                    ["avg min_dists", sum(pair_min_dists) / len(pair_min_dists)],
                    ["max min_dists", max(pair_min_dists)],
                    ["min avg_dists", min(pair_avg_dists)],
                    ["avg avg_dists", sum(pair_avg_dists) / len(pair_avg_dists)],
                    ["max avg_dists", max(pair_avg_dists)],
                    ["min max_dists", min(pair_max_dists)],
                    ["avg max_dists", sum(pair_max_dists) / len(pair_max_dists)],
                    ["max max_dists", max(pair_max_dists)],
                    ["min weights", min(pair_weights)],
                    ["avg weights", sum(pair_weights) / len(pair_weights)],
                    ["max weights", max(pair_weights)],
                    ["number of cliques", len(pair_weights)],
                    ["number of single nodes", len(list(filter(lambda x: x == -1, weights)))]
                    ]
    with open(os.path.join(directory, 'metrics.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(metrics_rows)


def write_hds_time(hds, directory, nid):
    if not os.path.exists(directory):
        return

    headers = ['timestamp(s)', 'relative_time(s)', 'hd']
    rows = [headers]

    for i in range(len(hds)):
        row = [hds[i][0], hds[i][0] - hds[0][0], hds[i][1]]
        rows.append(row)

    with open(os.path.join(directory, f'hd-n{nid}.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)


def write_hds_round(hds, rounds, directory, nid):
    if not os.path.exists(directory):
        return

    headers = ['round', 'time(s)', 'hd']
    rows = [headers]

    for i in range(len(hds)):
        row = [i+1, rounds[i+1] - rounds[0], hds[i][1]]
        rows.append(row)

    with open(os.path.join(directory, f'hd-n{nid}.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)


def write_swarms(swarms, rounds, directory, nid):
    headers = [
        'timestamp(s)',
        'relative times(s)',
        'num_swarms',
        'average_swarm_size',
        'largest_swarm',
        'smallest_swarm',
    ]

    rows = [headers]

    for i in range(len(swarms)):
        t = swarms[i][0] - rounds[0]
        num_swarms = len(swarms[i][1])
        sizes = swarms[i][1].values()

        row = [swarms[i][0], t, num_swarms, sum(sizes)/num_swarms, max(sizes), min(sizes)]
        rows.append(row)

    with open(os.path.join(directory, f'swarms-n{nid}.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)


def write_configs(directory, date_time):
    headers = ['config', 'value']
    rows = [headers]

    kargs = vars(Config).items()
    if TestConfig.ENABLED:
        kargs = vars(TestConfig).items()

    for k, v in kargs:
        if not k.startswith('__'):
            rows.append([k, v])
    rows.append(["datetime", date_time])

    with open(os.path.join(directory, 'config.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)


def combine_csvs(directory, xslx_dir, file_name):
    csv_files = glob.glob(f"{directory}/*.csv")

    with pd.ExcelWriter(os.path.join(xslx_dir, f'{file_name}.xlsx')) as writer:
        for csv_file in csv_files:
            df = pd.read_csv(csv_file)
            sheet_name = csv_file.split('/')[-1][:-4]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    # shutil.rmtree(os.path.join(directory))
