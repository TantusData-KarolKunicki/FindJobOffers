from abc import ABC, abstractmethod


class LinkedinStrategy(ABC):
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.api = self.login()

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def get_person_info(self, link):
        pass
