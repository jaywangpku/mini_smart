from __future__ import annotations


FIRST_DERIVATIVE_SOURCE = '''def compute(candles, params):
    n = int(params.get("n", params.get("step", 5)))
    result = []
    for index, row in enumerate(candles):
        if index < n:
            result.append({"time": row["time"], "value": None})
            continue
        previous = candles[index - n]["close"]
        value = (row["close"] - previous) / previous if previous else None
        result.append({"time": row["time"], "value": value})
    return result
'''


SECOND_DERIVATIVE_SOURCE = '''def compute(candles, params):
    n = int(params.get("n", 5))
    m = int(params.get("m", params.get("step", 5)))
    first_values = []
    result = []

    for index, row in enumerate(candles):
        first = None
        if index >= n:
            previous_close = candles[index - n]["close"]
            first = (row["close"] - previous_close) / previous_close if previous_close else None
        first_values.append(first)

        second = None
        if index >= n + m:
            previous_first = first_values[index - m]
            if first is not None and previous_first:
                second = (first - previous_first) / previous_first
        result.append({"time": row["time"], "value": second})

    return result
'''
