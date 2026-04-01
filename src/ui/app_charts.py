import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from src.ui.components import status_label

def empty_state_figure(title: str, message: str):
    fig = go.Figure()
    fig.update_layout(
        title=title,
        height=360,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=message,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=15, color="#5f6c7b"),
            )
        ],
    )
    return make_line_theme(fig)

def make_line_theme(fig: go.Figure, horizontal_legend: bool = True):
    if horizontal_legend:
        legend_config = dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(255,255,255,0.76)",
            bordercolor="rgba(20,33,61,0.08)",
            borderwidth=1,
            font=dict(size=11),
        )
        margin_config = dict(l=20, r=20, t=76, b=84)
    else:
        legend_config = dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor="rgba(255,255,255,0.76)",
            bordercolor="rgba(20,33,61,0.08)",
            borderwidth=1,
            font=dict(size=11),
        )
        margin_config = dict(l=20, r=20, t=76, b=24)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.88)",
        font=dict(family="Georgia", color="#14213d"),
        margin=margin_config,
        title=dict(font=dict(size=22), x=0.01, xanchor="left", y=0.98, pad=dict(t=4, b=8)),
        legend=legend_config,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(20,33,61,0.08)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(20,33,61,0.08)")
    return fig

def chart_rul_band(battery_df: pd.DataFrame, selected_row: pd.Series | None = None):
    ordered = battery_df.sort_values("cycle_number")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ordered["cycle_number"],
            y=ordered["predicted_rul_upper"],
            mode="lines",
            line=dict(color="rgba(47,79,79,0)"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ordered["cycle_number"],
            y=ordered["predicted_rul_lower"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(242, 153, 74, 0.22)",
            line=dict(color="rgba(47,79,79,0)"),
            name="Prediction interval",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=ordered["cycle_number"],
            y=ordered["predicted_rul"],
            mode="lines",
            line=dict(color="#f77f00", width=3),
            name="Predicted RUL",
        )
    )
    if "rul" in ordered.columns:
        fig.add_trace(
            go.Scatter(
                x=ordered["cycle_number"],
                y=ordered["rul"],
                mode="lines",
                line=dict(color="#003049", width=2, dash="dot"),
                name="Actual RUL",
            )
        )
    if selected_row is not None:
        fig.add_trace(
            go.Scatter(
                x=[selected_row["cycle_number"]],
                y=[selected_row["predicted_rul"]],
                mode="markers",
                marker=dict(size=12, color="#d62828", line=dict(width=2, color="#fffaf1")),
                name="Selected cycle",
            )
        )
    fig.update_layout(title="RUL Forecast With Confidence Envelope", xaxis_title="Cycle", yaxis_title="Remaining Useful Life")
    return make_line_theme(fig)

def chart_actual_vs_predicted(predictions: pd.DataFrame):
    # Downsampled from 7000 to 2500 to aggressively prevent Render 512MB RAM exhaustion
    scatter = px.scatter(
        predictions.sample(min(len(predictions), 2500), random_state=42),
        x="rul",
        y="predicted_rul",
        color="prediction_interval_width",
        color_continuous_scale=["#003049", "#f77f00", "#fcbf49"],
        opacity=0.55,
        title="Actual vs Predicted RUL",
        labels={"rul": "Actual RUL", "predicted_rul": "Predicted RUL", "prediction_interval_width": "Interval Width"},
    )
    if "rul" in predictions.columns and not predictions.empty:
        max_value = max(predictions["rul"].max(), predictions["predicted_rul"].max())
        scatter.add_trace(
            go.Scatter(
                x=[0, max_value],
                y=[0, max_value],
                mode="lines",
                line=dict(color="#2a9d8f", dash="dash"),
                name="Ideal fit",
            )
        )
    return make_line_theme(scatter)

def chart_battery_leaderboard(snapshot: pd.DataFrame):
    ranked = snapshot.nsmallest(12, "predicted_rul").copy()
    ranked["status"] = ranked["predicted_rul"].apply(status_label)
    fig = px.bar(
        ranked,
        x="predicted_rul",
        y=ranked["battery_id"].astype(str),
        color="status",
        orientation="h",
        title="Fleet Attention Board",
        color_discrete_map={
            "Immediate attention": "#d62828",
            "Watchlist": "#f77f00",
            "Stable": "#2a9d8f",
        },
        labels={"x": "Predicted RUL", "y": "Battery ID"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return make_line_theme(fig)

def chart_fleet_degradation_trajectories(predictions: pd.DataFrame):
    required = {"battery_id", "cycle_number", "capacity_remaining"}
    if not required.issubset(predictions.columns):
        return empty_state_figure("Fleet Degradation Trajectories", "Capacity trajectory columns are not available.")

    plot_df = predictions[list(required)].dropna().copy()
    if plot_df.empty:
        return empty_state_figure("Fleet Degradation Trajectories", "No degradation data available for plotting.")

    lifetime_df = (
        plot_df.groupby("battery_id", as_index=False)["cycle_number"]
        .max()
        .rename(columns={"cycle_number": "lifetime_cycles"})
        .sort_values("lifetime_cycles")
    )
    if len(lifetime_df) > 40:
        sampled_idx = np.linspace(0, len(lifetime_df) - 1, 40).astype(int)
        lifetime_df = lifetime_df.iloc[sampled_idx]
    plot_df = plot_df.merge(lifetime_df, on="battery_id", how="inner")

    lifetime_min = float(lifetime_df["lifetime_cycles"].min())
    lifetime_max = float(lifetime_df["lifetime_cycles"].max())
    lifetime_span = max(lifetime_max - lifetime_min, 1.0)

    fig = go.Figure()
    for battery_id, battery_trace in plot_df.groupby("battery_id", sort=False):
        # Prevent 512MB Render RAM crashes by subsampling 1/20th of the points
        # to dramatically lower JSON Plotly serialization size (from 100MB to 5MB)
        ordered = battery_trace.sort_values("cycle_number").iloc[::20]
        if ordered.empty:
            continue
            
        lifetime = float(battery_trace["lifetime_cycles"].iloc[0])
        norm = (lifetime - lifetime_min) / lifetime_span
        color = sample_colorscale("Turbo", [norm])[0]
        fig.add_trace(
            go.Scatter(
                x=ordered["cycle_number"],
                y=ordered["capacity_remaining"],
                mode="lines",
                line=dict(color=color, width=2),
                opacity=0.68,
                showlegend=False,
                hovertemplate=(
                    f"Battery {battery_id}<br>"
                    "Cycle %{x}<br>"
                    "Capacity %{y:.2f}%<br>"
                    f"Observed lifetime {lifetime:.0f} cycles<extra></extra>"
                ),
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[plot_df["cycle_number"].min()],
            y=[plot_df["capacity_remaining"].min()],
            mode="markers",
            marker=dict(
                size=0.1,
                opacity=0.0,
                color=[lifetime_min],
                cmin=lifetime_min,
                cmax=lifetime_max,
                colorscale="Turbo",
                showscale=True,
                colorbar=dict(title="Lifetime (Cycles)"),
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_hline(y=80, line_dash="dash", line_color="#d62828", annotation_text="80% EOL")
    fig.update_layout(
        title="Fleet Degradation Trajectories",
        xaxis_title="Cycle Number",
        yaxis_title="Remaining Capacity (%)",
        height=420,
    )
    fig.update_yaxes(range=[79.5, max(100.2, float(plot_df["capacity_remaining"].max()) + 0.3)])
    return make_line_theme(fig)

def chart_capacity_vs_rul(predictions: pd.DataFrame):
    # Downsampled to 2500 to aggressively prevent plotting JSON serialization RAM spikes
    sample = predictions.sample(min(len(predictions), 2500), random_state=42)
    fig = px.scatter(
        sample,
        x="capacity_remaining",
        y="predicted_rul",
        color="confidence_band",
        title="Capacity Remaining vs Predicted RUL",
        color_discrete_map={"High": "#2a9d8f", "Medium": "#f77f00", "Low": "#d62828"},
        labels={"capacity_remaining": "Capacity Remaining (%)", "predicted_rul": "Predicted RUL"},
    )
    return make_line_theme(fig)

def chart_temperature_cycle_life_window():
    temperatures = np.linspace(-30, 50, 161)
    profiles = [
        ("Gentle duty", 1225.0, "#1d4ed8", 1.0, 0.9),
        ("Mixed duty", 1110.0, "#2a9d8f", 1.1, 1.0),
        ("Aggressive duty", 885.0, "#fcbf49", 1.25, 1.15),
    ]

    fig = go.Figure()
    for label, base_life, color, cold_bias, heat_bias in profiles:
        cold_penalty = cold_bias * np.power(np.maximum(10.0 - temperatures, 0.0), 1.52) * 4.6
        heat_penalty = heat_bias * np.power(np.maximum(temperatures - 32.0, 0.0), 1.58) * 3.5
        curvature = 0.1 * np.square(temperatures - 28.0)
        projected_life = np.clip(base_life - cold_penalty - heat_penalty - curvature, 60.0, None)
        fig.add_trace(
            go.Scatter(
                x=temperatures,
                y=projected_life,
                mode="lines",
                name=label,
                line=dict(color=color, width=3),
            )
        )

    fig.add_vrect(x0=15, x1=35, fillcolor="rgba(42,157,143,0.12)", line_width=0)
    fig.add_annotation(
        x=25,
        y=1225,
        text="Optimal temperature window",
        showarrow=False,
        font=dict(color="#2a9d8f", size=13),
    )
    fig.update_layout(
        title="Temperature Window vs Projected Cycle Life",
        xaxis_title="Temperature (°C)",
        yaxis_title="Cycle Life",
        height=360,
    )
    return make_line_theme(fig)

def chart_temperature_voltage_curves():
    temperatures = [40, 30, 20, 10, 0, -10, -20]
    palette = ["#7f1d1d", "#d62828", "#f77f00", "#80ed99", "#4cc9f0", "#4895ef", "#4361ee"]

    fig = go.Figure()
    for temp, color in zip(temperatures, palette):
        usable_capacity = 2.75 - 1.3 * np.exp(-(temp + 20.0) / 18.0)
        capacity = np.linspace(0.0, usable_capacity, 160)
        frac = np.clip(capacity / usable_capacity, 0.0, 1.0)
        base_voltage = 4.16 - 0.33 * frac - 0.18 * frac**2 - 0.09 * np.log1p(9.0 * frac)
        end_knee = 0.78 * frac**10
        cold_drop = np.interp(temp, [-20.0, 40.0], [0.28, 0.02])
        initial_polarization = np.interp(temp, [-20.0, 40.0], [0.26, 0.04]) * np.exp(-capacity / 0.05)
        voltage = np.clip(base_voltage - end_knee - cold_drop - initial_polarization, 2.5, 4.22)
        fig.add_trace(
            go.Scatter(
                x=capacity,
                y=voltage,
                mode="lines",
                name=f"{temp}°C",
                line=dict(color=color, width=3),
            )
        )

    fig.update_layout(
        title="Voltage vs Capacity Across Temperatures",
        xaxis_title="Capacity (Ah)",
        yaxis_title="Voltage (V)",
        height=360,
    )
    return make_line_theme(fig, horizontal_legend=False)

def chart_temperature_capacity_fade():
    temperatures = [20, 30, 40, 50, 60]
    eol_cycles = {20: 2250, 30: 1825, 40: 1425, 50: 875, 60: 420}
    palette = {20: "#4cc9f0", 30: "#4895ef", 40: "#2a9d8f", 50: "#fcbf49", 60: "#d62828"}
    cycles = np.linspace(0.0, 2500.0, 220)

    fig = go.Figure()
    for temp in temperatures:
        decay_constant = -np.log(0.80) / eol_cycles[temp]
        normalized_capacity = np.clip(np.exp(-decay_constant * cycles), 0.74, 1.0)
        fig.add_trace(
            go.Scatter(
                x=cycles,
                y=normalized_capacity,
                mode="lines",
                name=f"{temp}°C",
                line=dict(color=palette[temp], width=3),
            )
        )

    fig.add_hline(y=0.80, line_dash="dash", line_color="#d62828", annotation_text="80% EOL")
    fig.update_layout(
        title="Temperature-Driven Capacity Fade",
        xaxis_title="Cycle Number",
        yaxis_title="Normalized Capacity",
        height=360,
    )
    fig.update_yaxes(range=[0.75, 1.01], tickformat=".0%")
    return make_line_theme(fig, horizontal_legend=False)

def chart_lifecycle_metrics(metrics_payload: dict):
    rows = []
    for phase, values in metrics_payload.get("test_lifecycle_metrics", {}).items():
        rows.append(
            {
                "Lifecycle Stage": phase.replace("_", " ").title(),
                "RMSE": values["RMSE"],
                "MAE": values["MAE"],
                "R2": values["R2"],
            }
        )
    lifecycle_df = pd.DataFrame(rows)
    fig = px.bar(
        lifecycle_df,
        x="Lifecycle Stage",
        y="RMSE",
        color="Lifecycle Stage",
        title="Error Profile Across Battery Lifecycle",
        color_discrete_sequence=["#003049", "#f77f00", "#d62828"],
    )
    return make_line_theme(fig)

def chart_validation_comparison(metrics_payload: dict):
    rows = []
    for name, values in metrics_payload.get("grouped_validation", {}).items():
        rows.append(
            {
                "Model": name.upper(),
                "RMSE": values["mean_RMSE"],
                "MAE": values["mean_MAE"],
                "R2": values["mean_R2"],
            }
        )
    comparison_df = pd.DataFrame(rows)
    fig = px.bar(
        comparison_df,
        x="Model",
        y=["RMSE", "MAE"],
        barmode="group",
        title="Grouped Validation Model Comparison",
        color_discrete_sequence=["#f77f00", "#003049"],
    )
    return make_line_theme(fig)

def chart_feature_importance(model_bundle: dict):
    if not model_bundle:
        return go.Figure()
    model = model_bundle.get("model")
    features = model_bundle.get("features", [])
    if not hasattr(model, "feature_importances_"):
        return go.Figure()
    importance_df = pd.DataFrame(
        {"Feature": features, "Importance": model.feature_importances_}
    ).sort_values("Importance", ascending=False).head(12)
    fig = px.bar(
        importance_df.sort_values("Importance"),
        x="Importance",
        y="Feature",
        orientation="h",
        title="Top Model Drivers",
        color="Importance",
        color_continuous_scale=["#003049", "#f77f00", "#fcbf49"],
    )
    return make_line_theme(fig)

def chart_driver_groups(metrics_payload: dict):
    groups = metrics_payload.get("driver_importance_groups", {})
    if not groups:
        return go.Figure()
    group_df = pd.DataFrame(
        {"Driver Group": [name.replace("_", " ").title() for name in groups], "Importance": list(groups.values())}
    ).sort_values("Importance")
    fig = px.bar(
        group_df,
        x="Importance",
        y="Driver Group",
        orientation="h",
        title="Grouped Degradation Drivers",
        color="Importance",
        color_continuous_scale=["#003049", "#f77f00", "#fcbf49"],
    )
    return make_line_theme(fig)
