# Standard library imports
import json
import re
import logging
import urllib.parse
import random
import requests
import hashlib

# Third-party imports
from openai import OpenAI

# Django imports
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.db.models import Count, Avg
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

# Local app imports
from .models import (
    User,
    GeneratedRecipe,
    Recipe,
    SavedRecipe,
    SharedRecipe,
    RecipeRating,
    UserActivity,
)
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
from .forms import RecipeCommentForm


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

        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not email:
            errors["email"] = "Email is required."
        elif not re.match(email_pattern, email):
            errors["email"] = "Please enter a valid email address."
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

        num_recipes = max(1, min(num_recipes, 6))

        generated_titles = set()
        recipes = []

        attempts_limit = num_recipes * 3
        attempts = 0

        while len(recipes) < num_recipes and attempts < attempts_limit:
            attempts += 1

            prompt = build_prompt(ingredients, selected_filters, generated_titles)

            recipe_list, raw_text = call_groq(prompt)

            if not recipe_list:
                logging.warning(
                    f"Skipping iteration {attempts + 1} due to bad response."
                )
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

        if request.user.is_authenticated:
            try:
                GeneratedRecipe.objects.create(
                    user=request.user,
                    title=recipe["title"],
                    ingredients=recipe["ingredients"],
                    instructions=recipe["instructions"],
                    tags=selected_tag_keys,
                    image_url=image_url,
                    hash=recipe_hash,
                )
            except Exception as e:
                logging.error(f"Error saving GeneratedRecipe: {e}", exc_info=True)

            recipe["hash"] = recipe_hash
            recipe["image_url"] = image_url
            recipe["filters"] = selected_filters

            recipes.append(recipe)

        # If no recipes generated, set recipes to None to show error alert on frontend
        if not recipes:
            recipes = None
        else:
            # Log activity for generated recipes
            if request.user.is_authenticated:
                UserActivity.objects.create(
                    user=request.user,
                    action="generated",
                    details=f"{len(recipes)} recipes",
                )

    # AJAX response for fetch()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            if recipes:
                html = render_to_string(
                    "recipes/_recipe_results.html", {"recipes": recipes}, request=request
                )
            else:
                html = error_html
            return JsonResponse({"html": html})
        except Exception as e:
            logging.error(f"Error rendering AJAX response: {e}", exc_info=True)
            return JsonResponse({"html": error_html, "error": str(e)}, status=500)

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
        "Only include ingredients that make sense together — skip anything that doesn't fit naturally (unless preferences say otherwise). "
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


def shared(request):
    shared_recipes_qs = SharedRecipe.objects.all()

    # Always annotate with num_ratings (total votes)
    shared_recipes_qs = shared_recipes_qs.annotate(num_ratings=Count("ratings"))

    # Search
    q = request.GET.get("q", "").strip()
    if q:
        shared_recipes_qs = shared_recipes_qs.filter(recipe__title__icontains=q)

    # Sort
    sort = request.GET.get("sort", "popular")
    if sort == "newest":
        shared_recipes_qs = shared_recipes_qs.order_by("-recipe__created_at")
    elif sort == "oldest":
        shared_recipes_qs = shared_recipes_qs.order_by("recipe__created_at")
    elif sort == "popular":
        shared_recipes_qs = shared_recipes_qs.annotate(
            avg_rating=Avg("ratings__rating")
        ).order_by("-num_ratings", "-avg_rating", "-shared_at")
    elif sort == "top_rated":
        MIN_VOTES = 2  # Only show recipes with at least 2 votes
        shared_recipes_qs = (
            shared_recipes_qs.annotate(
                avg_rating=Avg("ratings__rating"),
                vote_count=Count("ratings"),
            )
            .filter(vote_count__gte=MIN_VOTES)
            .order_by("-avg_rating", "-vote_count", "-shared_at")
        )
    else:
        shared_recipes_qs = shared_recipes_qs.order_by("-shared_at")

    # Convert to list for Python-side filtering
    shared_recipes = list(shared_recipes_qs)

    # Filter by tag (Python-side filtering)
    active_filters = request.GET.getlist("filter")
    if active_filters:
        shared_recipes = [
            sr
            for sr in shared_recipes
            if all(f in (sr.recipe.tags or []) for f in active_filters)
        ]

    # Pagination
    page = request.GET.get("page", 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    ITEMS_PER_PAGE = 12
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    has_more = end_idx < len(shared_recipes)
    current_page_recipes = shared_recipes[start_idx:end_idx]

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "recipes/partials/_shared_recipe_cards.html",
            {"shared_recipes": current_page_recipes},
            request=request,
        )
        return JsonResponse({"html": html, "has_more": has_more})

    return render(
        request,
        "recipes/shared.html",
        {
            "shared_recipes": current_page_recipes,
            "active_filters": active_filters,
            "sort": sort,
            "TAGS": TAGS,
            "has_more": has_more,
        },
    )


def about(request):
    return render(request, "recipes/about.html")


@login_required
def saved(request):
    saved_recipes_qs = SavedRecipe.objects.filter(user=request.user)

    # Search
    q = request.GET.get("q", "").strip()
    if q:
        saved_recipes_qs = saved_recipes_qs.filter(recipe__title__icontains=q)

    # Sort
    sort = request.GET.get("sort", "liked")
    if sort == "newest":
        saved_recipes_qs = saved_recipes_qs.order_by("-recipe__created_at")
    elif sort == "oldest":
        saved_recipes_qs = saved_recipes_qs.order_by("recipe__created_at")
    else:  # Default: most recently saved
        saved_recipes_qs = saved_recipes_qs.order_by("-saved_at")

    # Convert to list for Python-side filtering
    saved_recipes = list(saved_recipes_qs)

    # Filter by tag (Python-side filtering)
    active_filters = request.GET.getlist("filter")
    if active_filters:
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

    current_page_recipes = saved_recipes[start_idx:end_idx]

    # Collect recipe IDs for current page
    current_recipe_ids = [sr.recipe.id for sr in current_page_recipes]

    # Query average ratings for these recipes across their shared versions
    avg_ratings_qs = (
        Recipe.objects.filter(id__in=current_recipe_ids)
        .annotate(avg_rating=Avg("shared_versions__ratings__rating"))
        .values_list("id", "avg_rating")
    )
    avg_rating_dict = {recipe_id: (avg or 0) for recipe_id, avg in avg_ratings_qs}

    # Query vote counts for these recipes across their shared versions
    vote_counts_qs = (
        Recipe.objects.filter(id__in=current_recipe_ids)
        .annotate(vote_count=Count("shared_versions__ratings"))
        .values_list("id", "vote_count")
    )
    vote_count_dict = {recipe_id: (count or 0) for recipe_id, count in vote_counts_qs}

    shared_recipe_ids = set(SharedRecipe.objects.values_list("recipe_id", flat=True))

    # AJAX request returns partial HTML
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "recipes/partials/_saved_recipe_cards.html",
            {
                "saved_recipes": current_page_recipes,
                "shared_recipe_ids": shared_recipe_ids,
                "avg_rating_dict": avg_rating_dict,
                "vote_count_dict": vote_count_dict,
            },
            request=request,
        )
        return JsonResponse({"html": html, "has_more": has_more})

    # Full page render
    return render(
        request,
        "recipes/saved.html",
        {
            "saved_recipes": current_page_recipes,
            "active_filters": active_filters,
            "sort": sort,
            "TAGS": TAGS,
            "shared_recipe_ids": shared_recipe_ids,
            "avg_rating_dict": avg_rating_dict,
            "vote_count_dict": vote_count_dict,
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
    recipe_hash = request.POST.get("recipe_hash")

    if not recipe_hash:
        return JsonResponse(
            {"status": "error", "message": "No recipe hash provided."}, status=400
        )

    recipe_hash.strip()

    # Try to find a GeneratedRecipe for this user and hash
    gen_recipe = GeneratedRecipe.objects.filter(
        hash=recipe_hash, user=request.user
    ).first()
    recipe = None
    if gen_recipe:
        # Try to find an identical recipe already in Recipe
        recipe = Recipe.objects.filter(hash=recipe_hash).first()
        if not recipe:
            # Download image
            image_file = None
            if gen_recipe.image_url:
                try:
                    response = requests.get(gen_recipe.image_url, timeout=5)
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
    else:
        # Try to find an existing Recipe with this hash
        recipe = Recipe.objects.filter(hash=recipe_hash).first()
        if not recipe:
            return JsonResponse(
                {"status": "error", "message": "Recipe not found."}, status=404
            )

    # Save the recipe for the user (won't duplicate due to `unique_together`)
    try:
        saved, created = SavedRecipe.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            return JsonResponse(
                {"status": "exists", "message": "Recipe already saved."}
            )
        # Log activity for saving recipe
        UserActivity.objects.create(
            user=request.user, action="saved", details=recipe.title
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "saved", "message": "Recipe saved successfully."})


@require_POST
@login_required
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
        recipe_title = saved_recipe.recipe.title
        saved_recipe.delete()
        # Log activity for unsaving recipe
        UserActivity.objects.create(
            user=request.user, action="unsaved", details=recipe_title
        )
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

    # Tag label resolution
    tag_key_to_label = {v: k for k, v in TAGS.items()}
    tag_labels = [
        tag_key_to_label.get(tag)
        for tag in (recipe.tags or [])
        if tag in tag_key_to_label
    ]

    shared_recipe = SharedRecipe.objects.filter(recipe__hash=recipe.hash).first()
    saved_recipe = SavedRecipe.objects.filter(
        recipe__hash=recipe.hash, user=request.user
    ).first()

    # Check if the recipe is shared by the current user
    is_shared_by_user = SharedRecipe.objects.filter(
        recipe=recipe, author=request.user
    ).exists()

    # Check if the recipe is shared by any user
    is_shared_by_anyone = SharedRecipe.objects.filter(recipe=recipe).exists()

    # Ratings setup
    average_rating = None
    total_votes = 0
    user_rating = None

    if shared_recipe:
        rating_data = shared_recipe.ratings.aggregate(
            avg=Avg("rating"), count=Count("rating")
        )
        average_rating = round(rating_data["avg"], 1) if rating_data["avg"] else None
        total_votes = rating_data["count"] or 0

        # Correctly get current user's rating using 'rater' field
        user_rating_obj = shared_recipe.ratings.filter(rater=request.user).first()
        if user_rating_obj:
            user_rating = user_rating_obj.rating

    # --- Comments logic ---
    comment_form = None
    comments = []
    if shared_recipe:
        if request.method == "POST":
            comment_form = RecipeCommentForm(request.POST, request.FILES)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.author = request.user
                comment.recipe = shared_recipe
                comment.save()
                # Log activity for commenting
                UserActivity.objects.create(
                    user=request.user, action="commented", details=f"{recipe.title}: {comment.text[:50]}"
                )
                return redirect("recipe_details", recipe_id=recipe.id)
        else:
            comment_form = RecipeCommentForm()
        comments = shared_recipe.comments.select_related('author').order_by('-created_at')

    return render(
        request,
        "recipes/recipe_details.html",
        {
            "recipe": recipe,
            "tag_labels": tag_labels,
            "shared_recipe": shared_recipe,
            "saved_recipe": saved_recipe,
            "average_rating": average_rating,
            "total_votes": total_votes,
            "user_rating": user_rating,
            "is_shared_by_user": is_shared_by_user,
            "is_shared_by_anyone": is_shared_by_anyone,
            "comment_form": comment_form,
            "comments": comments,
        },
    )


@require_POST
@login_required
def share_recipe(request):
    recipe_id = request.POST.get("recipe_id")
    if not recipe_id:
        messages.error(request, "No recipe specified to share.")
        return redirect("index")

    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Check if already shared by any user
    already_shared = SharedRecipe.objects.filter(recipe=recipe).exists()
    if already_shared:
        messages.error(request, "This recipe has already been shared by another user.")
        return redirect("recipe_details", recipe_id=recipe.id)

    # Check if already shared by this user (extra safety check)
    already_shared_by_user = SharedRecipe.objects.filter(
        recipe=recipe, author=request.user
    ).exists()
    if already_shared_by_user:
        messages.info(request, "You have already shared this recipe.")
        return redirect("recipe_details", recipe_id=recipe.id)

    SharedRecipe.objects.create(recipe=recipe, author=request.user)
    # Log activity for sharing recipe
    UserActivity.objects.create(
        user=request.user, action="shared", details=recipe.title
    )
    messages.success(request, "Recipe shared with the community!")
    return redirect("recipe_details", recipe_id=recipe.id)


@login_required
def rate_recipe(request, shared_recipe_id):
    if request.method == "POST":
        shared_recipe = get_object_or_404(SharedRecipe, id=shared_recipe_id)
        rating_value = request.POST.get("rating")

        try:
            rating_value = int(rating_value)
            if 1 <= rating_value <= 5:
                # Prevent duplicate ratings by the same user
                rating_obj, created = RecipeRating.objects.get_or_create(
                    rater=request.user,
                    recipe=shared_recipe,
                    defaults={"rating": rating_value},
                )
                if not created:
                    rating_obj.rating = rating_value
                    rating_obj.save()

                # Log activity for rating
                UserActivity.objects.create(
                    user=request.user, action="rated", details=f"{shared_recipe.recipe.title}: {rating_value} stars"
                )

                # For AJAX requests, return JSON
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    avg = shared_recipe.ratings.aggregate(
                        avg=Avg("rating"), count=Count("rating")
                    )
                    return JsonResponse(
                        {
                            "success": True,
                            "user_rating": rating_value,
                            "average_rating": (
                                round(avg["avg"], 1) if avg["avg"] else None
                            ),
                            "total_votes": avg["count"] or 0,
                        }
                    )
        except (ValueError, TypeError):
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": "Invalid rating value."}, status=400
                )
            pass  # Invalid input silently ignored or handle with a message

    # Fallback for non-AJAX POSTs
    return redirect("recipe_details", recipe_id=shared_recipe.recipe.id)


@require_POST
@login_required
def remove_shared_recipe(request):
    recipe_id = request.POST.get("recipe_id")
    if not recipe_id:
        messages.error(request, "No recipe specified to remove from shared.")
        return redirect("index")

    recipe = get_object_or_404(Recipe, id=recipe_id)
    shared_recipe = SharedRecipe.objects.filter(
        recipe=recipe, author=request.user
    ).first()

    if not shared_recipe:
        messages.error(request, "You haven't shared this recipe.")
        return redirect("recipe_details", recipe_id=recipe.id)

    shared_recipe.delete()
    # Log activity for unsharing recipe
    UserActivity.objects.create(
        user=request.user, action="unshared", details=recipe.title
    )
    messages.success(request, "Recipe removed from shared recipes!")
    return redirect("recipe_details", recipe_id=recipe.id)


class EmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]


class DevPasswordChangeForm(DjangoPasswordChangeForm):
    def clean_new_password1(self):
        password1 = self.cleaned_data.get("new_password1")
        # Skip all validators in development mode
        return password1


@login_required
def profile(request):
    user = request.user
    email_form = EmailForm(instance=user)
    password_form = DevPasswordChangeForm(user)
    email_success = password_success = False

    # Get the latest 20 activities for the user
    activities = UserActivity.objects.filter(user=user).order_by("-timestamp")[:20]

    if request.method == "POST":
        if "email_submit" in request.POST:
            email_form = EmailForm(request.POST, instance=user)
            if email_form.is_valid():
                email_form.save()
                email_success = True
                # Log activity for email change
                UserActivity.objects.create(
                    user=request.user, action="email_changed", details=f"Changed email to {user.email}"
                )
        elif "password_submit" in request.POST:
            password_form = DevPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                password_success = True
                # Log activity for password change
                UserActivity.objects.create(
                    user=request.user, action="password_changed", details="Password changed"
                )

    return render(
        request,
        "recipes/profile.html",
        {
            "user": user,
            "email_form": email_form,
            "password_form": password_form,
            "email_success": email_success,
            "password_success": password_success,
            "activities": activities,
        },
    )
