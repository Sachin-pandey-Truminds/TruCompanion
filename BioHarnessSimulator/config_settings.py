"""
Configuration settings for the BioHarness Vitals Simulator
"""

# Server Configuration
HTTP_SERVER_HOST = "localhost"
HTTP_SERVER_PORT = 8000

# Simulator Configuration
DEFAULT_SIMULATION_INTERVAL_SECONDS = 10
DEFAULT_PATIENT_IDENTIFIER = "patient_001"
DEFAULT_DEVICE_IDENTIFIER = "BioHarness_Sim_001"
MINIMUM_SIMULATION_INTERVAL_SECONDS = 1

# Rule Engine Integration
RULE_ENGINE_BASE_URL = "http://localhost:3000"
RULE_ENGINE_VITALS_ENDPOINT = "/api/vitals/stream"
RULE_ENGINE_CONNECTION_TIMEOUT_SECONDS = 5
RULE_ENGINE_REQUEST_RETRY_COUNT = 3

# UI Broadcasting Configuration
UI_WEBSOCKET_URL = "ws://localhost:3001/vitals"
UI_HTTP_ENDPOINT = "http://localhost:3001/api/vitals/update"
UI_CONNECTION_TIMEOUT_SECONDS = 3

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE_PATH = "simulator.log"
ENABLE_CONSOLE_LOGGING = True
ENABLE_FILE_LOGGING = True

# Data Broadcasting Configuration
ENABLE_RULE_ENGINE_BROADCASTING = True
ENABLE_UI_BROADCASTING = True
BROADCASTING_RETRY_DELAY_SECONDS = 2
MAX_BROADCASTING_RETRIES = 3

# Vital Signs Normal Ranges (for reference)
NORMAL_VITAL_RANGES = {
    "heart_rate": (60, 100),
    "bp_systolic": (90, 140),
    "bp_diastolic": (60, 90),
    "spo2": (95, 100),
    "temperature": (36.1, 37.2),
    "respiratory_rate": (12, 20)
}

# Vital Signs Abnormal Ranges
ABNORMAL_VITAL_RANGES = {
    "heart_rate": (40, 180),
    "bp_systolic": (70, 200),
    "bp_diastolic": (40, 120),
    "spo2": (85, 94),
    "temperature": (35.0, 40.0),
    "respiratory_rate": (8, 30)
}

# Vital Signs Emergency Ranges
EMERGENCY_VITAL_RANGES = {
    "heart_rate": (30, 220),
    "bp_systolic": (60, 250),
    "bp_diastolic": (30, 150),
    "spo2": (70, 84),
    "temperature": (32.0, 42.0),
    "respiratory_rate": (5, 40)
}