from src.features.cache.constants import CACHE_TYPES

def validate_cache_type(cache_type: str) -> bool:
    """
    Check if the cache_type is valid.
    """
    return cache_type in CACHE_TYPES 