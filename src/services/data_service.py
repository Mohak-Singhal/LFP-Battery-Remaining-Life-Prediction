import json
from pathlib import Path
import joblib
import pandas as pd
from src.config import DEFAULT_DATA_PATH, DEFAULT_MODEL_PATH, DEFAULT_PREDICTIONS_PATH

import streamlit as st

@st.cache_data
def load_json(path_str: str):
    path = Path(path_str)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

@st.cache_resource
def load_model_bundle():
    if not DEFAULT_MODEL_PATH.exists():
        return None
    return joblib.load(DEFAULT_MODEL_PATH)

@st.cache_data
def load_default_dataset():
    if DEFAULT_DATA_PATH.exists():
        return pd.read_csv(DEFAULT_DATA_PATH)
    return pd.DataFrame()

@st.cache_data
def load_predictions_frame():
    if DEFAULT_PREDICTIONS_PATH.exists():
        if DEFAULT_PREDICTIONS_PATH.suffix == '.parquet':
            df = pd.read_parquet(DEFAULT_PREDICTIONS_PATH)
        else:
            df = pd.read_csv(DEFAULT_PREDICTIONS_PATH)
            
        # Aggressive memory downcasting to prevent 512MB limit OOM crashes on Render
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = df[col].astype('float32')
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype('category')
            
        return df
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
