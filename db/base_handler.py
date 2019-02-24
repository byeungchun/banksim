from abc import ABC, abstractmethod

class DBHandler(ABC):
    @abstractmethod
    def insert_items(self):
        pass

    @abstractmethod
    def find_items(self):
        pass

    @abstractmethod
    def find_item(self):
        pass

    @abstractmethod
    def delete_items(self):
        pass

    @abstractmethod
    def update_items(self):
        pass

    @abstractmethod
    def aggregate(self):
        pass
