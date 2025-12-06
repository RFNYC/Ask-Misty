# --- MongoDB Helper Functions ---

# Self explanatory
def get_last_timestamp(collection_file):

    # Retrieving first document in collection
    # Should reference the timestamp document
    doc = collection_file.find_one()
    time = doc['timestamp']

    return time

def get_all_news(collection_file):

    events = []

    doc = collection_file.find({})
    for event in doc:
        events.append(event)
    
    return events

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

def pair_specific_news(collection_file, currency1, currency2):
    events = []

    query = { 'currency-impacted': f"{currency1}" }
    docs = collection_file.find(query)

    for event in docs:
        events.append(event)

    query = { 'currency-impacted': f"{currency2}" }
    docs = collection_file.find(query)

    for event in docs:
        events.append(event)

    
    return events

# not optimal time complexity but stop judging me 
def register_guild(collection_file, guild_id, server_name):
    servers = set()

    
    docs = collection_file.find({
        "guild-id": { "$exists": True } 
    })

    for server in docs:
        servers.add(server['guild-id'])
    
    if guild_id not in servers:
        
        new_server = {
            "server": "",
            "guild-id": "",
            "announcement-channel": "",
            "strategies": {}
        }

        new_server["server"] = server_name
        new_server["guild-id"] = guild_id

        collection_file.insert_one(new_server)
        response = f"Server-ID:{guild_id} registered with Misty successfully."

        return response
    else:

        response = f"Server-ID:{guild_id} already registered with Misty."

        return response

def check_guild_exists(collection_file, guild_id):

    temp = []

    doc = collection_file.find({ "guild-id": f'{guild_id}' })

    for server in doc:
        temp.append(server)

    if len(temp) == 0:
        response = "[404]"
        return response
    else:
        response = "[200]"
        return response
    
def set_announcement_channel(collection_file, guild_id, channel_id):

    query = { "guild-id": f'{guild_id}' }

    # praying this works
    new_values = {"$set": {"announcement-channel": f"{channel_id}"}}
    res = collection_file.update_one(query, new_values)

    if res.modified_count == 1:
        print(res)

        response = "[201]"
        return response
    else:
        response = "[400]"
        return response

def get_guild_information(collection_file, guild_id):

    if check_guild_exists(collection_file, guild_id) == '[200]':

        query = ({ "guild-id": f"{guild_id}" })

        # should return a dict
        guild_info = collection_file.find_one(query)

        return guild_info
    else:
        return '[404]'

# returns only the IDs for announcement channels
# all other info is unnecessary for the intended use.
def get_announcement_channels(collection_file):

    # returns a regular array of nums
    channels = collection_file.distinct("announcement-channel")

    return channels

def set_new_strategy(collection_file, strategy_object, guild_id):

    # To update the strategies list simply grab the existing array. Append the new strategy to the end, then replace the entire list.

    query = { "guild-id": f"{guild_id}" }
    document = collection_file.find_one(query)

    # returns an existing object
    strategies = document['strategies'] # type: ignore

    # dont ask me how this works lmao
    keys = list(strategy_object.keys())
    entry_name = keys[0]
    strategies[f"{entry_name}"] = strategy_object[f"{entry_name}"]
    update = { "$set": {"strategies": strategies} }

    res = collection_file.update_one(query, update)

    if res.modified_count == 1:
        print(res)

        response = "[201]"
        return response
    else:
        response = "[400]"
        return response

