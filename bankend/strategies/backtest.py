from __future__ import annotations

import math
from typing import Any


def run_backtest(candles: list[dict], signals: list[dict], options: dict[str, Any]) -> dict:
    initial_cash = float(options.get("initial_cash", 100000))
    fee_rate = max(0.0, float(options.get("fee_rate", 0.0003)))
    slippage_rate = max(0.0, float(options.get("slippage_rate", 0.0002)))
    cash = initial_cash
    position = 0.0
    open_lots: list[dict] = []
    trades: list[dict] = []
    equity_curve: list[dict] = []
    signal_by_time: dict[int, list[dict]] = {}

    for signal in signals:
        signal_by_time.setdefault(int(signal["time"]), []).append(signal)

    peak = initial_cash
    max_drawdown = 0.0

    for candle in sorted(candles, key=lambda row: row["time"]):
        close = float(candle["close"])
        for signal in signal_by_time.get(int(candle["time"]), []):
            action = str(signal.get("action", "")).lower()
            quantity = float(signal.get("quantity") or 0)
            if quantity <= 0:
                continue
            base_price = float(signal.get("price") or close)
            if not math.isfinite(base_price) or base_price <= 0:
                continue

            if action == "buy":
                price = base_price * (1 + slippage_rate)
                max_quantity = math.floor(cash / (price * (1 + fee_rate)))
                executed = min(quantity, max_quantity)
                if executed <= 0:
                    continue
                fee = executed * price * fee_rate
                cash -= executed * price + fee
                position += executed
                open_lots.append({"time": candle["time"], "price": price, "quantity": executed, "fee": fee})
                signal["price"] = price
                signal["executed_quantity"] = executed
                signal["fee"] = fee

            elif action == "sell":
                executed = min(quantity, position)
                if executed <= 0:
                    continue
                price = base_price * (1 - slippage_rate)
                fee = executed * price * fee_rate
                cash += executed * price - fee
                position -= executed
                signal["price"] = price
                signal["executed_quantity"] = executed
                signal["fee"] = fee

                remaining = executed
                while remaining > 0 and open_lots:
                    lot = open_lots[0]
                    matched = min(remaining, lot["quantity"])
                    buy_cost = matched * lot["price"]
                    sell_value = matched * price
                    buy_fee = lot["fee"] * (matched / lot["quantity"]) if lot["quantity"] else 0
                    sell_fee = fee * (matched / executed) if executed else 0
                    pnl = sell_value - sell_fee - buy_cost - buy_fee
                    trades.append(
                        {
                            "buy_time": lot["time"],
                            "sell_time": candle["time"],
                            "quantity": matched,
                            "buy_price": lot["price"],
                            "sell_price": price,
                            "pnl": pnl,
                            "return_pct": pnl / buy_cost if buy_cost else None,
                        }
                    )
                    lot["quantity"] -= matched
                    lot["fee"] -= buy_fee
                    remaining -= matched
                    if lot["quantity"] <= 0:
                        open_lots.pop(0)

        value = cash + position * close
        peak = max(peak, value)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - value) / peak)
        equity_curve.append({"time": candle["time"], "value": value, "cash": cash, "position": position})

    final_value = equity_curve[-1]["value"] if equity_curve else initial_cash
    wins = [trade for trade in trades if trade["pnl"] > 0]
    return {
        "signals": signals,
        "trades": trades,
        "equity_curve": equity_curve,
        "summary": {
            "initial_cash": initial_cash,
            "final_value": final_value,
            "cash": cash,
            "position": position,
            "total_return_pct": (final_value - initial_cash) / initial_cash if initial_cash else None,
            "trade_count": len(trades),
            "win_rate": len(wins) / len(trades) if trades else None,
            "max_drawdown_pct": max_drawdown,
        },
    }
