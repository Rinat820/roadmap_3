from abc import ABC

class BaseDAO(ABC):
    def __init__(self, conn):
        self.conn = conn