# --- MongoDB Helper Functions ---

def get_last_timestamp(collection_file):

    # Retrieving first document in collection
    # Should reference the timestamp document
    doc = collection_file.find_one()
    time = doc['timestamp']

    return time