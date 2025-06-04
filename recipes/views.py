import requests
from django.shortcuts import render
from .forms import IngredientForm
from openai import OpenAI


GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def index(request):
    suggestions = None
    image_urls = []

    if request.method == "POST":
        form = IngredientForm(request.POST)
        if form.is_valid():
            ingredients = form.cleaned_data['ingredients']
            prompt = f"I have {ingredients}. Give me 5 simple recipes I can make."

            # Call Groq
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=False,
                stop=None,
            )

            suggestions = response.choices[0].message.content

    else:
        form = IngredientForm()

    return render(request, "recipes/index.html", {
        "form": form,
        "suggestions": suggestions,
    })