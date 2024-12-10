import threading

class Counter:
    def __init__(self, initial_value=0):
        self.lock = threading.Lock()
        self.initial_count = self.count = initial_value

    def increment(self):
        with self.lock:
            self.count -= 1

    def get_value(self):
        return self.count

    def get_initial_count(self):
        return self.initial_count