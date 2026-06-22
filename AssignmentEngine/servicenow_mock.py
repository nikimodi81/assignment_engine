import random

# A mock data store representing the current state of ServiceNow tickets.
MOCK_TICKETS = [
    {
        "sys_id": "INC001001",
        "type": "Incident",
        "short_description": "ETL job failed on server 4",
        "description": "Informatica workflow wf_billing_load aborted due to DB connection loss",
        "region": "AMER",
        "bp": "Billing",
        "assigned_to": None
    },
    {
        "sys_id": "RITM002002",
        "type": "RITM",
        "short_description": "Macbook Pro request for new joiner",
        "description": "Procure standard laptop package for EMEA engineering team member",
        "region": "EMEA",
        "bp": "Order-to-Cash",
        "assigned_to": None
    },
    {
        "sys_id": "INC003003",
        "type": "Incident",
        "short_description": "Tibco ESB queue processing blocked",
        "description": "EMEA supply chain portal reports HTTP 504 Gateway Timeout on Tibco",
        "region": "EMEA",
        "bp": "Supply Chain",
        "assigned_to": None
    },
    {
        "sys_id": "INC004004",
        "type": "Incident",
        "short_description": "SAP billing interface failure",
        "description": "Order processing stuck due to billing data load timeout",
        "region": "AMER",
        "bp": "Order-to-Cash",
        "assigned_to": None
    },
    {
        "sys_id": "INC005005",
        "type": "Incident",
        "short_description": "SSO integration failure on AWS portal",
        "description": "Major security warning: Identity Provider sync is broken",
        "region": "APAC",
        "bp": "Procure-to-Pay",
        "assigned_to": None
    }
]

# Mock active ticket counts in team member queues
MOCK_QUEUES = {
    "nikhil.modi": 4,      # e.g., John is L1 with higher volume
    "anup.roy": 2,    # e.g., Jane is L2 Flow Supervisor with 2 tickets
    "kunal.nayak": 1,   # Bob is L3 with 1 high-severity ticket
    "vipul.kabadi": 3     # Alice has 3 tickets
}

class ServiceNowMockClient:
    def __init__(self):
        self.tickets = MOCK_TICKETS
        self.queues = MOCK_QUEUES

    def get_unassigned_tickets(self):
        """Simulates fetching tickets where assigned_to is empty."""
        return [t for t in self.tickets if t["assigned_to"] is None]

    def get_user_queue_count(self, user_id):
        """Simulates counting active tickets in the user's queue."""
        return self.queues.get(user_id, 0)

    def assign_ticket(self, ticket_id, user_id):
        """Simulates assigning a ticket to an agent."""
        for t in self.tickets:
            if t["sys_id"] == ticket_id:
                t["assigned_to"] = user_id
                # Update queue count for simulator
                self.queues[user_id] = self.queues.get(user_id, 0) + 1
                return True
        return False
