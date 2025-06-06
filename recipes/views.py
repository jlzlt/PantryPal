import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.template.loader import render_to_string
from .forms import IngredientForm
from openai import OpenAI
from .constants import (
    GROQ_API_KEY,
    GROQ_URL,
    GROQ_MODEL,
    FILTER_NAMES,
    INGREDIENTS,
    FILTER_PHRASES,
    EXAMPLE_RECIPE,
)
import json
import re
import logging
import uuid
import os
import urllib.parse
import random

API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
API_TOKEN = "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"


def index(request):
    recipes = None
    filters_selected = {}
    image_urls = []

    if request.method == "POST":
        ingredients = request.POST.get("ingredients", "").strip()
        print(ingredients)

        # Collect filters
        filters_selected = {f: (f in request.POST) for f in FILTER_NAMES}

        prompt = f"I have these ingredients: {ingredients}. "

        selected_filters = [
            FILTER_PHRASES[name]
            for name, selected in filters_selected.items()
            if selected and name in FILTER_PHRASES
        ]
        if selected_filters:
            prompt += f" Apply these preferences: {', '.join(selected_filters)}. "
            print(selected_filters)

        prompt += (
            "Give me 5 recipes I can make using the ingredients I have. "
            "Your response should be ONLY a single valid JSON array containing exactly 5 objects. "
            "Do not include any extra text, notes, or formatting outside the array (this part is super important, make sure to follow it). "
            f"Here is one full example: {json.dumps(EXAMPLE_RECIPE)} ..."
            'Each object MUST have exactly three keys: "title", "ingredients", and "instructions". '
            '"title" must be a string. '
            '"ingredients" must be a JSON array of strings, where each string describes the amount and item clearly. '
            '"instructions" must be a JSON array of strings. '
            "Each ingredient should be portioned for one person. "
            "Find the best possible combinations. If some ingredients don't fit or don't make sense you can skip them. "
            "Each instruction step should be written in full, descriptive sentences for beginners. "
            "Avoid vague phrases like 'cook the bacon' — explain how to cook it, how long, what to look for, etc. "
            "Do not repeat the same type of recipe (e.g. 3 sandwiches). Use a variety of dishes. "
        )

        recipes, raw_text = call_groq(prompt)

        if not recipes:
            recipes = [
                {
                    "title": "Error generating recipes",
                    "description": raw_text or "No valid response received.",
                }
            ]
        else:
            for recipe in recipes:
                prompt_img = f"A high quality photo of {recipe['title']} dish, appetizing and well-lit"
                image_url = generate_image(prompt_img)

                # Assign Pollinations image URL (no need to download or save)
                recipe["image_url"] = image_url or "/static/default_recipe_img.png"

    # AJAX response (for JavaScript fetch)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("recipes/_recipe_results.html", {"recipes": recipes})
        return JsonResponse({"html": html})

    return render(
        request,
        "recipes/index.html",
        {
            "recipes": recipes,
        },
    )


def call_groq(prompt, retries=5):
    client = OpenAI(base_url=GROQ_URL, api_key=GROQ_API_KEY)
    last_response_text = ""

    for attempt in range(retries + 1):
        logging.info(f"Groq attempt {attempt + 1}/{retries + 1}")
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                max_tokens=1024,
            )
        except Exception as e:
            logging.error(f"Groq API error on attempt {attempt + 1}: {e}")
            continue

        response_text = response.choices[0].message.content.strip()
        last_response_text = response_text

        logging.info(f"Raw response text (attempt {attempt + 1}): {response_text}")

        json_text = extract_json(response_text)

        try:
            parsed = json.loads(json_text.replace("'", '"'))
            if isinstance(parsed, list) and all(isinstance(r, dict) for r in parsed):
                return parsed, response_text
            else:
                logging.warning(
                    f"Parsed content is not a list of dicts (attempt {attempt + 1})"
                )
                continue
        except Exception as e:
            logging.warning(f"JSON parsing failed on attempt {attempt + 1}: {e}")
            continue

    # If all attempts fail
    logging.error("All retries failed. Returning last raw response.")
    return None, last_response_text


def extract_json(text):
    """
    Extract the first top-level JSON array from text, even with nested dicts/lists.
    Falls back to returning raw text if no valid-looking JSON is found.
    """
    # Remove code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip("` \n")

    # Try to find the first [ and balance brackets to extract the full array
    start = text.find("[")
    if start == -1:
        return text  # No JSON array found

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return text  # fallback if brackets aren't balanced


@require_GET
def autocomplete_ingredients(request):
    query = request.GET.get("query", "").lower()
    matches = [i for i in INGREDIENTS if i.startswith(query)][:5]
    return JsonResponse(matches, safe=False)


def generate_image(prompt: str) -> str:
    """
    Generates a Pollinations.AI image URL from the given prompt.
    Returns the image URL string.
    """
    # URL-encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)

    # Optional: Use a random seed to avoid repeated identical images
    seed = random.randint(1, 99999)

    # Construct Pollinations image URL
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&seed={seed}&nologo=true"

    return image_url
