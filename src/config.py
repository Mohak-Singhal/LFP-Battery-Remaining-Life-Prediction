from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Paths
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_TRAIN_DATA = DATA_DIR / "processed" / "synthetic_battery_rul.csv"
DEFAULT_TEST_DATA = DATA_DIR / "processed" / "synthetic_battery_rul.csv"
DEFAULT_DATA_PATH = DEFAULT_TEST_DATA

# Model Paths
MODEL_DIR = PROJECT_ROOT / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "rul_model.pkl"
DEFAULT_METRICS_PATH = MODEL_DIR / "training_metrics.json"
DEFAULT_DEPLOYABILITY_PATH = MODEL_DIR / "deployability_report.json"

# Results Paths
RESULTS_DIR = PROJECT_ROOT / "results"
DEFAULT_PREDICTIONS_PATH = RESULTS_DIR / "predictions.parquet"
DEFAULT_TEST_METRICS_PATH = RESULTS_DIR / "test_metrics.json"
DEFAULT_PLOT_DIR = RESULTS_DIR / "plots"

# Constants
VALIDATION_SPLITS = 3
VALIDATION_TEST_SIZE = 0.2
FINAL_TRAIN_SAMPLE_SIZE = 250000

MODEL_FEATURES = [
    'cycle_number', 'voltage', 'current', 'current_abs', 'temperature', 'soc',
    'dod', 'c_rate', 'capacity_remaining', 'internal_resistance', 'energy_throughput',
    'cycle_age', 'rolling_temperature', 'avg_dod', 'charge_rate_mean',
    'rolling_voltage_avg', 'capacity_fade', 'capacity_fade_rate', 'thermal_stress_index',
    'health_score', 'power_draw', 'temperature_soc_interaction', 'voltage_drop_from_avg',
    'temperature_stress_factor', 'dod_stress_factor', 'c_rate_stress_factor',
    'equivalent_full_cycles', 'combined_stress_index', 'capacity_margin_to_eol',
    'degradation_rate_est', 'physics_rul_proxy', 'remaining_calendar_months_proxy',
]
