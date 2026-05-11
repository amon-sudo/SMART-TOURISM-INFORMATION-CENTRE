from abc import ABC, abstractmethod

class UserInterface(ABC):
    @abstractmethod
    def register_user(self, username: str, password: str) -> None:
        pass

    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def get_user_details(self, username: str) -> dict:
        pass

    
    