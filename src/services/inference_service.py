import numpy as np
import pandas as pd
from src.services.business_logic import enrich_business_columns
from src.data.preprocessing import clean_data, handle_missing_values, create_features, estimate_rul
from src.data.data_loader import map_columns

def load_and_map_from_frame(df: pd.DataFrame):
    return map_columns(df)

def prediction_intervals(predictions: np.ndarray, uncertainty_profile: dict):
    if not uncertainty_profile:
        return predictions, predictions
    overall = uncertainty_profile.get("overall", {"lower_residual_q": 0.0, "upper_residual_q": 0.0})
    by_band = uncertainty_profile.get("by_prediction_band", {})
    lower = []
    upper = []
    for prediction in predictions:
        if prediction <= 500:
            band = "near_eol"
        elif prediction <= 2000:
            band = "mid_life"
        else:
            band = "early_life"
        band_profile = by_band.get(band, overall)
        lower.append(max(0.0, prediction + band_profile["lower_residual_q"]))
        upper.append(max(0.0, prediction + band_profile["upper_residual_q"]))
    return np.array(lower), np.array(upper)

def confidence_band(width: float):
    if width <= 150:
        return "High"
    if width <= 350:
        return "Medium"
    return "Low"

def out_of_distribution_flags(df: pd.DataFrame, feature_ranges: dict):
    flags = pd.DataFrame(index=df.index)
    for feature, stats in feature_ranges.items():
        if feature not in df.columns:
            continue
        margin = max(1e-9, 0.1 * max(abs(stats["min"]), abs(stats["max"]), 1.0))
        lower = stats["min"] - margin
        upper = stats["max"] + margin
        flags[f"{feature}_ood"] = (df[feature] < lower) | (df[feature] > upper)
    return flags

def score_uploaded_dataset(df_raw: pd.DataFrame, model_bundle: dict):
    mapped_df, mapping, missing = load_and_map_from_frame(df_raw)
    df = clean_data(mapped_df)
    df = handle_missing_values(df)
    df = create_features(df)
    df = estimate_rul(df)

    model = model_bundle["model"]
    features = model_bundle.get("features", [])
    missing_features = [feature for feature in features if feature not in df.columns]
    if missing_features:
        raise ValueError("Uploaded dataset is missing required engineered features: " + ", ".join(missing_features))

    predictions = np.maximum(0.0, model.predict(df[features]))
    lower, upper = prediction_intervals(predictions, model_bundle.get("uncertainty_profile", {}))
    df["predicted_rul"] = predictions
    df["predicted_rul_lower"] = lower
    df["predicted_rul_upper"] = upper
    df["prediction_interval_width"] = upper - lower
    df["confidence_band"] = df["prediction_interval_width"].apply(confidence_band)
    df["predicted_rul_months"] = df["predicted_rul"] / 30.0
    if "capacity_remaining" in df.columns:
        df["energy_margin_to_eol_kwh"] = np.maximum(0.0, (df["capacity_remaining"] - 80.0) / 100.0 * 35.0)
    else:
        df["energy_margin_to_eol_kwh"] = 0.0
    flags = out_of_distribution_flags(df[features], model_bundle.get("feature_ranges", {}))
    if not flags.empty:
        df["ood_feature_count"] = flags.sum(axis=1)
        df["is_out_of_distribution"] = df["ood_feature_count"] > 0
    else:
        df["ood_feature_count"] = 0
        df["is_out_of_distribution"] = False

    if "capacity_remaining" not in df.columns:
        df["capacity_remaining"] = 85.0
    df = enrich_business_columns(df)

    return df, mapping, missing
