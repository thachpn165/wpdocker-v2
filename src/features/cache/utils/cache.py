VALID_CACHE_TYPES = [
    "fastcgi-cache",
    "wp-super-cache",
    "w3-total-cache",
    "wp-fastest-cache",
    "no-cache"
]

def validate_cache_type(cache_type: str) -> bool:
    """
    Check if the cache_type is valid.
    """
    return cache_type in VALID_CACHE_TYPES 