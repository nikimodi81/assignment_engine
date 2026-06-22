import os

# Base Directories
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data Paths
ROSTER_PATH = os.path.join(WORKSPACE_DIR, "roster_template.csv")
SHIFT_DEFS_PATH = os.path.join(WORKSPACE_DIR, "shift_definitions.csv")
ELIGIBILITY_PATH = os.path.join(WORKSPACE_DIR, "team_eligibility_template.csv")

# Simulation Settings
SIMULATION_CURRENT_DAY = 17  # Simulate 17th of the month
SIMULATION_CURRENT_TIME_UTC = "13:30"  # Simulate 13:30 UTC
SIMULATION_POLL_INTERVAL_SEC = 2
