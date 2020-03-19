def strictly_increasing(data):
    return all(x < y for x, y in zip(data, data[1:]))


def strictly_decreasing(data):
    return all(x > y for x, y in zip(data, data[1:]))


def non_increasing(data):
    return all(x >= y for x, y in zip(data, data[1:]))


def non_decreasing(data):
    return all(x <= y for x, y in zip(data, data[1:]))


def monotonic(data):
    return non_increasing(data) or non_decreasing(data)


def within_bounds(data, bound):
    return all(x <= bound for x in data)
