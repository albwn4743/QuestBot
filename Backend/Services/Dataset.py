# dataset.py
from langchain_community.embeddings import HuggingFaceEmbeddings
import weaviate
from weaviate.classes.query import Filter
from weaviate.classes.init import Auth
# -------- CONNECT --------
import os
from dotenv import load_dotenv
load_dotenv()

def connect_weaviate():
    return weaviate.connect_to_weaviate_cloud(
    cluster_url=os.getenv("WEAVIATE_CLUSTER_URL"),
    auth_credentials=Auth.api_key(os.getenv("WEAVIATE_API_KEY")),
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
    query_lower = query.lower()

    collection = client.collections.get("CompanyDocs")

    DOMAIN_MAP = {
        "Data Science": ["data science", "machine learning", "ai", "ml", "artificial intelligence", "deep learning"],
        "Data Analytics": ["analytics", "data analysis", "tableau", "power bi", "data visualization"],
        "Python Full Stack": ["python", "mern", "fullstack", "full stack", "django", "web development", "frontend", "backend"],
        "Java Full Stack": ["java", "spring", "spring boot", "springboot", "j2ee", "java fullstack"]
    }

    filters = None

    import re
    # 🔹 DOMAIN detection
    for domain, keywords in DOMAIN_MAP.items():
        pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
        if re.search(pattern, query_lower):
            filters = Filter.by_property("course_domain").equal(domain)
            break

    # 🔹 TYPE detection (IMPORTANT)
    trainer_keywords = ["trainer", "trainers", "tutor", "tutors", "instructor", "instructors", "faculty", "teacher", "teachers"]
    trainer_pattern = r'\b(' + '|'.join(trainer_keywords) + r')\b'
    
    if re.search(trainer_pattern, query_lower):
        trainer_filter = Filter.by_property("content_type").equal("trainer")
        filters = trainer_filter if not filters else filters & trainer_filter
    else:
        not_trainer = Filter.by_property("content_type").not_equal("trainer")
        filters = not_trainer if not filters else filters & not_trainer

    policy_keywords = ["policy", "policies", "rule", "rules", "guideline", "guidelines", "regulation", "regulations", "terms", "conditions", "hr", "leave", "holiday"]
    policy_pattern = r'\b(' + '|'.join(policy_keywords) + r')\b'
    if re.search(policy_pattern, query_lower):
        policy_filter = Filter.by_property("file_type").equal("policy")
        filters = policy_filter if not filters else filters & policy_filter

    # 🔍 Vector search
    response = collection.query.near_vector(
        near_vector=query_vector,
        limit=8,  # slightly more for filtering
        filters=filters,
        return_metadata=["distance"]
    )

    results = []

    for obj in response.objects:
        distance = obj.metadata.distance

        # 🔥 STRICT FILTER (IMPORTANT)
        if distance <= 0.85:
            results.append({
                "text": obj.properties.get("text", ""),
                "source": obj.properties.get("source", ""),
                "type": obj.properties.get("file_type", ""),
                "course_domain": obj.properties.get("course_domain", ""),
                "trainer_domain": obj.properties.get("trainer_domain", ""),
                "distance": distance
            })

    # 🔁 FALLBACK (if nothing good found)
    if not results:
        for obj in response.objects[:3]:  # top 3 only
            results.append({
                "text": obj.properties.get("text", ""),
                "source": obj.properties.get("source", ""),
                "type": obj.properties.get("file_type", ""),
                "domain": obj.properties.get("domain", ""),
                "distance": obj.metadata.distance
            })

    # 🔝 Sort results (best first)
    results = sorted(results, key=lambda x: x["distance"])

    return results