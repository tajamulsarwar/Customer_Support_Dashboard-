import os
from pathlib import Path

# Keep the download inside this folder instead of the global ~/.cache/kagglehub
os.environ["KAGGLEHUB_CACHE"] = str(Path(__file__).parent)

import kagglehub

# Download latest version
path = kagglehub.dataset_download("bitext/training-dataset-for-chatbotsvirtual-assistants")

print("Path to dataset files:", path)
