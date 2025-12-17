
import re
from typing import List, Dict

def normalize_url(u):
    # Normalize: lower case and strip trailing slash
    return u.rstrip('/').lower()

def clean_url(u):
    # Remove trailing punctuation often attached by LLMs
    return re.sub(r'[.,;:!)]+$', '', u)

def validate_urls(text: str, context: List[Dict]) -> str:
    print(f"Text from LLM: {text}")
    
    # 1. Extract valid URLs from context
    valid_urls = set()
    for item in context:
        for key, value in item.items():
            if value and isinstance(value, str):
                # Using the same regex as the app
                found_urls = re.findall(r'https?://[^\s<>"]+', value)
                cleaned = [clean_url(u) for u in found_urls]
                valid_urls.update(cleaned)
    
    # Normalize valid URLs
    normalized_valid_urls = {normalize_url(u) for u in valid_urls}
    print(f"Valid URLs (DB): {normalized_valid_urls}")

    # 2. Extract URLs from LLM response
    response_urls = re.findall(r'https?://[^\s<>"]+', text)
    print(f"Raw URLs from LLM: {response_urls}")

    validated_text = text
    for url in response_urls:
        # Clean & Normalize response URL
        cleaned_url = clean_url(url)
        norm_url = normalize_url(cleaned_url)
        
        print(f"Checking: '{url}' -> Cleaned: '{cleaned_url}' -> Norm: '{norm_url}'")
        
        if norm_url not in normalized_valid_urls:
            print(f"MISMATCH! '{norm_url}' not in {normalized_valid_urls}")
            validated_text = validated_text.replace(url, '[Link not available in database]')
        else:
            print(f"MATCH!")
            
    return validated_text

# Test Case 1: Standard Link
context1 = [{"answer": "Here is the link: https://roadmap.sh/game-developer"}]
text1 = "Here's the roadmap you need: https://roadmap.sh/game-developer"

# Test Case 2: Link with trailing slash
text2 = "Here's the roadmap: https://roadmap.sh/game-developer/"

# Test Case 3: Link inside parentheses (Markdown style)
text3 = "Here is the roadmap (https://roadmap.sh/game-developer)."

print("--- TEST 1 ---")
print(validate_urls(text1, context1))
print("\n--- TEST 2 ---")
print(validate_urls(text2, context1))
print("\n--- TEST 3 ---")
print(validate_urls(text3, context1))
