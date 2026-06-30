# assignment_engine

A ServiceNow AI Auto-Assignment Hub that routes incoming tickets to team members based on shift status, region/BP capability, active queue load, and AI semantic skill matching.

The project ships in two flavors:
- **CLI simulator** (`main.py`) — prints the auto-assignment run to the terminal.
- **Streamlit web UI** (`app.py`) — interactive dashboard with checkboxes, agent cards, and an assignment log.

## Project Structure

| File / Folder | Purpose |
|---|---|
| `app.py` | Streamlit web UI for interactive ticket assignment |
| `main.py` | CLI simulator that runs the same auto-assignment logic end-to-end |
| `config.py` | Paths to CSV data + simulation day/time defaults |
| `parsers.py` | Loads CSV roster, shift definitions, and team eligibility; computes who is in shift |
| `matcher.py` | Cosine-similarity-based semantic matching + role/region/BP filtering |
| `servicenow_mock.py` | In-memory mock of the ServiceNow API (tickets + queue counts) |
| `roster_template.csv` | Daily shift assignments (Day 1–31 columns) |
| `shift_definitions.csv` | Shift start/end UTC windows |
| `team_eligibility_template.csv` | Agent skills, regions, BPs, and tech stack |
| `requirement.txt` | Python package dependencies |
| `assignment_engine/` | Optional local Python virtual environment (pyvenv.cfg present) |

## Requirements

- **Python 3.8+**
- pip

## Setup

### 1. Create and activate a virtual environment

From the project root (`assignment_engine/`):

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> A pre-existing venv is also available at `assignment_engine/` (it has its own `pyvenv.cfg`). To use it instead, activate that one directly:
> - Windows: `assignment_engine\Scripts\activate.bat`
> - macOS/Linux: `source assignment_engine/bin/activate`

### 2. Install dependencies

```bash
pip install -r requirement.txt
```

This installs:
- `streamlit` — drives the web UI
- `pandas` — used by the Streamlit app

All other modules used by the project (`math`, `re`, `csv`, `datetime`, `os`, `random`) are part of Python's standard library.

## Running the Project

You can run the project in two ways.

### Option A — Streamlit Web UI (recommended)

From the project root (`assignment_engine/`):

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`) in your browser.

In the UI:
1. Use the **left sidebar** to adjust the simulated day of the month and current UTC time.
2. In the main panel, tick the checkboxes next to unassigned tickets.
3. Click **Assign Selected** to auto-route them.
4. Scroll down to see the **Assignment Execution & Reason Logs**.
5. The right panel shows live **Shift & Queue Dashboard** cards for every agent.

### Option B — CLI Simulator

From the project root (`assignment_engine/`):

```bash
python main.py
```

This prints, in the terminal:
- The simulated date/time context.
- The active team members currently in shift.
- Each unassigned ticket and the candidate analysis.
- The final assignment and updated queue counts.

To change the simulated day or time, edit `SIMULATION_CURRENT_DAY` and `SIMULATION_CURRENT_TIME_UTC` in `config.py` and re-run.

## Customizing the Data

- **Roster** (`roster_template.csv`) — `OFF` or a shift code per agent per day-of-month.
- **Shifts** (`shift_definitions.csv`) — define each shift's start/end in UTC.
- **Team eligibility** (`team_eligibility_template.csv`) — comma-separated technologies, regions, BPs, and an "Indicative Issue Descriptions" field used for AI semantic matching.
- **Mock ServiceNow tickets** — edit `MOCK_TICKETS` and `MOCK_QUEUES` in `servicenow_mock.py`.

## How Matching Works

1. `parsers.get_in_shift_users()` reads the roster CSV column for the current day and checks the time against `shift_definitions.csv`.
2. `parsers.load_team_eligibility()` reads the agent capability CSV.
3. `matcher.find_eligible_agents()` filters agents by region & BP (hard requirements), then ranks Tech Specialists by cosine similarity between the ticket text and the agent's `indicative_desc`.
4. The caller intersects eligible agents with the in-shift set, then picks the agent with the **lowest active queue** (tie-break: highest similarity score).
5. `servicenow_mock.ServiceNowMockClient` is used by `main.py` to track queue counts; `app.py` tracks them in `st.session_state` instead.

## Troubleshooting

- **`streamlit` command not found** — make sure your virtual environment is activated, then re-run `pip install -r requirement.txt`.
- **`ModuleNotFoundError: No module named 'streamlit'`** — you are probably running outside the venv. Activate it (see Setup step 1).
- **Time format error in the UI** — enter the sidebar time as `HH:MM` in 24-hour UTC format (e.g. `13:30`).
- **All tickets show as "Unassigned"** — no team members are on shift for the selected day/time. Adjust the sliders in the sidebar.
