# For more info visit -> https://github.com/google-gemini/cookbook/blob/main/examples/Talk_to_documents_with_embeddings.ipynb

import textwrap
from google import genai
from google.genai import types
import numpy as np
import pandas as pd
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import find_dotenv, load_dotenv
import os, json


dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
MONGODB = os.getenv('MongoDB')
GEMINI = os.getenv("GeminiAPI")
uri = f'mongodb+srv://rftestingnyc_db_user:{MONGODB}@cluster.4n8bbif.mongodb.net/?appName=Cluster'
mongo_client = MongoClient(uri, server_api=ServerApi('1'))

try:
    mongo_client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

database = mongo_client["static-info"]
collection = database['vector-embeddings']

EMBEDDING_MODEL_ID = "gemini-embedding-001"
client = genai.Client(api_key=f"{GEMINI}")


mycwd = os.getcwd()
with open(f'{mycwd}/rag_src.json', 'r') as file:
    data = json.load(file)

documents = []
for entry in data:
    documents.append(entry)

df = pd.DataFrame(documents)
df.columns = ['Title', 'Text']

def embed_fn(title, text):
  response = client.models.embed_content(
        model=EMBEDDING_MODEL_ID,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="retrieval_document",
            title=title
        )
    )

  return response.embeddings[0].values

df['Embeddings'] = df.apply(lambda row: embed_fn(row['Title'], row['Text']), axis=1)

# to be sent to mongoDB
embeddings_dict = df.to_dict(orient="dict")

# mongoDB only takes dicts with string key values, this converts all keys and nested keys into strings.
embeddings_package = {}
for col_name, row_data in embeddings_dict.items():
    embeddings_package[str(col_name)] = {str(k): v for k, v in row_data.items()}


# quickly deletes previous sync and inserts a new one.
collection.delete_many({})
collection.insert_one(embeddings_package)
