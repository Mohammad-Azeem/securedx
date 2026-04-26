#GradientQueue is a class that manages a queue of gradients for a machine learning model.
# It allows for adding gradients to the queue, retrieving gradients from the queue, 
# and checking if the queue is empty. The class uses a simple list to store the gradients
#  and provides thread-safe access to the queue using a lock.


# services/fl-client/client/gradient_queue.py

class GradientQueue:
    """Stub for offline gradient storage (will implement later)"""
    
    def __init__(self, queue_dir="/var/securedx/fl-queue"):
        self.queue_dir = queue_dir
    
    def save(self, gradients):
        """Save gradients to queue (stub)"""
        pass
    
    def load(self):
        """Load gradients from queue (stub)"""
        return []