import os 
import json 
from langchain.vectorstores import FAISS 
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings

from dotenv import load_dotenv 
load_dotenv()
COHERE_API_KEY =os.getenv("COHERE_API_KEY")


# embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# embedding = HuggingFaceEmbeddings(model_name ="intfloat/e5-small-v2")
embedding =CohereEmbeddings(model ="embed-english-light-v3.0", cohere_api_key=COHERE_API_KEY)

def load_product_documents(prod_paths ="products.json"):
    with open(prod_paths, 'r') as f:
        products =json.load(f)

    docs =[] 
    for product in products:
        content =f"{product['name']}. {product['name']} - {product['description']} - {product['category']}"
        metadata = {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "category": product["category"],
            "price": product["price"]
        }

        docs.append(Document(page_content=content.lower(), metadata =metadata))
        print("Documents loaded & added successfully!")

    return docs

def create_vectorstore():
    docs =load_product_documents()
    splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=20)
    chunks = splitter.split_documents(docs)
    #embedding =HuggingFaceBgeEmbeddings("BAAI/bge-large-en-v1.5")
    vector_store =FAISS.from_documents(chunks, embedding)
    print("Vector Store initialised...")
    return vector_store