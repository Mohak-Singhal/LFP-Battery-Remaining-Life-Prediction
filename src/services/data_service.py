import json
from pathlib import Path
import joblib
import pandas as pd
from src.config import DEFAULT_DATA_PATH, DEFAULT_MODEL_PATH, DEFAULT_PREDICTIONS_PATH

def load_json(path: Path):
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def load_model_bundle():
    if not DEFAULT_MODEL_PATH.exists():
        return None
    return joblib.load(DEFAULT_MODEL_PATH)

def load_default_dataset():
    if DEFAULT_DATA_PATH.exists():
        return pd.read_csv(DEFAULT_DATA_PATH)
    return pd.DataFrame()

def load_predictions_frame():
    if DEFAULT_PREDICTIONS_PATH.exists():
        if DEFAULT_PREDICTIONS_PATH.suffix == '.parquet':
            return pd.read_parquet(DEFAULT_PREDICTIONS_PATH)
        return pd.read_csv(DEFAULT_PREDICTIONS_PATH)
    return pd.DataFrame()

def latest_snapshot(predictions: pd.DataFrame):
    if predictions.empty:
        return pd.DataFrame()
    snapshot = predictions.sort_values("cycle_number").groupby("battery_id", as_index=False).tail(1)
    return snapshot.sort_values("predicted_rul")

def fleet_snapshot_at_cycle(predictions: pd.DataFrame, selected_cycle: int):
    if predictions.empty:
        return pd.DataFrame()
    eligible = predictions[predictions["cycle_number"] <= selected_cycle].copy()
    if eligible.empty:
        return latest_snapshot(predictions)
    snapshot = eligible.sort_values("cycle_number").groupby("battery_id", as_index=False).tail(1)
    return snapshot.sort_values("predicted_rul")
