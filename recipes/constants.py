import json
from pathlib import Path


GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama3-70b-8192"

FILTER_NAMES = (
    "use_all_ingredients",
    "under_30_minutes",
    "easy_only",
    "kid_friendly",
    "metric_system",
    "no_cook_only",
    "minimize_prep_time",
    "breakfast",
    "lunch",
    "dinner",
    "basic_practical",
    "creative_surprising",
)

FILTER_PHRASES = {
    "use_all_ingredients": "Use all ingredients",
    "under_30_minutes": "Under 30 minutes",
    "easy_only": "Easy only",
    "kid_friendly": "Kid friendly",
    "metric_system": "Use metric units",
    "no_cook_only": "No-cook only (salads, smoothies, etc.)",
    "minimize_prep_time": "Minimize prep time",
    "breakfast": "Make it suitable for breakfast",
    "lunch": "Make it suitable for lunch",
    "dinner": "Make it suitable for dinner",
    "basic_practical": "Basic and practical",
    "creative_surprising": "Creative or surprising",
}

INGREDIENTS = []
try:
    path = Path(__file__).resolve().parent / "ingredients.json"
    with open(path, "r") as f:
        INGREDIENTS = json.load(f)
except Exception as e:
    print("Error loading ingredient list:", e)

EXAMPLE_RECIPE = [
    {
        "title": "Grilled Cheese Sandwich",
        "ingredients": [
            "2 slices of white bread",
            "2 slices of cheddar cheese",
            "1 tablespoon of butter",
        ],
        "instructions": [
            "Spread the butter on one side of each slice of bread.",
            "Place one slice, buttered side down, in a non-stick skillet over medium heat.",
            "Add the cheese on top of the bread in the skillet.",
            "Place the second slice of bread on top, buttered side up.",
            "Cook for 2-3 minutes, until the bottom is golden brown.",
            "Flip and cook the other side until the bread is toasted and the cheese is fully melted.",
        ],
    }
]
