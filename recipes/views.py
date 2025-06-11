from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import JsonResponse, HttpResponseRedirect
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from .models import User, SavedRecipe, SharedRecipe, RecipeComment, RecipeVote
from openai import OpenAI
from .constants import (
    GROQ_API_KEY,
    GROQ_URL,
    GROQ_MODEL,
    INGREDIENTS,
    FILTER_PHRASES,
    EXAMPLE_RECIPE,
)
import json
import re
import logging
import urllib.parse
import random
import requests
import hashlib
import ast


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirmation = request.POST.get("confirmation", "")

        errors = {}

        if not username:
            errors["username"] = "Username is required."
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Username already taken."

        if not email:
            errors["email"] = "Email is required."
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Email already in use."

        if not password:
            errors["password"] = "Password is required."
        if not confirmation:
            errors["confirmation"] = "Please confirm your password."
        elif password != confirmation:
            errors["confirmation"] = "Passwords must match."

        if errors:
            return render(
                request,
                "recipes/register.html",
                {
                    "errors": errors,
                    "values": {
                        "username": username,
                        "email": email,
                    },
                },
            )

        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:
            return render(
                request,
                "recipes/register.html",
                {"errors": {"username": "Username already exists."}},
            )

        login(request, user)
        return redirect("index")

    return render(request, "recipes/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        errors = {}

        if not username:
            errors["username"] = "Username is required."
        if not password:
            errors["password"] = "Password is required."

        if username and password:
            try:
                user_check = User.objects.get(username=username)
                # If user exists, check if password is correct
                authenticated_user = authenticate(
                    request, username=username, password=password
                )
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    return redirect(reverse("index"))
                else:
                    errors["password"] = "Incorrect password."
            except User.DoesNotExist:
                errors["username"] = "This username does not exist."

        # Render login page with field-specific errors
        return render(request, "recipes/login.html", {"errors": errors})

    return render(request, "recipes/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def index(request):
    recipes = None
    filters_selected = {}

    if request.method == "POST":
        ingredients = request.POST.get("ingredients", "").strip()
        print(ingredients)

        if not ingredients:
            return HttpResponseRedirect(reverse("index"))

        # Collect filters
        filters_selected = {f: (f in request.POST) for f in FILTER_PHRASES.keys()}
        print(filters_selected)

        # Number of recipes to generate
        num_recipes = request.POST.get("num_recipes", "").strip()

        prompt = f"I have these ingredients: {ingredients}. Give me {num_recipes} recipes I can make using the ingredients I have. "

        selected_filters = [
            FILTER_PHRASES[name]
            for name, selected in filters_selected.items()
            if selected and name in FILTER_PHRASES
        ]
        print(selected_filters)
        if selected_filters:
            prompt += f"Also apply these preferences: {', '.join(selected_filters)}. "

        prompt += (
            f"Your response should be ONLY a single valid JSON array containing exactly {num_recipes} objects. "
            "Do not include any extra text, notes, or formatting outside the array (this part is super important, make sure to follow it). "
            f"Here is one full example: {json.dumps(EXAMPLE_RECIPE)} ..."
            'Each object MUST have exactly three keys: "title", "ingredients", and "instructions". '
            '"title" must be a string. '
            '"ingredients" must be a JSON array of strings, where each string describes the amount and item clearly. '
            '"instructions" must be a JSON array of strings. '
            "Each ingredient should be portioned for one person. "
            "Find the best possible combinations. If some ingredients don't fit or don't make sense you can skip them. "
            "Each instruction step should be written in full, descriptive sentences. "
            "Avoid vague phrases like 'cook the bacon' — explain how to cook it, how long, what to look for, etc. "
            "Do not repeat the same type of recipe (e.g. 3 sandwiches). Use a variety of dishes. "
        )

        print(prompt)

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

                # Generate and attach hash to recipe
                recipe["hash"] = generate_recipe_hash(recipe)

                recipe["filters"] = selected_filters

    # AJAX response (for JavaScript fetch)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "recipes/_recipe_results.html", {"recipes": recipes}, request=request
        )
        return JsonResponse({"html": html})

    return render(
        request,
        "recipes/index.html",
        {"recipes": recipes},
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


def trending(request):
    pass


def about(request):
    pass


def saved(request):
    pass


def generate_recipe_hash(recipe):
    raw_data = json.dumps(
        {
            "title": recipe["title"],
            "ingredients": recipe["ingredients"],
            "instructions": recipe["instructions"],
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw_data.encode()).hexdigest()


@login_required
@require_POST
def save_recipe(request):
    title = request.POST.get("title")
    image_url = request.POST.get("image_url")
    recipe_hash = request.POST.get("hash")

    try:
        ingredients = ast.literal_eval(request.POST.get("ingredients", "[]"))
        instructions = ast.literal_eval(request.POST.get("instructions", "[]"))
        tags = ast.literal_eval(request.POST.get("tags", "[]"))

        if not isinstance(ingredients, list):
            raise ValueError("Ingredients must be a list")
        if not isinstance(instructions, list):
            raise ValueError("Instructions must be a list")
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list")

    except (ValueError, SyntaxError) as e:
        ingredients = []
        instructions = []
        tags = []

    if not all([title, recipe_hash, ingredients, instructions]):
        return JsonResponse(
            {"status": "error", "message": "Missing required fields"}, status=400
        )

    # Check for duplicate
    if SavedRecipe.objects.filter(user=request.user, hash=recipe_hash).exists():
        return JsonResponse(
            {
                "status": "exists",
                "message": "Recipe already saved.",
                "hash": recipe_hash,
            }
        )

    # Download and save the image file
    image_file = None
    if image_url:
        try:
            response = requests.get(image_url, timeout=5)
            response.raise_for_status()
            image_file = ContentFile(response.content, name=f"{recipe_hash}.jpg")
        except requests.RequestException:
            pass

    # Save recipe
    with transaction.atomic():
        SavedRecipe.objects.create(
            user=request.user,
            title=title,
            ingredients=ingredients,
            instructions=instructions,
            tags=tags,
            hash=recipe_hash,
            image=image_file,
        )

    return JsonResponse(
        {
            "status": "saved",
            "message": "Recipe saved successfully.",
            "hash": recipe_hash,
        }
    )


@login_required
@require_POST
def remove_saved_recipe(request):
    recipe_hash = request.POST.get("hash")
    if not recipe_hash:
        return JsonResponse(
            {"status": "error", "message": "Missing recipe hash"}, status=400
        )

    try:
        saved_recipe = SavedRecipe.objects.get(user=request.user, hash=recipe_hash)
        saved_recipe.delete()
        return JsonResponse(
            {"status": "removed", "message": "Recipe removed from saved"}
        )
    except SavedRecipe.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Recipe not found"}, status=404
        )
