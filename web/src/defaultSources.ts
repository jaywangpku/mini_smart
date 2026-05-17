export function defaultFactorSource() {
  return `def compute(candles, params):
    n = int(params.get("n", 5))
    result = []
    for index, row in enumerate(candles):
        if index < n:
            result.append({"time": row["time"], "value": None})
            continue
        previous = candles[index - n]["close"]
        value = (row["close"] - previous) / previous if previous else None
        result.append({"time": row["time"], "value": value})
    return result
`
}

export function defaultStrategySource() {
  return `def generate_signals(ctx, params):
    buy_size = int(params.get("buy_size", 100))
    threshold = float(params.get("threshold", 0.01))
    first = ctx.factor("first_derivative", {"n": int(params.get("n", 5))})
    signals = []
    holding = False

    for index, row in enumerate(ctx.candles):
        value = first[index]["value"]
        if value is None:
            continue
        if not holding and value > threshold:
            signals.append({
                "time": row["time"],
                "action": "buy",
                "quantity": buy_size,
                "reason": "一阶导向上突破"
            })
            holding = True
        elif holding and value < 0:
            signals.append({
                "time": row["time"],
                "action": "sell",
                "quantity": buy_size,
                "reason": "一阶导转负"
            })
            holding = False
    return signals
`
}
