import config
import parsers
import matcher
import servicenow_mock

def run_auto_assignment_simulation():
    print("=" * 70)
    print("      STARTING AI AUTO-ASSIGNMENT SIMULATOR FOR SERVICENOW")
    print("=" * 70)
    print(f"Simulating Context:")
    print(f" - Date: Day {config.SIMULATION_CURRENT_DAY} of the Month")
    print(f" - Time: {config.SIMULATION_CURRENT_TIME_UTC} UTC")
    
    # 1. Fetch who is currently in shift
    in_shift_roster = parsers.get_in_shift_users(config.SIMULATION_CURRENT_DAY, config.SIMULATION_CURRENT_TIME_UTC)
    in_shift_ids = {u['user_id'] for u in in_shift_roster}
    
    print("\n[Roster Parsing]")
    print(f"Active Team Members on Shift ({len(in_shift_roster)}):")
    for u in in_shift_roster:
        print(f" - {u['name']} ({u['user_id']}) [Shift: {u['shift_code']}]")
        
    if not in_shift_roster:
        print("WARNING: No team members are currently on shift. Tickets cannot be auto-assigned!")
        return

    # 2. Load team eligibility
    team_eligibility = parsers.load_team_eligibility()
    
    # 3. Instantiate ServiceNow client
    sn_client = servicenow_mock.ServiceNowMockClient()
    unassigned_tickets = sn_client.get_unassigned_tickets()
    
    print(f"\n[ServiceNow Polling]")
    print(f"Found {len(unassigned_tickets)} unassigned tickets to process.\n")
    
    print("=" * 70)
    print("PROCESSING TICKETS:")
    print("=" * 70)

    for ticket in unassigned_tickets:
        print(f"\nProcessing Ticket {ticket['sys_id']} ({ticket['type']}):")
        print(f" - Title: '{ticket['short_description']}'")
        print(f" - Region: {ticket['region']} | BP: {ticket['bp']}")
        
        # A. Find eligible agents based on capability
        candidates = matcher.find_eligible_agents(ticket, team_eligibility)
        
        if not candidates:
            print(" x Result: No eligible agents found with matching skills/capabilities.")
            continue
            
        # B. Filter by active shift
        in_shift_candidates = []
        for agent, match_type, score, reason in candidates:
            if agent['user_id'] in in_shift_ids:
                # Get current queue size
                queue_count = sn_client.get_user_queue_count(agent['user_id'])
                in_shift_candidates.append({
                    'agent': agent,
                    'match_type': match_type,
                    'score': score,
                    'reason': reason,
                    'queue_count': queue_count
                })
                
        if not in_shift_candidates:
            print(" [X] Result: Eligible candidates found, but NONE are currently on shift:")
            for agent, match_type, _, _ in candidates:
                print(f"   - {agent['name']} ({agent['user_id']}) [{agent['role_type']}] is OFF shift.")
            continue
            
        # C. Select candidate: Least queue count first, tie-breaker: highest score
        # Sort key: queue_count ascending, then score descending
        in_shift_candidates.sort(key=lambda x: (x['queue_count'], -x['score']))
        
        print(" Candidates analyzed:")
        for idx, cand in enumerate(in_shift_candidates):
            marker = "-->" if idx == 0 else "   "
            print(f"   {marker} {cand['agent']['name']} ({cand['agent']['user_id']}):")
            print(f"       Role Match: {cand['match_type']} (Score: {cand['score']:.2f})")
            print(f"       Active Queue Load: {cand['queue_count']} tickets")

        selected = in_shift_candidates[0]
        selected_agent = selected['agent']
        
        # D. Assign ticket
        success = sn_client.assign_ticket(ticket['sys_id'], selected_agent['user_id'])
        if success:
            print(f" [ASSIGNED] to {selected_agent['name']} ({selected_agent['user_id']})")
        else:
            print(" [ERROR] Error assigning ticket.")

    print("\n" + "=" * 70)
    print("SIMULATION SUMMARY")
    print("=" * 70)
    print("Final Agent Queues:")
    for agent in team_eligibility:
        print(f" - {agent['name']} ({agent['user_id']}): {sn_client.get_user_queue_count(agent['user_id'])} tickets")
    print("=" * 70)

if __name__ == "__main__":
    run_auto_assignment_simulation()
