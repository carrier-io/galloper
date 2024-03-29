def strictly_increasing(data):
    return all(x < y for x, y in zip(data, data[1:]))


def strictly_decreasing(data):
    return all(x > y for x, y in zip(data, data[1:]))


def non_increasing(data):
    return all(x >= y for x, y in zip(data, data[1:]))


def non_decreasing(data, deviation=None, val=False):
    if not deviation:
        deviation = 0
    if not val:
        return all(x <= (y + y * deviation) for x, y in zip(data, data[1:]))
    else:
        index = 0
        for x, y in zip(data, data[1:]):
            if y == 0:
                continue
            index += 1
            if x > (y + y * deviation):
                return y, index
        else:
            if int(data[-1]) != 0:
                return data[-1], index
            else:
                return max(data), data.index(max(data))


def monotonic(data):
    return non_increasing(data) or non_decreasing(data)


def within_bounds(data, bound):
    return all(x <= bound for x in data)


def get_aggregated_data(aggregation, values, metric="total"):
    totals = [d.to_json()[metric] for d in values]
    if aggregation == "max":
        return max(totals)
    elif aggregation == "min":
        return min(totals)
    elif aggregation == "avg":
        return sum(totals) / len(totals)


def closest(lst, val):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i].total - val))]
