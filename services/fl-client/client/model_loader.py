# Added on gemini recomm

import sys
import os

# This allows this file to "see" the model.py you found
sys.path.append(os.path.abspath("../../inference/engine"))
from model import DiagnosticModel

class OnnxModelLoader:
    def __init__(self, model_path):
        self.model_path = model_path

    def load(self):
        # Uses the DiagnosticModel class from your inference engine
        return DiagnosticModel(self.model_path)
