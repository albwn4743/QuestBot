import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
import warnings
warnings.filterwarnings("ignore")
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings


client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://gpms6mjcsvuhv9bclfw5cg.c0.asia-southeast1.gcp.weaviate.cloud",
    auth_credentials=Auth.api_key("NmZqQTJYcVRyQ0MyRTJjSV8zdXZZdTlLWG0rMkQ4UjhzdzlVZG5yeW42RFQvcE81SEs4RFo1M2JmYmxRPV92MjAw"),  # ✅ secure
    skip_init_checks=True
)
# print(client.is_ready())

if client.collections.exists("CompanyDocs"):
    client.collections.delete("CompanyDocs")
client.collections.create(
    name="CompanyDocs",
    vectorizer_config=Configure.Vectorizer.none(),  # manual embeddings
    properties=[
        Property(name="text", data_type=DataType.TEXT),
        Property(name="source", data_type=DataType.TEXT),
        Property(name="file_type", data_type=DataType.TEXT),
        Property(name='course_domain',data_type=DataType.TEXT)# ✅ domain
    ]
)
documents = []
datapath="QuestRagData/Data_Science_5pages.pdf"
# if file.endswith(".pdf"):
loader=PyPDFLoader(datapath)
docs = loader.load()

for doc in docs:
    doc.metadata["source"] = datapath
    documents.append(doc)
# print(f"✅ Loaded {len(documents)} documents")
# print(documents[0])

splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
chunks = splitter.split_documents(documents)

embeddings= HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

collection = client.collections.get("CompanyDocs")
for chunk in chunks:
    text = chunk.page_content
    source = chunk.metadata["source"].lower()
    file_type = "pdf"
    course_domain = "data science" # ✅ domain

    vector = embeddings.embed_query(text)

    collection.data.insert(
        vector=vector,
        properties={
            "text": text,
            "source": source,
            "file_type": file_type,
            "course_domain": course_domain
        }
    )
# print("✅ Documents embedded and stored in Weaviate")

# response = collection.query.fetch_objects(limit=5)
# for obj in response.objects:
#     print(obj.properties)

query = "data science course"
query_vector = embeddings.embed_query(query)

response = collection.query.near_vector(
    near_vector=query_vector,
    limit=5,
    return_metadata=["distance"]
)

for obj in response.objects:
    print(obj.properties)