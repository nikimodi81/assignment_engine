import math
import re

def clean_text(text):
    """Cleans text by lowering case and removing punctuation."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text

def get_tokens(text):
    """Splits text into a bag of words, removing common stopwords."""
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'of', 'for', 'my', 'need', 'unable'}
    words = clean_text(text).split()
    return [w for w in words if w not in stopwords and len(w) > 1]

def calculate_cosine_similarity(text1, text2):
    """
    Computes a simple term frequency (TF) cosine similarity.
    This works out-of-the-box without requiring scikit-learn or external model servers.
    """
    tokens1 = get_tokens(text1)
    tokens2 = get_tokens(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
        
    # Create frequency dictionaries
    freq1 = {}
    for t in tokens1:
        freq1[t] = freq1.get(t, 0) + 1
        
    freq2 = {}
    for t in tokens2:
        freq2[t] = freq2.get(t, 0) + 1
        
    # Get unique words
    all_words = set(freq1.keys()).union(set(freq2.keys()))
    
    dot_product = 0.0
    sum_sq1 = 0.0
    sum_sq2 = 0.0
    
    for w in all_words:
        v1 = freq1.get(w, 0)
        v2 = freq2.get(w, 0)
        dot_product += v1 * v2
        sum_sq1 += v1 * v1
        sum_sq2 += v2 * v2
        
    if sum_sq1 == 0.0 or sum_sq2 == 0.0:
        return 0.0
        
    return dot_product / (math.sqrt(sum_sq1) * math.sqrt(sum_sq2))

def calculate_gemini_similarity(text1, text2, api_key=None):
    """
    Placeholder/template for actual Gemini API Embeddings:
    Once you configure your Google Gemini API key, you can swap this in.
    
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    emb1 = genai.embed_content(model="models/text-embedding-004", contents=text1)
    emb2 = genai.embed_content(model="models/text-embedding-004", contents=text2)
    # Then calculate dot product or cosine similarity of the vectors...
    """
    pass

def find_eligible_agents(ticket, team_eligibility):
    """
    Filters agents based on:
    1. Region & BP match for Flow Supervisors.
    2. Region & BP & Tech stack/AI semantic similarity for Tech Specialists.
    
    Returns a list of tuples: (agent, role_match_type, score, reason)
    """
    ticket_region = ticket.get("region", "").strip().lower()
    ticket_bp = ticket.get("bp", "").strip().lower()
    ticket_text = f"{ticket.get('short_description', '')} {ticket.get('description', '')}"
    
    eligible = []
    
    for agent in team_eligibility:
        # Check Region capability
        agent_regions = [r.lower() for r in agent['regions']]
        region_match = "all" in agent_regions or ticket_region in agent_regions
        
        # Check BP capability
        agent_bps = [b.lower() for b in agent['bps']]
        bp_match = "all" in agent_bps or ticket_bp in agent_bps
        
        if not (region_match and bp_match):
            continue  # Region and BP are hard requirements
            
        # If agent is a Flow Supervisor, they match the supervisor route
        if agent['role_type'] == "Flow Supervisor":
            reason = f"Flow Supervisor matching Region ({ticket_region.upper()}) & BP ({ticket_bp.title()})."
            eligible.append((agent, "Flow Supervisor Match", 1.0, reason))
            continue
            
        # Otherwise, calculate similarity of ticket to agent skills/descriptions
        similarity_score = calculate_cosine_similarity(ticket_text, agent['indicative_desc'])
        
        # If similarity score is high enough (e.g. > 0.05 for this simple token matching)
        if similarity_score > 0.05:
            reason = f"Tech Specialist with {similarity_score:.2f} semantic similarity match to skill profile."
            eligible.append((agent, "Tech Specialist Semantic Match", similarity_score, reason))
            
    # Sort by score descending
    eligible.sort(key=lambda x: x[2], reverse=True)
    return eligible

if __name__ == "__main__":
    # Test matching
    test_eligibility = [
        {
            'user_id': 'john.doe',
            'name': 'John Doe',
            'role_type': 'Tech Specialist',
            'regions': ['AMER'],
            'bps': ['Order-to-Cash', 'Billing'],
            'indicative_desc': 'Cannot login to my Windows account; Password reset; Outlook installation'
        },
        {
            'user_id': 'jane.smith',
            'name': 'Jane Smith',
            'role_type': 'Flow Supervisor',
            'regions': ['EMEA', 'APAC'],
            'bps': ['Procure-to-Pay', 'Supply Chain'],
            'indicative_desc': 'Tibco ESB queue full; Purchase order integration error'
        }
    ]
    
    test_ticket = {
        'short_description': 'Need help with outlook mail setup',
        'description': 'Outlook client profile configuration failed',
        'region': 'AMER',
        'bp': 'Billing'
    }
    
    print("Testing matching engine:")
    results = find_eligible_agents(test_ticket, test_eligibility)
    for agent, rtype, score, reason in results:
        print(f" - Candidate: {agent['name']} ({agent['user_id']}) | Type: {rtype} | Score: {score:.2f} | Reason: {reason}")
