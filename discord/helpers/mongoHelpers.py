# --- MongoDB Helper Functions ---

# TODO: Write a function to force data updates incase the bot is outdated or the cycle is too long.

# Self explanatory
def get_last_timestamp(collection_file):

    # Retrieving first document in collection
    # Should reference the timestamp document
    doc = collection_file.find_one()
    time = doc['timestamp']

    return time

# Sends all high impact news entries (most relevant to traders)
# returns a list of objects. all of which are navigated using obj['index']
def high_impact_news(collection_file):

    query = { 'impact-level': "High Impact Expected" }
    docs = collection_file.find(query)

    events = []
    
    for event in docs:
        events.append(event)

    return events

def currency_specific_news(collection_file, currency):

    query = { 'currency-impacted': f"{currency}" }
    docs = collection_file.find(query)

    events = []
    
    for event in docs:
        events.append(event)

    return events