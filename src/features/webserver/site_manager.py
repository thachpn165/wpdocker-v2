from abc import ABC, abstractmethod

class WebserverSiteManager(ABC):
    @abstractmethod
    def create_website(self, domain: str, **kwargs) -> bool:
        pass

    @abstractmethod
    def delete_website(self, domain: str) -> bool:
        pass

    @abstractmethod
    def ensure_site_config(self, domain: str) -> bool:
        pass

    # Có thể bổ sung các method khác nếu cần 