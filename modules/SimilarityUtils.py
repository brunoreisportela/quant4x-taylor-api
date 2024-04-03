import re
from decimal import Decimal

class SimilarityUtils:

    def jaccard_similarity(self, text1, text2):
        # Preprocess the text: lowercase and split into words
        words1 = set(re.split(r'\s+', text1.lower()))
        words2 = set(re.split(r'\s+', text2.lower()))

        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1) + len(words2) - intersection
        similarity = intersection / union

        return similarity
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)