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
from dotenv import load_dotenv
load_dotenv()

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.getenv("WEAVIATE_CLUSTER_URL"),
    auth_credentials=Auth.api_key(os.getenv("WEAVIATE_API_KEY")),
    skip_init_checks=True
)

# ------------------ RESET COLLECTION (OPTIONAL) ------------------
if client.collections.exists("CompanyDocs"):
    print("⚠️ Deleting old collection...")
    client.collections.delete("CompanyDocs")

# ------------------ CREATE COLLECTION ------------------
client.collections.create(
    name="CompanyDocs",
    vectorizer_config=Configure.Vectorizer.none(),  # manual embeddings
    properties=[
        Property(name="course_domain", data_type=DataType.TEXT),
        Property(name="trainer_domain", data_type=DataType.TEXT),
        Property(name="content_type", data_type=DataType.TEXT),# ✅ domain
    ]
)

# print("✅ Collection created")

# ------------------ EMBEDDING MODEL ------------------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ------------------ LOAD PDFs ------------------
DATA_PATH = "D:\Data science notes\Projects\Quest\Backend\Services\QuestRagData"
documents = []
doc_map = {}

def get_type(filename):
    name = filename.lower()
    if "policies" in name:
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

        if doc_type not in doc_map:
            doc_map[doc_type] = []

        for doc in docs:
            doc.metadata["source"] = file
            doc.metadata["type"] = doc_type

            documents.append(doc)
            doc_map[doc_type].append(doc)

print(f"📄 Loaded {len(documents)} documents")

# ------------------ SPLIT ------------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80
)

chunks = splitter.split_documents(documents)
print(f"✂️ Created {len(chunks)} chunks")

# ------------------ METADATA EXTRACTION ------------------
def extract_metadata(text, filename):
    text_lower = text.lower()
    filename_lower = filename.lower()

    metadata = {
        "content_type": "general",
        "course_domain": "general",
        "trainer_domain": "none"
    }

    # ---------------- TYPE ----------------
    if "name:" in text_lower and "qualification" in text_lower:
        metadata["content_type"] = "trainer"

    # ---------------- TRAINER DOMAIN ----------------
    if "domain:" in text_lower:
        if "data science" in text_lower:
            metadata["trainer_domain"] = "Data Science"
        elif "analytics" in text_lower:
            metadata["trainer_domain"] = "Data Analytics"
        elif "django" in text_lower:
            metadata["trainer_domain"] = "Django"

    # ---------------- COURSE DOMAIN ----------------
    import re
    if re.search(r'\b(data science|machine learning|ai|ml)\b', text_lower):
        metadata["course_domain"] = "Data Science"

    elif any(x in text_lower for x in ["analytics", "tableau"]):
        metadata["course_domain"] = "Data Analytics"

    elif any(x in text_lower for x in ["react", "html", "css", "javascript"]):
        metadata["course_domain"] = "Web Development"

    # ---------------- FALLBACK (filename) ----------------
    if metadata["course_domain"] == "general":
        if "data_science" in filename_lower:
            metadata["course_domain"] = "Data Science"
        elif "analytics" in filename_lower:
            metadata["course_domain"] = "Data Analytics"
        elif "python" in filename_lower:
            metadata["course_domain"] = "Python Full Stack"
        elif "java" in filename_lower:
            metadata["course_domain"] = "Java Full Stack"

    return metadata
# ------------------ STORE IN WEAVIATE ------------------
collection = client.collections.get("CompanyDocs")

for chunk in chunks:
    vector = embeddings.embed_query(chunk.page_content)

    filename = chunk.metadata.get("source", "")
    file_type = chunk.metadata.get("type", "")

    extra_meta = extract_metadata(chunk.page_content, filename)

    collection.data.insert(
    properties={
        "text": chunk.page_content,
        "source": filename,
        "page": chunk.metadata.get("page", 0),

        "file_type": file_type,

        "content_type": extra_meta["content_type"],
        "course_domain": extra_meta["course_domain"],
        "trainer_domain": extra_meta["trainer_domain"]
    },
    vector=vector
)

print("🚀 Data uploaded successfully!")

# ------------------ VERIFY ------------------
response = collection.query.fetch_objects(limit=5)

for obj in response.objects:
    print(obj.properties)

# ------------------ CLOSE ------------------
client.close()