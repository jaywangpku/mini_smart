from __future__ import annotations

from dataclasses import dataclass

from .common import trading_day


@dataclass(frozen=True)
class DerivativeFactorPoint:
    time: int
    first_derivative: float | None
    second_derivative: float | None


def compute_derivative_factors(
    candles: list[dict],
    symbol: str,
    n_minutes: int,
    m_minutes: int,
) -> list[DerivativeFactorPoint]:
    if n_minutes <= 0:
        raise ValueError("n_minutes 必须大于 0")
    if m_minutes <= 0:
        raise ValueError("m_minutes 必须大于 0")

    points: list[DerivativeFactorPoint] = []
    current_day: str | None = None
    day_candles: list[dict] = []

    for candle in sorted(candles, key=lambda row: row["time"]):
        day = trading_day(candle["time"], symbol)
        if current_day is None:
            current_day = day
        if day != current_day:
            points.extend(_compute_day(day_candles, n_minutes, m_minutes))
            day_candles = []
            current_day = day
        day_candles.append(candle)

    if day_candles:
        points.extend(_compute_day(day_candles, n_minutes, m_minutes))

    return points


def _compute_day(candles: list[dict], n_minutes: int, m_minutes: int) -> list[DerivativeFactorPoint]:
    first_values: list[float | None] = [None] * len(candles)
    points: list[DerivativeFactorPoint] = []

    for index, candle in enumerate(candles):
        if index >= n_minutes:
            previous_close = candles[index - n_minutes]["close"]
            if previous_close:
                first_values[index] = (candle["close"] - previous_close) / n_minutes

        second_value: float | None = None
        if index >= n_minutes + m_minutes:
            current_first = first_values[index]
            previous_first = first_values[index - m_minutes]
            if current_first is not None and previous_first:
                second_value = (current_first - previous_first) / m_minutes

        points.append(
            DerivativeFactorPoint(
                time=candle["time"],
                first_derivative=first_values[index],
                second_derivative=second_value,
            )
        )

    return points
