from src.simulation_models import (
    monte_carlo_normal,
    monte_carlo_bootstrap,
    backtest_rolling_windows,
    load_historical_annual_returns,
)


def test_historical_returns_load():
    hist = load_historical_annual_returns()
    assert hist.size >= 50


def test_monte_carlo_normal_output_shape():
    result = monte_carlo_normal(
        initial_wealth=100_000,
        monthly_contribution=1_000,
        years=20,
        mean_return=0.06,
        volatility=0.15,
        inflation_rate=0.02,
        annual_spending=30_000,
        safe_withdrawal_rate=0.04,
        num_simulations=500,
        seed=42,
    )
    assert result["paths"].shape == (500, 21)
    assert 0 <= result["success_rate_final"] <= 100


def test_bootstrap_output_shape():
    hist = load_historical_annual_returns()
    result = monte_carlo_bootstrap(
        initial_wealth=100_000,
        monthly_contribution=1_000,
        years=20,
        inflation_rate=0.02,
        annual_spending=30_000,
        safe_withdrawal_rate=0.04,
        historical_returns=hist,
        num_simulations=500,
        seed=42,
    )
    assert result["paths"].shape == (500, 21)
    assert 0 <= result["success_rate_final"] <= 100


def test_backtesting_rolling_windows():
    hist = load_historical_annual_returns()
    years = 20
    result = backtest_rolling_windows(
        initial_wealth=100_000,
        monthly_contribution=1_000,
        years=years,
        inflation_rate=0.02,
        annual_spending=30_000,
        safe_withdrawal_rate=0.04,
        historical_returns=hist,
    )
    expected_windows = hist.size - years + 1
    assert result["paths"].shape == (expected_windows, years + 1)
    assert result["windows_count"] == expected_windows
