from Levenshtein import distance

def find_matches_preprocessed(query: str, catalog_lower: list[str], max_distance: int = 1) -> list[int]:
    return [i for i, item in enumerate(catalog_lower)
            if distance(query.lower(), item) <= max_distance]

def find_similar_queries(input_query, catalog):
    """
    Returns a list of indices from the catalog that are within 
    1 edit distance (0 or 1) of the input_query.
    
    Complexity: O(N * L) where N is catalog size and L is string length.
    """
    match_indices = []
    
    for i, candidate in enumerate(catalog):
        n, m = len(input_query), len(candidate)
        
        # Optimization 1: Length Filter
        # 1 edit distance is impossible if length differs by more than 1
        if abs(n - m) > 1:
            continue
        
        # Optimization 2: Exact Match (Distance 0)
        if input_query == candidate:
            match_indices.append(i)
            continue
        
        # Check for Distance 1
        if is_one_edit_away(input_query, candidate):
            match_indices.append(i)
            
    return match_indices

def is_one_edit_away(s1, s2):
    """
    Helper function to check if strings are exactly 1 edit apart.
    Assumes len(s1) and len(s2) differ by at most 1.
    """
    # Ensure s1 is the shorter (or equal) string to simplify logic
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    
    n, m = len(s1), len(s2)
    
    for i in range(n):
        if s1[i] != s2[i]:
            # If lengths are equal, it must be a Substitution
            # The rest of the strings must match exactly
            if n == m:
                return s1[i+1:] == s2[i+1:]
            
            # If lengths are different, it must be an Insertion/Deletion
            # The rest of s1 must match s2 shifted by 1
            else:
                return s1[i:] == s2[i+1:]
    
    # If we finish the loop without returning, it means the only 
    # difference is the last character of the longer string.
    return True


# ---------------------------------------------------------
# DEMO WITH CHASE REWARDS CONTEXT
# ---------------------------------------------------------
if __name__ == "__main__":
    # Catalog of typical Chase reward keywords + some noise
    cache_catalog = [
        "travel", "points", "cashback", "dining", "groceries",
        "free", "cars", "gap", "lyft", "united", "prime", "offer", "lyft offers", "prime offers"
    ]

    # Dangerous inputs (from our previous discussion)
    test_queries = [
        "fee",      # Should match "free" (Dangerous)
        "care",     # Should match "cars" (Confusing)
        "gas",      # Should match "gap" (Cross-category)
        "lift",     # Should match "lyft" (Brand typo - Good match)
        "point",    # Should match "points" (Plural - Good match)
        "crime",
    ]

    print(f"{'Input':<10} | {'Matched Indices':<15} | {'Matched Values'}")
    print("-" * 60)
    for q in test_queries:
        indices = find_similar_queries(q, cache_catalog)
        # Lookup values for display
        values = [cache_catalog[i] for i in indices]
        print(f"{q:<10} | {str(indices):<15} | {values}")

        indices = find_matches_preprocessed(q, cache_catalog)
        values = [cache_catalog[i] for i in indices]
        print(f"{q:<10} | {str(indices):<15} | {values}")