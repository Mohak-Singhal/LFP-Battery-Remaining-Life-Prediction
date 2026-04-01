import sys
import numpy as np
import pandas as pd
import streamlit as st

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.services.data_service import (
    load_json,
    load_model_bundle,
    load_predictions_frame,
    latest_snapshot,
    fleet_snapshot_at_cycle,
)
from src.services.inference_service import score_uploaded_dataset
from src.services.business_logic import enrich_business_columns
from src.services.sensitivity_analysis import conduct_sensitivity_analysis
from src.ui.model_visualization import plot_failure_curve
from src.ui.styles import inject_styles
from src.ui.components import hero_metric, status_label, render_health_and_optimization
from src.ui.app_charts import (
    chart_rul_band,
    chart_actual_vs_predicted,
    chart_battery_leaderboard,
    chart_fleet_degradation_trajectories,
    chart_capacity_vs_rul,
    chart_temperature_cycle_life_window,
    chart_temperature_voltage_curves,
    chart_temperature_capacity_fade,
    chart_lifecycle_metrics,
    chart_validation_comparison,
    chart_feature_importance,
    chart_driver_groups,
)
from src.config import DEFAULT_METRICS_PATH as METRICS_PATH

def main():
    st.set_page_config(page_title="Battery RUL Command Center", page_icon=":battery:", layout="wide")
    inject_styles()

    metrics_payload = load_json(METRICS_PATH)
    model_bundle = load_model_bundle()
    saved_predictions = load_predictions_frame()

    st.markdown(
        """
        <div class="hero-shell">
            <div class="hero-kicker">Battery Intelligence Studio</div>
            <div class="hero-title"> Battery RUL  Dashboard</div>
            <div class="hero-subtitle">
                Live-ready command center for remaining useful life forecasting, fleet risk triage,
                confidence monitoring, and model credibility storytelling.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Navigation")
        app_page = st.radio("Select View:", ["Command Center", "Endur-Cert: 2nd Life"], index=0)
        st.divider()
        st.header("Battery Rul Predictor")
        mode = st.radio("Dataset mode", ["Saved demo outputs", "Upload custom CSV"], index=0)
        uploaded_file = st.file_uploader("Upload battery CSV", type=["csv"])
        st.caption("Tip: use the saved outputs during the presentation for the smoothest experience.")

    mapping = {}
    missing = []
    if mode == "Upload custom CSV" and uploaded_file is not None and model_bundle is not None:
        raw_df = pd.read_csv(uploaded_file)
        predictions = None
        try:
            predictions, mapping, missing = score_uploaded_dataset(raw_df, model_bundle)
        except Exception as exc:
            st.error(f"Could not score uploaded dataset: {exc}")
            predictions = pd.DataFrame()
    else:
        predictions = saved_predictions.copy()

    if predictions.empty:
        st.warning("No predictions available yet. Run training and prediction first, or upload a valid dataset.")
        return

    if "battery_id" not in predictions.columns:
        predictions["battery_id"] = "Demo"
    if "battery_health_class" not in predictions.columns and "capacity_remaining" in predictions.columns:
        predictions = enrich_business_columns(predictions)

    if app_page == "Endur-Cert: 2nd Life":
        from src.ui.endur_cert_ui import render_endur_cert_tab
        render_endur_cert_tab(predictions)
        return

    snapshot = latest_snapshot(predictions)
    selected_battery = st.sidebar.selectbox(
        "Battery spotlight",
        snapshot["battery_id"].astype(str).tolist(),
        index=0,
    )
    selected_battery_int = int(selected_battery) if str(selected_battery).isdigit() else selected_battery
    battery_df = predictions[predictions["battery_id"] == selected_battery_int].copy()
    battery_df = battery_df.sort_values("cycle_number")
    cycle_min = int(battery_df["cycle_number"].min())
    cycle_max = int(battery_df["cycle_number"].max())

    if "cycle_spotlight" not in st.session_state:
        st.session_state["cycle_spotlight"] = cycle_max
    if st.session_state["cycle_spotlight"] > cycle_max:
        st.session_state["cycle_spotlight"] = cycle_max
    elif st.session_state["cycle_spotlight"] < cycle_min:
        st.session_state["cycle_spotlight"] = cycle_min

    selected_cycle = st.sidebar.slider(
        "Cycle spotlight", 
        min_value=cycle_min, 
        max_value=cycle_max, 
        value=st.session_state["cycle_spotlight"]
    )
    st.session_state["cycle_spotlight"] = selected_cycle

    selected_row_df = battery_df.loc[battery_df["cycle_number"] == selected_cycle]
    if selected_row_df.empty:
        selected_row = battery_df.iloc[-1]
    else:
        selected_row = selected_row_df.iloc[-1]
        
    fleet_cycle_min = int(predictions["cycle_number"].min())
    fleet_cycle_max = int(predictions["cycle_number"].max())

    if "fleet_cycle_state" not in st.session_state:
        st.session_state["fleet_cycle_state"] = fleet_cycle_max
    if st.session_state["fleet_cycle_state"] > fleet_cycle_max:
        st.session_state["fleet_cycle_state"] = fleet_cycle_max
    elif st.session_state["fleet_cycle_state"] < fleet_cycle_min:
        st.session_state["fleet_cycle_state"] = fleet_cycle_min

    fleet_cycle = st.sidebar.slider(
        "Fleet cycle view",
        min_value=fleet_cycle_min,
        max_value=fleet_cycle_max,
        value=st.session_state["fleet_cycle_state"],
        help="Shows fleet-level status using the latest available row for each battery up to this cycle."
    )
    st.session_state["fleet_cycle_state"] = fleet_cycle

    fleet_snapshot = fleet_snapshot_at_cycle(predictions, fleet_cycle)

    rmse = metrics_payload.get("test_metrics", {}).get("RMSE", np.nan)
    r2 = metrics_payload.get("test_metrics", {}).get("R2", np.nan)
    coverage = metrics_payload.get("test_interval_metrics", {}).get("coverage", np.nan)
    baseline_rmse = metrics_payload.get("baseline_test_metrics", {}).get("RMSE", np.nan)
    improvement = ((baseline_rmse - rmse) / baseline_rmse * 100.0) if baseline_rmse and not np.isnan(rmse) else np.nan

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        hero_metric("Battery Spotlight", f"{selected_battery}", f"{status_label(selected_row['predicted_rul'])}")
    with c2:
        hero_metric("Selected Cycle RUL", f"{selected_row['predicted_rul']:.0f}", f"Cycle {int(selected_row['cycle_number'])} | {selected_row['confidence_band']} confidence")
    with c3:
        hero_metric("Test RMSE", f"{rmse:.1f}", f"{improvement:.1f}% better than baseline")
    with c4:
        hero_metric("Interval Coverage", f"{coverage * 100:.1f}%", f"Test R2 = {r2:.3f}")

    st.markdown('<div class="section-shell">', unsafe_allow_html=True)
    left, right = st.columns([1.8, 1.2])
    with left:
        st.plotly_chart(chart_rul_band(battery_df, selected_row=selected_row), use_container_width=True)
    with right:
        st.subheader("Battery Storyline")
        st.markdown(
            f"""
            <div class="mini-note">
            At <b>cycle {int(selected_row['cycle_number'])}</b>, battery <b>{selected_battery}</b> projects
            <b>{selected_row['predicted_rul']:.0f}</b> remaining cycles.
            The forecast interval ranges from <b>{selected_row['predicted_rul_lower']:.0f}</b> to <b>{selected_row['predicted_rul_upper']:.0f}</b> cycles.
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        metric_cols = st.columns(2)
        metric_cols[0].metric("Capacity Remaining", f"{selected_row['capacity_remaining']:.2f}%")
        metric_cols[1].metric("OOD Flags", int(selected_row.get("ood_feature_count", 0)))
        metric_cols = st.columns(2)
        metric_cols[0].metric("Estimated Months Left", f"{selected_row.get('predicted_rul_months', selected_row['predicted_rul'] / 30.0):.1f}")
        metric_cols[1].metric("Energy To EOL", f"{selected_row.get('energy_margin_to_eol_kwh', 0.0):.2f} kWh")
        metric_cols = st.columns(2)
        metric_cols[0].metric("Health Class", str(selected_row.get("battery_health_class", "n/a")))
        metric_cols[1].metric("Warranty Risk", str(selected_row.get("warranty_risk", "n/a")))
        if "rul" in selected_row.index:
            metric_cols = st.columns(2)
            metric_cols[0].metric("Actual RUL", f"{selected_row['rul']:.0f}")
            metric_cols[1].metric("Prediction Error", f"{abs(selected_row['predicted_rul'] - selected_row['rul']):.0f}")
        st.info(str(selected_row.get("maintenance_recommendation", "No maintenance note available.")))
        st.dataframe(
            fleet_snapshot[["battery_id", "predicted_rul", "predicted_rul_lower", "predicted_rul_upper", "capacity_remaining", "battery_health_class", "warranty_risk"]]
            .rename(
                columns={
                    "battery_id": "Battery",
                    "predicted_rul": "Predicted RUL",
                    "predicted_rul_lower": "Lower",
                    "predicted_rul_upper": "Upper",
                    "capacity_remaining": "Capacity %",
                    "battery_health_class": "Health",
                    "warranty_risk": "Warranty Risk",
                }
            )
            .head(8),
            use_container_width=True,
            hide_index=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    render_health_and_optimization(selected_row, model_bundle)

    st.markdown('<div class="section-shell">', unsafe_allow_html=True)
    st.subheader("Battery & Cycle Detail Explorer")
    st.caption("Use this during the presentation to answer questions about any battery at any cycle.")
    explorer_df = battery_df.reset_index(drop=True)
    table_left, table_right = st.columns([1.1, 2.2])
    with table_left:
        st.metric("Selected Battery", str(selected_battery))
        st.metric("Selected Cycle", int(selected_row["cycle_number"]))
    with table_right:
        window = st.slider("Neighboring rows to show", min_value=0, max_value=25, value=3)
    cycle_detail = explorer_df.loc[explorer_df["cycle_number"] == selected_cycle]
    if cycle_detail.empty:
        cycle_detail = explorer_df.iloc[[-1]]
    center_idx = int(cycle_detail.index[0])
    nearby_rows = explorer_df.iloc[max(0, center_idx - window): min(len(explorer_df), center_idx + window + 1)]
    transposed = cycle_detail.T.copy()
    col_name = "Selected Value"
    transposed.rename(columns={cycle_detail.index[0]: col_name}, inplace=True)
    transposed[col_name] = transposed[col_name].astype(str)
    st.dataframe(transposed, use_container_width=True)
    st.caption("Nearby context around the selected cycle")
    st.dataframe(nearby_rows, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    row_a, row_b = st.columns(2)
    with row_a:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.plotly_chart(chart_actual_vs_predicted(predictions), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with row_b:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.plotly_chart(chart_battery_leaderboard(fleet_snapshot), use_container_width=True)
        st.caption(f"Fleet ranking as of cycle {fleet_cycle}.")
        st.markdown("</div>", unsafe_allow_html=True)

    row_c, row_d = st.columns(2)
    with row_c:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.plotly_chart(chart_validation_comparison(metrics_payload), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with row_d:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.plotly_chart(chart_lifecycle_metrics(metrics_payload), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-shell">', unsafe_allow_html=True)
    st.subheader("Degradation Behavior")
    st.caption("A neat judge-facing view from single-battery failure progression to fleet-wide degradation spread.")
    degrade_left, degrade_right = st.columns([1.0, 1.2])
    with degrade_left:
        st.plotly_chart(plot_failure_curve(battery_df), use_container_width=True)
    with degrade_right:
        st.plotly_chart(chart_fleet_degradation_trajectories(predictions), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-shell">', unsafe_allow_html=True)
    st.subheader("Temperature vs Degradation")
    st.caption("These scenario plots answer the hackathon requirement for degradation trends and sensitivity analysis under temperature stress.")
    temp_a, temp_b, temp_c = st.columns(3)
    with temp_a:
        st.plotly_chart(chart_temperature_cycle_life_window(), use_container_width=True)
    with temp_b:
        st.plotly_chart(chart_temperature_voltage_curves(), use_container_width=True)
    with temp_c:
        st.plotly_chart(chart_temperature_capacity_fade(), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    sens_fig, heat_fig = conduct_sensitivity_analysis(pd.DataFrame())
    st.markdown('<div class="section-shell">', unsafe_allow_html=True)
    st.subheader("Multivariable Sensitivity")
    st.caption("Temperature, DoD, and C-rate combined impact on projected battery life.")
    sens_left, sens_right = st.columns(2)
    with sens_left:
        st.plotly_chart(sens_fig, use_container_width=True)
    with sens_right:
        st.plotly_chart(heat_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    explain_left, explain_right = st.columns(2)
    with explain_left:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.plotly_chart(chart_feature_importance(model_bundle), use_container_width=True)
        st.caption("Explainability view: temperature, DoD, and C-rate derived features should appear among the top degradation drivers.")
        st.markdown("</div>", unsafe_allow_html=True)
    with explain_right:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.plotly_chart(chart_driver_groups(metrics_payload), use_container_width=True)
        st.caption("Judge-facing summary of the main degradation themes affecting RUL.")
        st.markdown("</div>", unsafe_allow_html=True)

    row_e, row_f = st.columns([1.25, 1.0])
    with row_e:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.plotly_chart(chart_capacity_vs_rul(predictions), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with row_f:
        st.markdown('<div class="section-shell">', unsafe_allow_html=True)
        st.subheader("Model Credibility")
        st.caption("A compact presentation slide built into the app.")
        overview = pd.DataFrame(
            [
                ["Best Model", metrics_payload.get("best_model", "n/a").upper()],
                ["Grouped Validation RMSE", f"{metrics_payload.get('best_rmse', np.nan):.2f}"],
                ["Final Test RMSE", f"{metrics_payload.get('test_metrics', {}).get('RMSE', np.nan):.2f}"],
                ["Final Test MAE", f"{metrics_payload.get('test_metrics', {}).get('MAE', np.nan):.2f}"],
                ["Final Test R2", f"{metrics_payload.get('test_metrics', {}).get('R2', np.nan):.4f}"],
                ["Interval Coverage", f"{metrics_payload.get('test_interval_metrics', {}).get('coverage', np.nan) * 100:.2f}%"],
                ["Mean Interval Width", f"{metrics_payload.get('test_interval_metrics', {}).get('mean_interval_width', np.nan):.2f}"],
                ["Baseline RMSE", f"{metrics_payload.get('baseline_test_metrics', {}).get('RMSE', np.nan):.2f}"],
            ],
            columns=["Metric", "Value"],
        )
        st.dataframe(overview, use_container_width=True, hide_index=True)
        if mapping:
            st.write("Upload column mapping")
            st.json(mapping)
        if missing:
            st.warning("Missing uploaded columns: " + ", ".join(missing))
        st.markdown(
            """
            **Talk track**

            - Grouped battery validation was used to avoid optimistic row leakage.
            - The final test set stayed untouched until the end.
            - Every forecast now ships with a confidence interval and OOD safety signal.
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-shell">', unsafe_allow_html=True)
    st.subheader("Fleet Snapshot")
    leaderboard = fleet_snapshot.copy()
    st.caption(f"Fleet state as of cycle {fleet_cycle}. Each row is the latest available reading for that battery up to the selected cycle.")
    leaderboard["Status"] = leaderboard["predicted_rul"].apply(status_label)
    leaderboard["Confidence"] = leaderboard["confidence_band"]
    leaderboard["Predicted RUL"] = leaderboard["predicted_rul"].round(1)
    leaderboard["Lower"] = leaderboard["predicted_rul_lower"].round(1)
    leaderboard["Upper"] = leaderboard["predicted_rul_upper"].round(1)
    leaderboard["Snapshot Cycle"] = leaderboard["cycle_number"].astype(int)
    leaderboard["Capacity %"] = leaderboard["capacity_remaining"].round(2)
    if "battery_health_class" in leaderboard.columns:
        leaderboard["Health"] = leaderboard["battery_health_class"]
    if "warranty_risk" in leaderboard.columns:
        leaderboard["Warranty Risk"] = leaderboard["warranty_risk"]
    if "maintenance_recommendation" in leaderboard.columns:
        leaderboard["Maintenance Recommendation"] = leaderboard["maintenance_recommendation"]
    st.dataframe(
        leaderboard[[col for col in ["battery_id", "Snapshot Cycle", "Predicted RUL", "Lower", "Upper", "Capacity %", "Confidence", "Health", "Warranty Risk", "Status", "Maintenance Recommendation"] if col in leaderboard.columns]]
        .rename(columns={"battery_id": "Battery"}),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()