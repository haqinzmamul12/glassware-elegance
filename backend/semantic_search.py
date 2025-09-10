from backend.vectorstore import create_vectorstore

vectorstore =create_vectorstore()
def semantic_match(query, k=3, threshold=0.6):
    results_with_scores = vectorstore.similarity_search_with_score(query, k=k)
    
    filtered = []
    for doc, score in results_with_scores:
        if score <= threshold:
            filtered.append(doc)
    
    return filtered
