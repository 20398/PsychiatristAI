eximport os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

# Load document
import os

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = r"C:\Users\parth\OneDrive\Desktop\workspace\agentic_rag\data"
all_docs = []

for filename in os.listdir(DATA_PATH):
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(DATA_PATH, filename))
        documents = loader.load()
        all_docs.extend(documents)
 
print(f"Loaded {len(all_docs)} documents")
# Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)
docs = splitter.split_documents(all_docs)

# Create embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# Create vector store
db = FAISS.from_documents(docs, embeddings)

# Save locally
db.save_local("vectorstore")

print("Ingestion complete.")