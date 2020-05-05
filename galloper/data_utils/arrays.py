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
            index += 1
            if x > (y + y * deviation):
                return y, index
        else:
            return data[-1], index


def monotonic(data):
    return non_increasing(data) or non_decreasing(data)


def within_bounds(data, bound):
    return all(x <= bound for x in data)
