# query.py

from Dataset import connect_weaviate, get_embeddings, search_query
import warnings
warnings.filterwarnings("ignore")
client = connect_weaviate()
embeddings = get_embeddings()

query = input("what is data Science?")

results = search_query(query, client, embeddings)

print("\n--- ANSWER ---\n")

for r in results:
    print(r)
    print("\n")

client.close()