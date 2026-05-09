import os
from enum import Enum

API_BASE_URL = os.getenv("UIBENCHKIT_API_URL", "http://localhost:5000")

class Method(str, Enum):
    """Generation method."""
    dcgen = 'dcgen'
    direct = 'direct'
    latcoder = 'latcoder'
    uicopilot = 'uicopilot'
    layoutcoder = 'layoutcoder'

class Dataset(str, Enum):
    """Available datasets."""
    design2code = 'design2code'
    dcgen = 'dcgen'

class ModelFamily(str, Enum):
    """Model families."""
    gemini = 'gemini'
    gpt4 = 'gpt4'
    claude = 'claude'
    qwen = 'qwen'

# Model versions for each family (for reference/validation)
MODEL_VERSIONS = {
    "gemini": [
        "gemini-2.0-flash", "gemini-2.0-flash-exp", "gemini-1.5-flash",
        "gemini-1.5-flash-8b", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-exp-1206"
    ],
    "gpt4": [
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-4-vision-preview",
        "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13",
        "o1", "o1-mini", "o1-preview"
    ],
    "claude": [
        "claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620", "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
    ],
    "qwen": [
        "qwen2.5-vl-72b-instruct", "qwen2.5-vl-7b-instruct", "qwen2-vl-72b-instruct",
        "qwen2-vl-7b-instruct", "qwen-vl-max", "qwen-vl-plus"
    ]
}

# Backwards compatibility alias
Subset = Method
