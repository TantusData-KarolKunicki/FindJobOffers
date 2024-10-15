import threading

from .strategies.linkedin_strategy_api import LinkedinApi


class LinkedinSingleton:
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with cls._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = super(LinkedinSingleton, cls).__new__(cls)
        return cls._instance

    def __init__(self, email, password, strategy_class=LinkedinApi):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self.email = email
            self.password = password
            self.strategy = strategy_class(email, password)
            self.lock = threading.Lock()

    def get_person_info(self, link):
        with self.lock:
            return self.strategy.get_person_info(link)
