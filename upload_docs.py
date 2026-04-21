import os
import warnings
warnings.filterwarnings("ignore")

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
# ------------------ CONNECT ------------------
client = weaviate.connect_to_weaviate_cloud(
    cluster_url="url",
    auth_credentials=Auth.api_key("kiki"),
    skip_init_checks=True
    # print("Connected to:", WEAVIATE_URL)
)

# ------------------ CHECK IF DATA EXISTS ------------------
if client.collections.exists("CompanyDocs"):
    print("⚠️ Data already exists. Skipping upload.")
    client.close()
    exit()

# ------------------ CREATE COLLECTION ------------------
client.collections.create(
    name="CompanyDocs",
    vectorizer_config=Configure.Vectorizer.none(),  # ✅ manual embeddings
    properties=[
        Property(name="text", data_type=DataType.TEXT),
        Property(name="source", data_type=DataType.TEXT),
        Property(name="page", data_type=DataType.INT),
        Property(name="type", data_type=DataType.TEXT),  # 🔥 important
    ]
)

print("Collection created ✅")

# ------------------ EMBEDDING MODEL ------------------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ------------------ LOAD PDFs ------------------
DATA_PATH = "QuestRagData"
documents = []

def get_type(filename):
    name = filename.lower()
    if "policy" in name:
        return "policy"
    elif "trainer" in name:
        return "trainer"
    else:
        return "course"

for file in os.listdir(DATA_PATH):
    if file.endswith(".pdf"):
        file_path = os.path.join(DATA_PATH, file)
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        doc_type = get_type(file)

        for doc in docs:
            doc.metadata["source"] = file
            doc.metadata["type"] = doc_type

        documents.extend(docs)

print(f"Loaded {len(documents)} documents")

# ------------------ SPLIT ------------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80
)

chunks = splitter.split_documents(documents)
print(f"Created {len(chunks)} chunks")

# ////////////////adding metadata////////////////////////////
def extract_metadata(text):
    text_lower = text.lower()

    metadata = {
        "type": "general",
        "domain": "general"
    }

    # TYPE detection
    if "name:" in text_lower and "qualification" in text_lower:
        metadata["type"] = "trainer"

    # DOMAIN detection (stronger)
    if "data science" in text_lower:
        metadata["domain"] = "Data Science"
    elif "analytics" in text_lower:
        metadata["domain"] = "Data Analytics"
    elif "embedded" in text_lower:
        metadata["domain"] = "Embedded"
    elif "django" in text_lower:
        metadata["domain"] = "Django"
    elif "react" in text_lower or "html" in text_lower:
        metadata["domain"] = "Web Development"

    return metadata
# ------------------ STORE IN WEAVIATE ------------------
collection = client.collections.get("CompanyDocs")

for chunk in chunks:
    vector = embeddings.embed_query(chunk.page_content)

    extra_meta = extract_metadata(chunk.page_content)

    collection.data.insert(
        properties={
            "text": chunk.page_content,
            "source": chunk.metadata.get("source", ""),
            "page": chunk.metadata.get("page", 0),
            "type": extra_meta["type"],
            "domain": extra_meta["domain"]
        },
        vector=vector
    )
print("🚀 Data uploaded successfully!")
print(client.collections.list_all())
response = client.collections.get("CompanyDocs").query.fetch_objects(limit=5)

# for obj in response.objects:
#     print(obj.properties)
# print("Connected to:", WEAVIATE_URL)
# ------------------ CLOSE ------------------
client.close()