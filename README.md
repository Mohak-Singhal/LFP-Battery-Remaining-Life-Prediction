# 🔋 LFP Battery Remaining Useful Life (RUL) Intelligence Studio

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![XGBoost](https://img.shields.io/badge/ML-XGBoost-orange)
![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)

A professional, domain-driven machine learning platform for predicting the Remaining Useful Life (RUL) of Lithium Iron Phosphate (LFP) Electric Vehicle batteries. This robust architecture uses advanced feature engineering, physics-informed degradation stressors, and tree-based regression models (XGBoost/Random Forest) to triage fleet risks and provide highly reliable forecast envelopes.

---

## 🚀 Vision & Key Capabilities

- **Command Center Dashboard:** A premium, glassmorphic Streamlit UI providing a judge-facing view spanning from single-battery failure prognostics to fleet-wide degradation trajectories.
- **Physics-Informed Modeling:** Combines data-driven XGBoost forecasts with domain-specific penalty algorithms capturing the compounded stress of high **C-Rates**, dense **Depth of Discharges (DoD)**, and punishing **Temperatures** (specifically adapted for high-ambient Indian deployment environments).
- **Confidence Metrics:** Forecasts don't just output a number; they yield prediction intervals (`Upper` and `Lower` confidence bounds) alongside an Out-Of-Distribution (OOD) safety flag scanner to guarantee inference credibility.
- **Simulation Sandbox:** Predict the impact of operational changes live. Simulate adjustments like capping charge rates and limiting DoD to quantify how many extra life-cycles or months an EV asset might gain.

---

## 🧭 Architecture

The repository enforces a strict separation of concerns, migrating away from monolithic notebooks into a clean SaaS-ready structure:
```text
LFP-Battery-Remaining-Life-Prediction/
├── 📁 data/                        # Raw datasets and processed simulation files
├── 📁 models/                      # Pickled model binaries, deployability reports, & training metrics
├── 📁 results/                     # Batch prediction inference CSVs
├── 📁 src/                         # Main application source code
│   ├── 📁 data/                    # Ingestion loaders, cleaning pipelines, and feature engineers
│   ├── 📁 models/                  # Offline training workflows, evaluation, and degradation logic
│   ├── 📁 services/                # Headless business logic, fleet aggregations, and inferencing
│   ├── 📁 ui/                      # Streamlit display components, style tokens, and Plotly charts
│   ├── app.py                      # Main Streamlit command center entrypoint
│   └── config.py                   # Centralized immutable project constants & paths
└── README.md
```

---

## 🛠 Usage & Execution Pipeline

The solution spans three decoupled phases: **Training**, **Inference**, and **Serving**.

### 1. Data Processing and Offline Training
Train the core models (Random Forest and XGBoost) using Group-Shuffle Splits to prevent data leakage and evaluate performance.
```bash
# Ensure you are at the project root folder
export PYTHONPATH=.
python3 -m src.models.train_model --data data/processed/synthetic_battery_rul.csv
```
_This outputs the compiled `rul_model.pkl` and `training_metrics.json` into the `models/` directory._

### 2. Batch Inference
Score a battery dataset to generate predicted lifetimes, compute confidence envelopes, flag anomalous outliers, and extract degradation business logic.
```bash
export PYTHONPATH=.
python3 -m src.models.predict_rul --data data/processed/synthetic_battery_rul.csv
```
_This outputs a rich `predictions.csv` payload into the `results/` directory._

### 3. Serving the Intelligence Studio
Launch the professional, dark-themed Command Center dashboard. The web client will automatically read the latest inference payload and model deployment bundle.
```bash
export PYTHONPATH=.
streamlit run src/app.py
```

---

## 💡 Practical Insights & Optimization
The Streamlit dashboard includes built-in driver importance features and sensitivity optimizations. Users can adjust parameters using the **Optimization Sandbox**, which dynamically projects lifecycle gains when limiting Depth of Discharge (DoD) to `60-70%`, enforcing a `0.5C` average charge rate, and maintaining operational temperatures in the realistic Indian standard range of `30-35°C`.
