import numpy as np
import pandas as pd
import streamlit as st

def status_label(rul_value: float):
    if rul_value < 300:
        return "Immediate attention"
    if rul_value < 800:
        return "Watchlist"
    return "Stable"

def hero_metric(label: str, value: str, caption: str):
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-label">{label}</div>
            <div class="hero-value">{value}</div>
            <div class="hero-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def get_health_status(value, metric_type):
    if metric_type == "temp":
        if 20 <= value <= 35: return "Optimal", "success"
        elif 15 <= value < 20 or 35 < value <= 45: return "Warning", "warning"
        else: return "Critical", "error"
    elif metric_type == "dod":
        if value <= 65: return "Optimal", "success"
        elif value <= 80: return "Warning", "warning"
        else: return "Critical", "error"
    elif metric_type == "crate":
        if value <= 1.2: return "Optimal", "success"
        elif value <= 2.0: return "Warning", "warning"
        else: return "Critical", "error"
    return "Unknown", "normal"

def calculate_physics_guided_rul(base_rul, curr_temp, curr_dod, curr_crate, new_temp, new_dod, new_crate):
    if base_rul <= 0:
        return 0.0

    def get_temp_penalty(t):
        return np.exp(0.04 * (t - 25))

    curr_temp_factor = get_temp_penalty(curr_temp)
    new_temp_factor = get_temp_penalty(new_temp)
    temp_multiplier = curr_temp_factor / new_temp_factor if new_temp_factor > 0 else 1.0

    dod_multiplier = (curr_dod / new_dod) ** 1.5 if new_dod > 0 else 1.0
    
    crate_multiplier = np.exp((curr_crate - new_crate) * 0.4)

    adjusted_rul = base_rul * temp_multiplier * dod_multiplier * crate_multiplier
    return max(0.0, float(adjusted_rul))

def render_health_and_optimization(selected_row: pd.Series, model_bundle: dict):
    st.markdown("<hr style='border:1px solid rgba(20,33,61,0.1); margin: 30px 0;'>", unsafe_allow_html=True)
    st.markdown("## 🔋 Battery Health & Optimization Sandbox")
    st.markdown("Review current operating habits and simulate adjustments to instantly see the impact on remaining battery life.")

    current_rul = float(selected_row.get("predicted_rul", 0.0))
    features = model_bundle.get("features", []) if model_bundle else []
    
    temp_col = next((col for col in features if 'temp' in col.lower()), None)
    dod_col = next((col for col in features if 'dod' in col.lower() or 'discharge' in col.lower()), None)
    crate_col = next((col for col in features if 'rate' in col.lower() or 'c_' in col.lower() or 'current' in col.lower()), None)

    raw_temp = selected_row.get(temp_col, 25.0) if temp_col else 25.0
    raw_dod = selected_row.get(dod_col, 80.0) if dod_col else 80.0
    raw_crate = selected_row.get(crate_col, 1.0) if crate_col else 1.0

    try:
        curr_temp = float(raw_temp)
        if not (-20 <= curr_temp <= 80): curr_temp = 25.0
    except:
        curr_temp = 25.0

    try:
        curr_dod = float(raw_dod)
        if 0.0 < curr_dod <= 1.0: curr_dod *= 100.0
        if not (10 <= curr_dod <= 100): curr_dod = 80.0
    except:
        curr_dod = 80.0

    try:
        curr_crate = float(raw_crate)
        if not (0.1 <= curr_crate <= 10.0): curr_crate = 1.0
    except:
        curr_crate = 1.0

    st.markdown("### 1. Current Operating Status")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    temp_label, temp_color = get_health_status(curr_temp, "temp")
    with status_col1:
        st.metric("Current Temperature", f"{curr_temp:.1f} °C", temp_label, delta_color="off")
        if temp_color == "error": st.error("Severe heat degrades battery fast.")
        elif temp_color == "warning": st.warning("Elevated thermal stress.")
        else: st.success("Safe operating zone for Indian ambient.")
        
    dod_label, dod_color = get_health_status(curr_dod, "dod")
    with status_col2:
        st.metric("Current Depth of Discharge", f"{curr_dod:.1f} %", dod_label, delta_color="off")
        if dod_color == "error": st.error("Deep cycling kills cells.")
        elif dod_color == "warning": st.warning("Moderate wear.")
        else: st.success("Healthy shallow cycles.")

    crate_label, crate_color = get_health_status(curr_crate, "crate")
    with status_col3:
        st.metric("Current C-Rate", f"{curr_crate:.1f} C", crate_label, delta_color="off")
        if crate_color == "error": st.error("Extreme fast charging.")
        elif crate_color == "warning": st.warning("Slightly elevated rate.")
        else: st.success("Safe charging speed.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.info("💡 **Practical EV Recommendation for India:** To maximize fleet ROI in high-ambient operations, aim to limit daily **DoD to 60-70%** (e.g., operate strictly between 20%-80% SoC). Prioritize overnight Level 2 AC charging to keep average **C-Rate below 0.5C**, and utilize shaded depot parking or active cooling to maintain battery **Temperatures near 30-35°C**.")

    st.markdown("### 2. Simulate Improvements")
    st.caption("Adjust the sliders to simulate new operating conditions. The physics-guided model will recalculate remaining life.")

    if current_rul <= 0.0:
        st.warning("⚠️ **End of Life Reached:** This battery is currently projected to have 0 cycles remaining. Operating changes cannot revive it at this stage.")

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        new_temp_val = np.clip(float(curr_temp), 15.0, 55.0)
        new_temp = st.slider("🌡️ Target Temperature (°C)", 15.0, 55.0, new_temp_val, 1.0)
    with sim_col2:
        new_dod = st.slider("🔋 Max Depth of Discharge (%)", 10.0, 100.0, float(curr_dod), 5.0)
    with sim_col3:
        new_crate = st.slider("⚡ Charge/Discharge C-Rate", 0.1, 5.0, float(curr_crate), 0.1)

    new_rul = calculate_physics_guided_rul(current_rul, curr_temp, curr_dod, curr_crate, new_temp, new_dod, new_crate)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 3. Projected Impact")
    
    result_col1, result_col2 = st.columns(2)
    
    delta_cycles = new_rul - current_rul
    delta_cycles_pct = (delta_cycles / current_rul * 100) if current_rul > 0 else 0.0
    
    curr_months = current_rul / 30.0
    new_months = new_rul / 30.0
    delta_months = new_months - curr_months
    delta_months_pct = (delta_months / curr_months * 100) if curr_months > 0 else 0.0

    sign_c = "+" if delta_cycles >= 0 else ""
    sign_p = "+" if delta_cycles_pct >= 0 else ""
    color_c = "#2a9d8f" if delta_cycles >= 0 else "#d62828"

    with result_col1:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.8); border: 1px solid rgba(20,33,61,0.1); border-radius: 12px; padding: 20px; text-align: center;">
                <h4 style="margin:0; color: #5f6c7b;">New Projected Cycles</h4>
                <h1 style="margin: 10px 0; font-size: 2.8rem; color: #0f172a;">{new_rul:.0f}</h1>
                <p style="margin:0; font-weight: bold; font-size: 1.1rem; color: {color_c}">
                    {sign_c}{delta_cycles:.0f} cycles ({sign_p}{delta_cycles_pct:.1f}%)
                </p>
            </div>
            """, unsafe_allow_html=True
        )

    sign_m = "+" if delta_months >= 0 else ""
    sign_mp = "+" if delta_months_pct >= 0 else ""
    color_m = "#2a9d8f" if delta_months >= 0 else "#d62828"

    with result_col2:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.8); border: 1px solid rgba(20,33,61,0.1); border-radius: 12px; padding: 20px; text-align: center;">
                <h4 style="margin:0; color: #5f6c7b;">New Projected Months</h4>
                <h1 style="margin: 10px 0; font-size: 2.8rem; color: #0f172a;">{new_months:.1f}</h1>
                <p style="margin:0; font-weight: bold; font-size: 1.1rem; color: {color_m}">
                    {sign_m}{delta_months:.1f} months ({sign_mp}{delta_months_pct:.1f}%)
                </p>
            </div>
            """, unsafe_allow_html=True
        )
