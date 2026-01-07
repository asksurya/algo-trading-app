"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv_data():
    """
    Generate realistic OHLCV data for testing strategies.

    Returns 100 days of data with realistic price movements.
    """
    np.random.seed(42)  # For reproducibility

    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Start at 100 and simulate random walk with trend
    close_prices = [100.0]
    for i in range(99):
        change = np.random.normal(0.001, 0.02)  # Small upward drift with volatility
        close_prices.append(close_prices[-1] * (1 + change))

    close = np.array(close_prices)

    # Generate high/low with realistic spreads
    high = close * (1 + np.abs(np.random.normal(0, 0.01, 100)))
    low = close * (1 - np.abs(np.random.normal(0, 0.01, 100)))

    # Open prices (close to previous close)
    open_prices = np.roll(close, 1)
    open_prices[0] = close[0]

    # Volume with some randomness
    volume = np.random.randint(1000000, 5000000, 100)

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    return df


@pytest.fixture
def trending_up_data():
    """Generate strongly trending upward data."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Strong uptrend
    close = np.linspace(100, 150, 100)
    noise = np.random.normal(0, 0.5, 100)
    close = close + noise

    high = close * 1.01
    low = close * 0.99
    open_prices = np.roll(close, 1)
    open_prices[0] = close[0]
    volume = np.random.randint(1000000, 5000000, 100)

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    return df


@pytest.fixture
def trending_down_data():
    """Generate strongly trending downward data."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Strong downtrend
    close = np.linspace(150, 100, 100)
    noise = np.random.normal(0, 0.5, 100)
    close = close + noise

    high = close * 1.01
    low = close * 0.99
    open_prices = np.roll(close, 1)
    open_prices[0] = close[0]
    volume = np.random.randint(1000000, 5000000, 100)

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    return df


@pytest.fixture
def ranging_data():
    """Generate sideways/ranging market data."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Oscillating around 100
    close = 100 + 5 * np.sin(np.linspace(0, 4 * np.pi, 100))
    noise = np.random.normal(0, 0.5, 100)
    close = close + noise

    high = close * 1.01
    low = close * 0.99
    open_prices = np.roll(close, 1)
    open_prices[0] = close[0]
    volume = np.random.randint(1000000, 5000000, 100)

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    return df


@pytest.fixture
def volatile_data():
    """Generate highly volatile data."""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # High volatility movements
    close = [100.0]
    for i in range(99):
        change = np.random.normal(0, 0.05)  # High volatility
        close.append(close[-1] * (1 + change))

    close = np.array(close)
    high = close * (1 + np.abs(np.random.normal(0, 0.03, 100)))
    low = close * (1 - np.abs(np.random.normal(0, 0.03, 100)))
    open_prices = np.roll(close, 1)
    open_prices[0] = close[0]
    volume = np.random.randint(1000000, 10000000, 100)

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    return df


@pytest.fixture
def insufficient_data():
    """Generate insufficient data for most strategies (only 5 periods)."""
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')

    close = np.array([100, 101, 102, 101, 103])
    high = close * 1.01
    low = close * 0.99
    open_prices = np.array([100, 100, 101, 102, 101])
    volume = np.array([1000000] * 5)

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    return df


@pytest.fixture
def data_with_nans():
    """Generate data with some NaN values to test robustness."""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')

    close = np.linspace(100, 110, 50)
    high = close * 1.01
    low = close * 0.99
    open_prices = np.roll(close, 1)
    open_prices[0] = close[0]
    volume = np.random.randint(1000000, 5000000, 50)

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    # Introduce some NaN values
    df.loc[df.index[10], 'close'] = np.nan
    df.loc[df.index[20], 'high'] = np.nan

    return df
