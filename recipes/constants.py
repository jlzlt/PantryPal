import json
from pathlib import Path


GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama3-70b-8192"

FILTER_NAMES = (
    "vegetarian",
    "quick",
    "gluten_free",
    "dairy_free",
    "low_carb",
    "vegan",
    "keto",
    "paleo",
)

INGREDIENTS = []
try:
    path = Path(__file__).resolve().parent / "ingredients.json"
    with open(path, "r") as f:
        INGREDIENTS = json.load(f)
except Exception as e:
    print("Error loading ingredient list:", e)
