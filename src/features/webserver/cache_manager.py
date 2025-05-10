from abc import ABC, abstractmethod

class BaseCacheManager(ABC):
    @abstractmethod
    def setup_w3_total_cache(self, domain: str) -> bool:
        pass

    @abstractmethod
    def setup_super_cache(self, domain: str) -> bool:
        pass

    @abstractmethod
    def setup_wp_fastest_cache(self, domain: str) -> bool:
        pass

    @abstractmethod
    def setup_no_cache(self, domain: str) -> bool:
        pass

    # Có thể bổ sung thêm các loại cache khác nếu cần 