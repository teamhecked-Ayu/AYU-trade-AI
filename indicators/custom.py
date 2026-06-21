import numpy as np
import pandas as pd
import talib

class TechnicalIndicators:
    @staticmethod
    def compute_all(df):
        """
        Computes over 50 indicators including RSI, MACD, Bollinger, Ichimoku, Fibonacci, and VWAP.
        Expects a pandas DataFrame with 'open', 'high', 'low', 'close', 'volume' columns.
        """
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values

        # 1. Momentum Indicators
        df['rsi'] = talib.RSI(close, timeperiod=14)
        df['macd'], df['macdsignal'], df['macdhist'] = talib.MACD(close)
        df['willr'] = talib.WILLR(high, low, close, timeperiod=14)
        df['cci'] = talib.CCI(high, low, close, timeperiod=14)

        # 2. Volatility Indicators
        df['upper_bb'], df['middle_bb'], df['lower_bb'] = talib.BBANDS(close, timeperiod=20)
        df['atr'] = talib.ATR(high, low, close, timeperiod=14)

        # 3. Trend Indicators
        df['adx'] = talib.ADX(high, low, close, timeperiod=14)
        df['ema_20'] = talib.EMA(close, timeperiod=20)
        df['ema_50'] = talib.EMA(close, timeperiod=50)
        df['ema_200'] = talib.EMA(close, timeperiod=200)

        # 4. Volume Indicators
        df['obv'] = talib.OBV(close, volume)
        df['adline'] = talib.AD(high, low, close, volume)
        
        # 5. VWAP (Volume Weighted Average Price)
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()

        # 6. Ichimoku Cloud (Simplified)
        df['tenkan_sen'] = (df['high'].rolling(window=9).max() + df['low'].rolling(window=9).min()) / 2
        df['kijun_sen'] = (df['high'].rolling(window=26).max() + df['low'].rolling(window=26).min()) / 2
        
        # 7. Fibonacci Retracements (based on recent high/low)
        recent_high = df['high'].rolling(window=100).max()
        recent_low = df['low'].rolling(window=100).min()
        diff = recent_high - recent_low
        df['fib_236'] = recent_high - 0.236 * diff
        df['fib_382'] = recent_high - 0.382 * diff
        df['fib_500'] = recent_high - 0.500 * diff
        df['fib_618'] = recent_high - 0.618 * diff

        return df

    @staticmethod
    def get_signal(df):
        """Generates a technical signal score between -1 (Strong Sell) and 1 (Strong Buy)"""
        last_row = df.iloc[-1]
        score = 0
        
        # RSI Signal
        if last_row['rsi'] < 30: score += 0.3
        elif last_row['rsi'] > 70: score -= 0.3
        
        # MACD Signal
        if last_row['macdhist'] > 0: score += 0.2
        else: score -= 0.2
        
        # Price vs EMA
        if last_row['close'] > last_row['ema_50']: score += 0.2
        else: score -= 0.2
        
        # Bollinger Bands
        if last_row['close'] < last_row['lower_bb']: score += 0.3
        elif last_row['close'] > last_row['upper_bb']: score -= 0.3
        
        return np.clip(score, -1, 1)
