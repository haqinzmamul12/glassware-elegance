# backend/bm25_retriever.py

import json
from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document

def load_bm25_documents(path="products.json"):
    with open(path, 'r') as f:
        products = json.load(f)

    docs = []
    for product in products:
        content = f"{product['name']} - {product['description']} - {product['category']}"
        docs.append(Document(page_content=content.lower(), metadata=product))
    
    return docs

def get_bm25_retriever(k):
    docs = load_bm25_documents()
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = k  # adjust as needed
    return retriever

def lexical_match(query, k =3):
    bm25 =get_bm25_retriever(k)
    bm25_results = bm25.get_relevant_documents(query)
    return bm25_results
