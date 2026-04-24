# query.py

from Dataset import connect_weaviate, get_embeddings, search_query
from Ai_Services import generate_answer
import warnings
warnings.filterwarnings("ignore")
print("Initializing AI components... Please wait.")
client = connect_weaviate()
embeddings = get_embeddings()
print("System Ready!\n")

print("Type 'quit' or 'exit' to stop.")
chat_history = []
while True:
    query = input("\n👤 You: ")
    if query.lower() in ['quit', 'exit', 'q']:
        print("Goodbye!")
        break
    if not query.strip():
        continue
        
    results = search_query(query, client, embeddings)

    print("\n🤖 AI:")
    answer = generate_answer(query, results, chat_history)
    print(answer)
    
    chat_history.append({"role": "user", "content": query})
    chat_history.append({"role": "assistant", "content": answer})
    
    print("-" * 50)

client.close()