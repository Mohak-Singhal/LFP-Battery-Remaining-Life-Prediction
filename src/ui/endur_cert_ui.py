import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from src.services.battery_engine import BatteryEngine
from src.services.certificate_generator import CertificateGenerator
from src.services.data_service import latest_snapshot

def render_endur_cert_tab(predictions_df: pd.DataFrame):
    st.header("🔋 Endur-Cert: Battery Blue Book & Certification")
    st.markdown("Transform RUL into Financial Value. Turn Second-Life into Sustainable Business.")
    st.divider()

    if predictions_df.empty:
        st.warning("No predictions loaded. Cannot calculate 2nd life valuation.")
        return

    # Extract unique batteries based on latest snapshot
    snapshot = latest_snapshot(predictions_df)
    
    # Map to Endur-Cert format
    input_df = pd.DataFrame({
        'Battery_ID': snapshot['battery_id'],
        'Predicted_RUL': snapshot['predicted_rul'],
        # If temperature is not aggressively tracked in parquet output, fall back to Indian average
        'Average_Operating_Temperature': snapshot.get('temperature', 35.0)
    })

    # Engine configs
    col1, col2 = st.columns([1, 2])
    with col1:
        new_pack_price = st.number_input(
            "New Battery Pack Price (₹)",
            value=250000,
            min_value=100000,
            step=10000,
            help="Reference price for a brand-new battery pack"
        )
    
    # Initialize engine dynamically based on slider
    engine = BatteryEngine(new_pack_price=new_pack_price)
    
    with st.spinner("🔄 Assessing fleet..."):
        assessed_df = engine.process_fleet(input_df)
        summary = engine.get_fleet_summary(assessed_df)

    st.success(f"✅ Auto-Assessed {len(input_df)} fleet batteries.")
    st.divider()

    # --- DASHBOARD ---
    st.subheader("Fleet Valuation Dashboard")
    
    scol1, scol2, scol3, scol4 = st.columns(4)
    with scol1: st.metric("Total Batteries", summary['Total_Batteries'])
    with scol2: st.metric("Total Residual Value", f"₹{summary['Total_Residual_Value_INR']:,.0f}")
    with scol3: st.metric("Avg Health Score", f"{summary['Avg_Health_Score_%']:.1f}%")
    with scol4: st.metric("Avg Temp", f"{summary['Avg_Operating_Temp_C']:.1f}°C")

    # Grade Distribution
    col1, col2 = st.columns(2)
    with col1:
        grade_counts = assessed_df['Grade'].value_counts()
        grade_counts = grade_counts.reindex(['Grade A', 'Grade B', 'Grade C'], fill_value=0)
        fig_pie = px.pie(
            values=grade_counts.values,
            names=grade_counts.index,
            color=grade_counts.index,
            color_discrete_map={'Grade A': '#27AE60', 'Grade B': '#FFD700', 'Grade C': '#E74C3C'},
            title="Battery Grade Distribution",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        grade_value = assessed_df.groupby('Grade')['Residual_Value_INR'].sum()
        grade_value = grade_value.reindex(['Grade A', 'Grade B', 'Grade C'], fill_value=0)
        fig_bar = px.bar(
            x=grade_value.index,
            y=grade_value.values,
            color=grade_value.index,
            color_discrete_map={'Grade A': '#27AE60', 'Grade B': '#FFD700', 'Grade C': '#E74C3C'},
            title="Total Residual Value by Grade",
            labels={'x': 'Grade', 'y': 'Value (₹)'}
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- CERTIFICATES ---
    st.divider()
    st.subheader("📜 Digital Battery Passports")
    st.write("Generate JSON or PDF Grade certificates to secure valuation for asset liquidation.")

    if 'cert_gen' not in st.session_state:
        st.session_state.cert_gen = CertificateGenerator(output_dir='certificates')
    
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        selected_batteries = st.multiselect(
            "Select specific batteries to certify (Empty = All):",
            options=assessed_df['Battery_ID'].tolist()
        )
    with fcol2:
        st.write("Format Generation:")
        gen_pdf = st.checkbox("📄 PDF Certificates", value=True)
        gen_json = st.checkbox("📋 JSON Certificates", value=False)
    
    if st.button("🏆 Generate Certificates", type="primary"):
        df_to_certify = assessed_df if not selected_batteries else assessed_df[assessed_df['Battery_ID'].isin(selected_batteries)]
        
        format_choice = 'both' if (gen_pdf and gen_json) else ('pdf' if gen_pdf else 'json')
        with st.spinner("⏳ Generating..."):
            results = st.session_state.cert_gen.generate_batch_certificates(df_to_certify, format=format_choice)
        st.success(f"✅ Generated {len(df_to_certify)} Certificates in `certificates/` directory!")
