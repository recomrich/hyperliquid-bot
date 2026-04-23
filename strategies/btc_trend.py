"""BTC Trend strategy - optimisée pour la faible volatilité de BTC.

Basée sur des bougies 1h pour filtrer le bruit des 15m.
Conditions strictes pour éviter les faux signaux en range.

BUY:  Prix > EMA200 + EMA20 > EMA50 + MACD croise à la hausse + RSI 45-60
SELL: Prix < EMA200 + EMA20 < EMA50 + MACD croise à la baisse + RSI 35-55

Filtre horaire (UTC) : évite 08h, 15h, 18h (statistiquement perdants sur BTC).
"""

from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
from loguru import logger

from indicators.momentum import rsi
from indicators.trend import add_trend_indicators
from strategies.base_strategy import BaseStrategy, Signal


class BtcTrendStrategy(BaseStrategy):
    """Trend following 1h optimisé BTC avec filtre EMA200 et RSI."""

    def __init__(self, params: dict | None = None) -> None:
        params = params or {}
        timeframe = params.get("timeframe", "1h")
        super().__init__("btc_trend", timeframe, params)
        self._ema_periods = params.get("ema_periods", [20, 50, 200])
        self._rsi_buy_min = params.get("rsi_buy_min", 45)
        self._rsi_buy_max = params.get("rsi_buy_max", 60)
        self._rsi_sell_min = params.get("rsi_sell_min", 35)
        self._rsi_sell_max = params.get("rsi_sell_max", 55)
        self._bad_hours_utc = params.get("bad_hours_utc", [8, 15, 18])

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        if len(df) < max(self._ema_periods) + 10:
            return Signal.HOLD

        # Filtre horaire : heures statistiquement perdantes sur BTC (UTC)
        current_hour = datetime.now(timezone.utc).hour
        if current_hour in self._bad_hours_utc:
            return Signal.HOLD

        data = add_trend_indicators(df, self._ema_periods)
        rsi_vals = rsi(df)

        latest = data.iloc[-1]
        prev = data.iloc[-2]

        ema_20 = latest.get("EMA_20")
        ema_50 = latest.get("EMA_50")
        ema_200 = latest.get("EMA_200")
        macd_val = latest.get("MACD")
        macd_signal = latest.get("MACD_Signal")
        prev_macd = prev.get("MACD")
        prev_macd_signal = prev.get("MACD_Signal")
        close = latest.get("close")

        if any(pd.isna(v) for v in [ema_20, ema_50, ema_200, macd_val, macd_signal,
                                      prev_macd, prev_macd_signal, close]):
            return Signal.HOLD

        current_rsi = float(rsi_vals.iloc[-1]) if not rsi_vals.empty else 50
        if pd.isna(current_rsi):
            return Signal.HOLD

        # MACD crossover (plus fiable qu'un simple MACD > signal)
        macd_crossed_up = prev_macd <= prev_macd_signal and macd_val > macd_signal
        macd_crossed_down = prev_macd >= prev_macd_signal and macd_val < macd_signal

        # BUY: prix au-dessus EMA200 + EMA haussières + MACD croise + RSI sain
        if (
            close > ema_200
            and ema_20 > ema_50
            and macd_crossed_up
            and self._rsi_buy_min <= current_rsi <= self._rsi_buy_max
        ):
            self._signal_count += 1
            logger.info(
                f"[{self.name}] BUY - prix={close:.0f} > EMA200={ema_200:.0f}, "
                f"EMA20={ema_20:.0f} > EMA50={ema_50:.0f}, "
                f"MACD crossover ↑, RSI={current_rsi:.1f}"
            )
            return Signal.BUY

        # SELL: prix en-dessous EMA200 + EMA baissières + MACD croise + RSI sain
        if (
            close < ema_200
            and ema_20 < ema_50
            and macd_crossed_down
            and self._rsi_sell_min <= current_rsi <= self._rsi_sell_max
        ):
            self._signal_count += 1
            logger.info(
                f"[{self.name}] SELL - prix={close:.0f} < EMA200={ema_200:.0f}, "
                f"EMA20={ema_20:.0f} < EMA50={ema_50:.0f}, "
                f"MACD crossover ↓, RSI={current_rsi:.1f}"
            )
            return Signal.SELL

        return Signal.HOLD

    def get_stop_loss(self, entry_price: float, atr_value: float, side: str = "buy") -> float:
        """2x ATR — plus large pour laisser BTC respirer sur 1h."""
        if side == "buy":
            return round(entry_price - (atr_value * 2.0), 2)
        return round(entry_price + (atr_value * 2.0), 2)

    def get_take_profit(self, entry_price: float, atr_value: float, side: str = "buy") -> float:
        """Pas utilisé — trailing stop gère la sortie."""
        if side == "buy":
            return round(entry_price + (atr_value * 4.0), 2)
        return round(entry_price - (atr_value * 4.0), 2)
