from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import JsonResponse, HttpResponseRedirect
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.paginator import Paginator
from .models import User, GeneratedRecipe, Recipe, SavedRecipe, SharedRecipe
from openai import OpenAI
from .constants import (
    GROQ_API_KEY,
    GROQ_URL,
    GROQ_MODEL,
    INGREDIENTS,
    FILTER_PHRASES,
    EXAMPLE_RECIPE,
    TAGS,
    DEFAULT_IMAGE_URL,
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
    error_html = '<div class="alert alert-danger">Failed to load recipes. Please try again.</div>'

    if request.method == "POST":
        ingredients = request.POST.get("ingredients", "").strip()
        print(f"Ingredients: {ingredients}")

        # Collect filters
        filters_selected = [name for name in FILTER_PHRASES if name in request.POST]
        print(f"Selected filters: {filters_selected}")

        # User-facing tags
        selected_tag_keys = [key for key in TAGS.values() if key in request.POST]

        # Map selected filters to their descriptive phrases for AI prompt
        selected_filters = [FILTER_PHRASES[name] for name in filters_selected]

        # Number of recipes to generate
        try:
            num_recipes = int(request.POST.get("num_recipes", 1))
        except (ValueError, TypeError):
            num_recipes = 1

        generated_titles = set()
        recipes = []

        attempts_limit = num_recipes * 3
        attempts = 0

        while len(recipes) < num_recipes and attempts < attempts_limit:
            attempts += 1

            prompt = build_prompt(ingredients, selected_filters, generated_titles)

            recipe_list, raw_text = call_groq(prompt)

            if not recipe_list:
                logging.warning(f"Skipping iteration {i + 1} due to bad response.")
                continue

            recipe = recipe_list[0]

            title = recipe.get("title", "").strip()
            if not title or title in generated_titles:
                logging.warning(f"Duplicate or missing title: {title}. Skipping.")
                continue

            generated_titles.add(title)

            # Generate image URL
            prompt_img = f"A high quality photo of {recipe['title']} dish, appetizing and well-lit"
            image_url = generate_image(prompt_img) or DEFAULT_IMAGE_URL

            recipe_hash = generate_recipe_hash(recipe)

            # Save to GeneratedRecipe model
            GeneratedRecipe.objects.create(
                user=request.user,
                title=recipe["title"],
                ingredients=recipe["ingredients"],
                instructions=recipe["instructions"],
                tags=selected_tag_keys,
                image_url=image_url,
                hash=recipe_hash,
            )

            recipe["hash"] = recipe_hash
            recipe["image_url"] = image_url
            recipe["filters"] = selected_filters

            recipes.append(recipe)

        # If no recipes generated, set recipes to None to show error alert on frontend
        if not recipes:
            recipes = None

    # AJAX response for fetch()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if recipes:
            html = render_to_string(
                "recipes/_recipe_results.html", {"recipes": recipes}, request=request
            )
        else:
            html = error_html
        return JsonResponse({"html": html})

    return render(
        request,
        "recipes/index.html",
        {"recipes": recipes},
    )


def build_prompt(ingredients, selected_filters, generated_titles):
    prompt = (
        "You are a professional recipe generator. "
        "Your only output should be a valid JSON object representing one complete recipe, where you should mimic the format and clarity of top food websites. "
        "Follow precise formatting and cooking standards. "
    )

    if ingredients:
        prompt += f"I have these ingredients: {ingredients}. Give me 1 recipe I can make using them. "
    else:
        prompt += f"Generate 1 random recipe. "

    if selected_filters:
        prompt += f"Apply these preferences: {', '.join(selected_filters)}. "

    if generated_titles:
        prompt += (
            "Exclude these recipes: "
            + ", ".join(f'"{t}"' for t in generated_titles)
            + ". "
        )

    prompt += (
        "Your response should be ONLY a single valid JSON object representing one complete recipe. "
        "Do not include any extra text, comments, explanations, or formatting outside the JSON object. "
        f"Here is one example recipe object (for format reference only, do not duplicate): {json.dumps(EXAMPLE_RECIPE)} "
        'The object MUST contain exactly three keys: "title", "ingredients", and "instructions". '
        '"title" must be a string. '
        '"ingredients" must be a JSON array of strings — each string must clearly state the exact amount, unit, and name of the ingredient, formatted like a professional recipe (e.g., "1 tablespoon olive oil", "100g boneless chicken breast"). '
        '"instructions" must be a JSON array of strings — each string must be a full, descriptive step in the cooking process. '
        'Steps should include time, temperature, textures, or other sensory cues when applicable (e.g., "Sauté the onions in olive oil over medium heat for 5–7 minutes, until soft and golden."). '
        "Ingredients should be portioned for one person. "
        "Only include ingredients that make sense together — skip anything that doesn’t fit naturally (unless preferences say otherwise). "
        "Avoid vague instructions like 'cook the pasta' — always specify how to cook it, how long, and what to look for. "
    )

    return prompt


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
            parsed = json.loads(json_text)
            if isinstance(parsed, dict):
                return [parsed], response_text
            elif isinstance(parsed, list) and all(isinstance(r, dict) for r in parsed):
                return parsed, response_text
            else:
                logging.warning(
                    f"Parsed content is not a dict or list of dicts (attempt {attempt + 1})"
                )
                continue
        except Exception as e:
            logging.warning(f"JSON parsing failed on attempt {attempt + 1}: {e}")
            continue

    # If all attempts fail
    logging.error(
        f"All retries failed. Last raw response: {last_response_text[:200]}..."
    )
    return None, last_response_text


def extract_json(text):
    """
    Extract the first top-level JSON object or array from text, even with nested structures.
    Removes markdown code fences if present.
    """
    # Clean up markdown formatting
    text = re.sub(r"^```(?:json)?", "", text).strip("` \n")

    # Look for the first '{' or '['
    brace_start = text.find("{")
    bracket_start = text.find("[")

    if brace_start == -1 and bracket_start == -1:
        return text  # fallback

    # Use whichever comes first
    if brace_start == -1 or (bracket_start != -1 and bracket_start < brace_start):
        start = bracket_start
        open_char, close_char = "[", "]"
    else:
        start = brace_start
        open_char, close_char = "{", "}"

    # Balance the brackets/braces
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_char:
            depth += 1
        elif text[i] == close_char:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return text  # fallback if unbalanced


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


@login_required
def saved(request):
    saved_recipes_qs = SavedRecipe.objects.filter(user=request.user)

    # Search
    q = request.GET.get("q", "").strip()
    if q:
        saved_recipes_qs = saved_recipes_qs.filter(recipe__title__icontains=q)

    # Sort (apply to QuerySet before Python-side filtering)
    sort = request.GET.get("sort", "liked")
    if sort == "newest":
        saved_recipes_qs = saved_recipes_qs.order_by("-recipe__created_at")
    elif sort == "oldest":
        saved_recipes_qs = saved_recipes_qs.order_by("recipe__created_at")
    else:  # Default: 'liked' (most recently saved)
        saved_recipes_qs = saved_recipes_qs.order_by("-saved_at")

    # Convert to list and filter by tag if needed
    saved_recipes = list(saved_recipes_qs)

    # Filter by tag (Python-side filtering)
    active_filters = request.GET.getlist("filter")  # Get all 'filter' parameters
    if active_filters:
        # Check if all active_filters are present in recipe.tags
        saved_recipes = [
            sr
            for sr in saved_recipes
            if all(f in (sr.recipe.tags or []) for f in active_filters)
        ]

    # Pagination for infinite scroll
    page = request.GET.get("page", 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    items_per_page = 12
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    has_more = end_idx < len(saved_recipes)

    # Get the current page of recipes
    current_page_recipes = saved_recipes[start_idx:end_idx]

    shared_recipe_ids = set(SharedRecipe.objects.values_list("recipe_id", flat=True))

    # If it's an AJAX request, return only the recipe cards HTML
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "recipes/partials/_saved_recipe_cards.html",
            {
                "saved_recipes": current_page_recipes,
                "shared_recipe_ids": shared_recipe_ids,
            },
            request=request,
        )
        return JsonResponse({"html": html, "has_more": has_more})

    return render(
        request,
        "recipes/saved.html",
        {
            "saved_recipes": current_page_recipes,
            "active_filters": active_filters,
            "sort": sort,
            "TAGS": TAGS,
            "shared_recipe_ids": shared_recipe_ids,
            "has_more": has_more,
        },
    )


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
    recipe_hash = request.POST.get("recipe_hash").strip()

    if not recipe_hash:
        return JsonResponse(
            {"status": "error", "message": "No recipe hash provided."}, status=400
        )

    gen_recipe = get_object_or_404(GeneratedRecipe, hash=recipe_hash, user=request.user)

    try:
        with transaction.atomic():
            # Check if an identical recipe already exists
            recipe = Recipe.objects.filter(hash=recipe_hash).first()

            if not recipe:
                # Download image
                image_file = None
                if gen_recipe.image_url:
                    try:
                        response = requests.get(gen_recipe.image_url, timeout=10)
                        response.raise_for_status()
                        image_file = ContentFile(
                            response.content, name=f"{gen_recipe.hash}.jpg"
                        )
                    except requests.RequestException:
                        print("Could not download image.")

                recipe = Recipe.objects.create(
                    title=gen_recipe.title,
                    ingredients=gen_recipe.ingredients,
                    instructions=gen_recipe.instructions,
                    tags=gen_recipe.tags,
                    image=image_file,
                    hash=recipe_hash,
                )

            # Save the recipe for the user (won't duplicate due to `unique_together`)
            saved, created = SavedRecipe.objects.get_or_create(
                user=request.user, recipe=recipe
            )

            if not created:
                return JsonResponse(
                    {"status": "exists", "message": "Recipe already saved."}
                )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "saved", "message": "Recipe saved successfully."})


@login_required
@require_POST
def remove_saved_recipe(request):
    recipe_hash = request.POST.get("recipe_hash")
    if not recipe_hash:
        return JsonResponse(
            {"status": "error", "message": "Missing recipe hash."}, status=400
        )

    try:
        saved_recipe = SavedRecipe.objects.get(
            user=request.user, recipe__hash=recipe_hash
        )
        saved_recipe.delete()
        return JsonResponse(
            {"status": "removed", "message": "Recipe removed from saved"}
        )
    except SavedRecipe.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Saved recipe not found"}, status=404
        )


@login_required
def recipe_details(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Reverse-map tag keys to user-facing names
    tag_key_to_label = {v: k for k, v in TAGS.items()}
    tag_labels = []

    for tag in recipe.tags:  # adjust based on how you store tags
        if tag in tag_key_to_label:
            tag_labels.append(tag_key_to_label[tag])

    shared_recipe = SharedRecipe.objects.filter(recipe__hash=recipe.hash).first()

    saved_recipe = SavedRecipe.objects.filter(recipe__hash=recipe.hash).first()

    return render(
        request,
        "recipes/recipe_details.html",
        {
            "recipe": recipe,
            "tag_labels": tag_labels,
            "shared_recipe": shared_recipe,
            "saved_recipe": saved_recipe,
        },
    )
