import re
from typing import List

def chunk_transcript(text: str, max_chars: int = 8000) -> List[str]:
    """
    Splits the cleaned transcript text into chunks of maximum max_chars characters.
    
    Tries to split at sentence boundaries (. ! ?) to avoid cutting mid-sentence.
    If a sentence/block itself exceeds max_chars (e.g. no punctuation in auto-generated transcripts),
    it splits at word boundaries (spaces).
    """
    if not text:
        return []
        
    # Split text using lookbehinds for . ! ? followed by a space
    # This keeps the punctuation marks attached to the end of sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_len = len(sentence)
        
        # Case 1: The single sentence itself is larger than our limit (e.g. a long video with no punctuation)
        if sentence_len > max_chars:
            # Save any accumulated text in current_chunk first
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # Force-split the long sentence by words to stay under the limit
            words = sentence.split(" ")
            sub_chunk = []
            sub_len = 0
            
            for word in words:
                word_len = len(word)
                # Account for space if not the first word in sub_chunk
                space_cost = 1 if sub_chunk else 0
                
                if sub_len + space_cost + word_len > max_chars:
                    if sub_chunk:
                        chunks.append(" ".join(sub_chunk))
                    sub_chunk = [word]
                    sub_len = word_len
                else:
                    sub_chunk.append(word)
                    sub_len += space_cost + word_len
                    
            if sub_chunk:
                current_chunk = sub_chunk
                current_length = sub_len
                
        # Case 2: Normal sentence that fits within the limit
        else:
            space_cost = 1 if current_chunk else 0
            # If adding this sentence would exceed the limit, save current_chunk and start new
            if current_length + space_cost + sentence_len > max_chars:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_len
            else:
                current_chunk.append(sentence)
                current_length += space_cost + sentence_len
                
    # Append the final chunk if there's anything left
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks
