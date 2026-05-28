import chromadb
from chromadb.utils import embedding_functions
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(
    path=os.getenv("CHROMA_PERSIST_DIR", "../data/chromadb")
)

# Embeddings — still local, free, no change needed
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Get or create collection
collection = chroma_client.get_or_create_collection(
    name="advisor_knowledge",
    embedding_function=embedding_fn
)

# Initialize Groq LLM
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    temperature=0.1,
    max_tokens=1024
)

def ingest_document(text: str, doc_id: str, metadata: dict = {}):
    """Split a document into chunks and store in ChromaDB"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(text)
    collection.upsert(
        documents=chunks,
        ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
        metadatas=[{**metadata, "chunk": i} for i in range(len(chunks))]
    )
    return {"ingested_chunks": len(chunks), "doc_id": doc_id}

def query_rag(question: str, n_results: int = 3) -> str:
    """Retrieve relevant chunks and generate answer using Groq"""

    # Step 1: Retrieve from ChromaDB
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )

    if not results["documents"][0]:
        return "No relevant information found in the knowledge base."

    # Step 2: Build context
    context = "\n\n".join(results["documents"][0])

    # Step 3: Call Groq
    messages = [
        SystemMessage(content="""You are an AI assistant for financial advisors 
at a broker-dealer firm. Use the provided context to answer questions accurately 
and concisely. If the answer is not in the context, say so clearly. 
Always be professional and precise with financial information."""),
        HumanMessage(content=f"""Context:
{context}

Advisor Question: {question}

Answer:""")
    ]

    response = llm.invoke(messages)
    return response.content