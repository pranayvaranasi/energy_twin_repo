import datetime

import pandas as pd
import numpy as np


def _load_tft_dependencies():
    try:
        from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer
        import pytorch_forecasting.metrics as pf_metrics
    except ImportError as exc:
        raise ImportError(
            "pytorch-forecasting and its dependencies are required for TFT model functions. "
            "Install the package from requirements.txt to enable this module."
        ) from exc
    return TimeSeriesDataSet, TemporalFusionTransformer, pf_metrics


def create_mock_historical_data() -> pd.DataFrame:
    """Generates a baseline history of crude prices and run rates."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    df = pd.DataFrame(
        {
            "time_idx": np.arange(100),
            "date": dates,
            "group_id": "India_Energy_Macro",
            "brent_price": np.random.normal(75.0, 2.0, 100).cumsum(),
            "refinery_run_rate": np.random.normal(92.0, 1.0, 100),
            "disruption_severity": np.zeros(100, dtype=float),
        }
    )
    return df


def initialize_tft_model(training_dataset):
    """Initializes the Temporal Fusion Transformer."""
    TimeSeriesDataSet, TemporalFusionTransformer, pf_metrics = _load_tft_dependencies()

    tft = TemporalFusionTransformer.from_dataset(
        training_dataset,
        learning_rate=0.03,
        hidden_size=16,
        attention_head_size=2,
        dropout=0.1,
        hidden_continuous_size=8,
        output_size=7,
        loss=pf_metrics.QuantileLoss(),
        log_interval=10,
        reduce_on_plateau_patience=4,
    )
    return tft


def predict_economic_fallout(
    disruption_event: str,
    severity_score: int,
    elasticity: float = -0.4,
    spr_release_cap: float = 1.5,
    refinery_buffer: int = 7,
) -> dict:
    """Predict the economic shock over the next 14 days using a TFT prototype."""
    df_history = create_mock_historical_data()

    max_prediction_length = 14
    max_encoder_length = 30

    TimeSeriesDataSet, TemporalFusionTransformer, pf_metrics = _load_tft_dependencies()

    training = TimeSeriesDataSet(
        df_history,
        time_idx="time_idx",
        target="brent_price",
        group_ids=["group_id"],
        min_encoder_length=max_encoder_length,
        max_encoder_length=max_encoder_length,
        min_prediction_length=max_prediction_length,
        max_prediction_length=max_prediction_length,
        time_varying_known_reals=["time_idx", "disruption_severity"],
        time_varying_unknown_reals=["brent_price", "refinery_run_rate"],
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
    )

    # TODO: Load an actual trained checkpoint once available.
    # tft = TemporalFusionTransformer.load_from_checkpoint("best_model.ckpt")
    # trainer = pl.Trainer(accelerator="auto", devices=1)
    # raw_predictions, x = tft.predict(training, mode="raw", return_x=True)

    base_price = float(df_history["brent_price"].iloc[-1])
    shock_inflation = 1 + (severity_score * 0.02) + abs(elasticity) * 0.05
    predicted_spike = base_price * shock_inflation
    run_rate = max(55.0, 95.0 - (severity_score * 1.5) - (refinery_buffer * 0.2))
    spr_drawdown = max(1.0, 9.5 - (severity_score * 0.3) + (spr_release_cap * 0.15))

    gdp_hit = (severity_score * 0.04) + abs(elasticity) * 0.1
    power_stress_index = min(100, 45 + (severity_score * 4.5) - (spr_release_cap * 2))

    forecast_dates = pd.date_range(datetime.date.today(), periods=14, freq="D")
    projected_prices = []
    current_price = base_price
    for i in range(14):
        step_up = (predicted_spike - base_price) / 7 if i < 7 else 0
        noise = np.random.normal(0, 0.4)
        current_price = current_price + step_up + noise
        projected_prices.append(round(current_price, 2))

    forecast_df = pd.DataFrame(
        {
            "Date": forecast_dates,
            "Projected Brent Crude ($/bbl)": projected_prices,
        }
    )

    return {
        "brent_spike": f"${predicted_spike:.2f}/bbl",
        "brent_delta": f"+{(shock_inflation - 1) * 100:.1f}%",
        "spr_cover": f"{spr_drawdown:.1f} Days",
        "spr_delta": f"-{(severity_score * 0.3 - spr_release_cap * 0.15):.1f} Days",
        "run_rate": f"{int(run_rate)}%",
        "run_rate_delta": f"-{int(severity_score * 1.5 + refinery_buffer * 0.2)}%",
        "gdp_impact": f"-{gdp_hit:.2f}%",
        "gdp_delta": f"-{gdp_hit:.2f}%",
        "power_stress": f"{int(power_stress_index)}/100",
        "power_stress_delta": f"+{int(severity_score * 4.5)} pts",
        "forecast_df": forecast_df,
        "assumptions": {
            "elasticity": elasticity,
            "spr_release_cap": spr_release_cap,
            "refinery_buffer": refinery_buffer,
        },
    }
