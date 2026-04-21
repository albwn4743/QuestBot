# dataset.py

from langchain_community.embeddings import HuggingFaceEmbeddings
import weaviate
from weaviate.classes.query import Filter
from weaviate.classes.init import Auth
# -------- CONNECT --------
def connect_weaviate():
    return weaviate.connect_to_weaviate_cloud(
    cluster_url="url",
    auth_credentials=Auth.api_key("kiki"),
    skip_init_checks=True
    # print("Connected to:", WEAVIATE_URL)
)

# -------- EMBEDDING --------
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

# -------- GET COLLECTION --------
def get_collection(client):
    return client.collections.get("CompanyDocs")

# -------- SEARCH --------
def search_query(query, client, embeddings):
    query_vector = embeddings.embed_query(query)

    collection = client.collections.get("CompanyDocs")

    filters = None
    query_lower = query.lower()

    # 🔥 Better domain detection
    if any(x in query_lower for x in ["data science", "machine learning", "ai"]):
        filters = Filter.by_property("domain").equal("Data Science")

    # 🔥 Type detection
    if "trainer" in query_lower:
        trainer_filter = Filter.by_property("type").equal("trainer")

        if filters:
            filters = filters & trainer_filter
        else:
            filters = trainer_filter

    # 🔥 Query
    response = collection.query.near_vector(
        near_vector=query_vector,
        limit=5,
        filters=filters,
        return_metadata=["distance"]
    )

    results = []

    for obj in response.objects:
        if obj.metadata.distance < 0.5:
            results.append(obj.properties.get("text", ""))
    if not results:
        for obj in response.objects:
            results.append(obj.properties.get("text", ""))

    return results