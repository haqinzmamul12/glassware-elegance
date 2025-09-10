from backend.semantic_search import semantic_match
from backend.lexical_search import lexical_match

def hybrid_search(query, k=3, threshold=0.6):
    semantic_results = semantic_match(query, k=k, threshold=threshold)
    lexical_results = lexical_match(query, k=k)

    # Merge & deduplicate by 'id'
    seen = set()
    unique_results = []

    for doc in lexical_results + semantic_results:
        unique_id = doc.metadata.get("id") or doc.metadata.get("name")
        if unique_id and unique_id not in seen:
            seen.add(unique_id)
            unique_results.append(doc.metadata)

    return unique_results



# if __name__=='__main__':
#     result =hybrid_search("Crystal Water Goblet", 2)
#     print("Final Result")
#     print(result)
