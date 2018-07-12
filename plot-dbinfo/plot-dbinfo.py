#!/usr/bin/env python

import json
import numpy as np
import operator
import matplotlib.pyplot as plt


result = {}


def read_json(filename):
    if filename:
        with open(filename, 'r') as f:
            return json.load(f)


def main():
    datastore = read_json("tags.json")
    for d in datastore:
        if d["title"] in result:
            continue
        side = d.get("side", None)
        if side is None:
            continue
        numbers = side.get("tag_info", None)
        if numbers is None or len(numbers) == 0:
            continue
        sum = 0
        for v in numbers.values():
            sum += int(v[0])

        result[d["title"]] = sum
    raw_values = list(result.values())
    sorted_d = sorted(result.items(), key=operator.itemgetter(1))
    print(sorted_d[:1000])
    mean = np.mean(raw_values)
    std = np.std(raw_values)
    print(mean, std)
    plt.plot(range(len(sorted_d)), [a[1] for a in sorted_d])
    plt.plot(range(len(sorted_d)), [mean for a in sorted_d])
    plt.axis([0, len(sorted_d), 0, 400845])

    plt.show()


if __name__ == '__main__':
    main()
