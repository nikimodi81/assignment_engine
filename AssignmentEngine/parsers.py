import csv
from datetime import datetime, time
import config

def parse_time(time_str):
    """Parses HH:MM string to datetime.time object."""
    return datetime.strptime(time_str.strip(), "%H:%M").time()

def load_shift_definitions():
    """Loads shift definitions from CSV into a dictionary."""
    shift_defs = {}
    with open(config.SHIFT_DEFS_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            shift_defs[row['Shift Code'].strip()] = {
                'start_time': parse_time(row['Start UTC (HH:MM)']),
                'end_time': parse_time(row['End UTC (HH:MM)']),
                'name': row['Shift Name'].strip(),
                'desc': row['Description'].strip()
            }
    return shift_defs

def load_team_eligibility():
    """Loads team eligibility records from CSV."""
    eligibility_list = []
    with open(config.ELIGIBILITY_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean fields
            technologies = [t.strip() for t in row['Technologies'].split(',')]
            regions = [r.strip() for r in row['Supported Regions'].split(',')]
            bps = [b.strip() for b in row['Supported Business Processes (BP)'].split(',')]
            
            eligibility_list.append({
                'user_id': row['User ID'].strip(),
                'name': row['Full Name'].strip(),
                'role_type': row['Role Type'].strip(),
                'level': row['Support Level'].strip(),
                'technologies': technologies,
                'regions': regions,
                'bps': bps,
                'skills': row['Primary Skills'].strip(),
                'indicative_desc': row['Indicative Issue Descriptions (For AI Semantic Matching)'].strip()
            })
    return eligibility_list

def get_in_shift_users(day_of_month, current_time_str):
    """
    Checks roster and shift definitions to determine which users are currently in shift.
    """
    shift_defs = load_shift_definitions()
    current_time = parse_time(current_time_str)
    day_col = str(day_of_month).strip()
    
    in_shift = []
    
    with open(config.ROSTER_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_id = row['User ID'].strip()
            name = row['Full Name'].strip()
            
            if day_col not in row:
                continue
                
            shift_code = row[day_col].strip()
            
            if shift_code == 'OFF' or shift_code not in shift_defs:
                continue
                
            times = shift_defs[shift_code]
            start = times['start_time']
            end = times['end_time']
            
            # Check if time is in shift window
            is_active = False
            if start <= end:
                # Normal shift (e.g. 06:00 to 14:00)
                is_active = start <= current_time <= end
            else:
                # Night shift crossing midnight (e.g. 22:00 to 06:00)
                is_active = current_time >= start or current_time <= end
                
            if is_active:
                in_shift.append({
                    'user_id': user_id,
                    'name': name,
                    'shift_code': shift_code
                })
                
    return in_shift

if __name__ == "__main__":
    print(f"Testing parsers for Day {config.SIMULATION_CURRENT_DAY} at {config.SIMULATION_CURRENT_TIME_UTC} UTC:")
    active = get_in_shift_users(config.SIMULATION_CURRENT_DAY, config.SIMULATION_CURRENT_TIME_UTC)
    for u in active:
        print(f" - {u['name']} ({u['user_id']}) is on shift {u['shift_code']}")
