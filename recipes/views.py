import requests
from django.shortcuts import render
from .forms import IngredientForm
from openai import OpenAI
from .constants import GROQ_API_KEY, GROQ_URL, GROQ_MODEL, FILTER_NAMES
import json


def index(request):
    recipes = None
    filters_selected = {}
    image_urls = []

    if request.method == "POST":
        ingredients = request.POST.get("ingredients", "").strip()
        difficulty = request.POST.get("difficulty", "").strip()
        time_limit = request.POST.get("time", "").strip()

        # Collect filters
        filters_selected = {f: (f in request.POST) for f in FILTER_NAMES}

        prompt = f"I have these ingredients: {ingredients}. "
        prompt += "I want recipes"

        selected_filters = [
            name.replace("_", " ")
            for name, selected in filters_selected.items()
            if selected
        ]
        if selected_filters:
            prompt += f" with the following filters: {', '.join(selected_filters)}."

        example_recipe = [
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

        prompt += (
            "Give me 5 recipes I can make using the ingredients I have. "
            "Respond ONLY with a single valid JSON array containing exactly 5 objects. "
            'Each object MUST have exactly three keys: "title", "ingredients", and "instructions". '
            '"title" must be a string. '
            "\"ingredients\" must be a JSON array of strings, where each string describes the amount and item clearly, e.g., '2 slices of bread', '1/4 cup chopped onion', '3 lettuce leaves'. "
            '"instructions" must be a JSON array of strings. '
            "Each ingredient should be portioned for one person. "
            "Each instruction step should be written in full, descriptive sentences for beginners. "
            "Avoid vague phrases like 'cook the bacon' — explain how to cook it, how long, what to look for, etc. "
            "Do not repeat the same type of recipe (e.g. 3 sandwiches). Use a variety of dishes. "
            "Respond ONLY with valid JSON. Do not include any extra text, notes, or formatting outside the array. "
            f"Here is one full example: {json.dumps(example_recipe)} ..."
        )

        if difficulty:
            prompt += f" Difficulty level should be {difficulty}."

        if time_limit:
            prompt += f" The cooking time should be less than {time_limit} minutes."

        # Call Groq
        client = OpenAI(base_url=GROQ_URL, api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )

        suggestions_text = response.choices[0].message.content

        print(suggestions_text)

        if not suggestions_text or len(suggestions_text.strip()) < 10:
            recipes = [
                {"title": "AI response", "description": "No valid response received."}
            ]
        else:
            try:
                # Parse the JSON array from the AI response
                recipes = json.loads(
                    suggestions_text.replace("'", '"')
                )  # replace single quotes if AI uses them
                if not isinstance(recipes, list) or not all(
                    isinstance(r, dict) for r in recipes
                ):
                    raise ValueError("Not a valid list of recipe dicts")
            except Exception:
                # Fallback: If parsing fails, put the whole text as one recipe
                recipes = [{"title": "AI response", "description": suggestions_text}]

    return render(
        request,
        "recipes/index.html",
        {
            "recipes": recipes,
            "filters_selected": filters_selected,
        },
    )
