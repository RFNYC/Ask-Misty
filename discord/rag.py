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

EMBEDDING_MODEL_ID = "gemini-embedding-001"
client = genai.Client(api_key=f"{GEMINI}")
query = "How does the announcement command work?"

uri = f'mongodb+srv://rftestingnyc_db_user:{MONGODB}@cluster.4n8bbif.mongodb.net/?appName=Cluster'
mongo_client = MongoClient(uri, server_api=ServerApi('1'))

try:
    mongo_client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

database = mongo_client["static-info"]
collection = database['vector-embeddings']
mongo_response = collection.find()
temp = []

for document in mongo_response:
    temp.append(document)

embeddings_package = temp[0]
del embeddings_package['_id']

# handling mongoDB embeddings we stored previously:
embeddings_restored = pd.DataFrame(embeddings_package)


print(embeddings_restored)

def find_best_passage(query, dataframe):
  """
  Compute the distances between the query and each document in the dataframe
  using the dot product.
  """
  query_embedding = client.models.embed_content(
      model=EMBEDDING_MODEL_ID,
      contents=query,
      config=types.EmbedContentConfig(
          task_type="retrieval_document",
          )
  )

  dot_products = np.dot(
      np.stack(dataframe['Embeddings']),
      query_embedding.embeddings[0].values # type: ignore
  )
  idx = np.argmax(dot_products)
  return dataframe.iloc[idx]['Text']


def make_prompt(query, relevant_passage):
  escaped = (
      relevant_passage
      .replace("'", "")
      .replace('"', "")
      .replace("\n", " ")
  )
  prompt = textwrap.dedent("""
    You are a helpful and informative discordpy bot that answers questions using text
    from the reference passage included below. Be sure to respond in a
    complete sentence, being comprehensive, including all relevant
    background information.

    However, you are talking to a mostly non-technical audience, so be sure to
    break down complicated concepts and strike a friendly but brief manner. 
    If the passage is irrelevant to the answer, you may ignore it.
                           
    Prioritize helping the user actually **use** a command. Only explain it's usage if asked what it does.

    QUESTION: '{query}'
    PASSAGE: '{relevant_passage}'

    ANSWER:
  """).format(query=query, relevant_passage=escaped)


  return prompt


relevant_content = find_best_passage(query, embeddings_restored)

prompt = make_prompt(query, relevant_content)


MODEL_ID = "gemini-2.5-flash"
answer = client.models.generate_content(
    model=MODEL_ID,
    contents=prompt,
)

print(answer.text)