# PantryPal

PantryPal is a Django-based web application that allows users to generate AI-powered recipes based on ingredients they already have at home. By combining fast, low-latency responses from large language models via the Groq API and AI-generated images through Pollinations.ai, PantryPal delivers dynamic and personalized recipe suggestions within seconds.

![Screenshot](/recipes/static/recipes/screenshot1.png)

![Screenshot](/recipes/static/recipes/screenshot2.png)

## Installation Guide

Follow these steps to set up and run PasswordManager on your local machine:

### 1.) Prerequisites
Make sure you have the following installed:

• Python 3.10+ (https://www.python.org/downloads/)  
• pip (comes with Python)  
• Git (https://git-scm.com/downloads)  
• Virtual Environment (venv) (optional but recommended)

### 2.) Clone the Repository
Open a terminal and run:  

`git clone https://github.com/jlzlt/PantryPal.git`  
`cd PantryPal`

### 3.) Create a Virtual Environment (Optional, Recommended)
To keep dependencies isolated, create and activate a virtual environment:

Windows:  
`python -m venv venv`  
`venv\Scripts\activate`  

Mac/Linux:  
`python3 -m venv venv`  
`source venv/bin/activate`  

### 4.) Install Dependencies
Install required Python packages:

`pip install -r requirements.txt`

### 5.) Set up the database

`python manage.py migrate`

### 6.) Run the development server

`python manage.py runserver`

## Features

### Ingredient-Based Recipe Generation

- Enter a list of ingredients — from just a couple to a fully stocked pantry. Or leave it empty if you want random suggestions.
- Get up to 6 unique AI-generated recipes per request.
- Apply filters to customize generation (Meal type, time constraints, style, etc).
- Filters are passed as structured instructions to the LLM for precise control.

### Backend Flow

1. Ingredients + filters → structured prompt → sent to Groq (via OpenAI Python library).
2. Response: 1 recipe in JSON format (validated for title, ingredients, instructions).
3. On failure → auto-retry up to limit.
4. Duplicates avoided via Python set of titles that gets updated and passed after every generated recipe.
5. Each valid recipe saved to GeneratedRecipe Django model (includes Pollinations image URL).
6. Images downloaded only when user saves a recipe.

This one-by-one generation pattern reduces AI generated JSON format failures, avoids token limit issues and also increases recipe quality, since LLMs tend to provide a more comprehensive response when you ask for one recipe rather than six at once.

### AI Image Integration

Images are generated via Pollinations.ai, a platform that leverages generative AI models (such as Stable Diffusion, DALL·E, and AudioLDM) to let users create images. It was chosen because it accepts HTTP GET requests with parameters embedded in the URL, allowing the backend to generate images without storing them immediately. The backend creates a prompt, constructs the URL, and sends it to the frontend, which uses it as the image source. The actual image is saved to the server only if the user decides to save the recipe.

### Saving Recipes

- Authenticated users can save a recipe, which copies it to the Recipe model and stores the generated image. Since Pollinations.ai keeps recently generated images accessible via the same prompt, we can fetch the image without regenerating it.
- The Saved Recipes page provides a clean, comfortable layout for browsing your recipes, along with these features:
  - Filter by tags (based on the filters the user applied when generating the recipes)
  - Search by title
  - Sort by newest or oldest
  - Infinite scroll (automatically loads 12 more recipes as you scroll to the bottom)
 
### Recipe Sharing

- Once user saves a recipe, he/she can then share it to the PantryPal community.
- Other users can then vote and comment on shared recipe.

### Individual Recipe Pages

Each saved recipe has its own individual page accessible via a unique URL. If the recipe is shared with the community, any user can view it through this URL.

Individual recipe pages include:
- The associated AI-generated image
- Tags related to the recipe
- Full list of ingredients and step-by-step instructions
- Actions: save/unsave, share/unshare
- Ratings and comments section (for shared recipes)

### Comment Section

Each shared recipe individual page includes a comment section.

Authenticated users can:
- Add comments on recipes
- See comments listed chronologically
- Post pictures of their meals after making the recipe

### Authentication + Profiles

- Django’s built-in auth for registration/login.
- Authenticated users can:
  - View/edit profile
  - See activity log (generated/saved/shared/rated/commented)
- Anonymous user can still generate recipes and browse shared recipes.

### UI/UX
- Fully responsive (mobile, tablet, desktop)
- Infinite scrolling on Saved / Shared pages
- Custom loading screens during AI calls
- Smooth AJAX interactions for recipe generation, voting and saving
- Built with Bootstrap + Vanilla JS

### Tech Stack

- Backend: Django, Python 3, OpenAI API, Groq
- Frontend:	HTML, CSS, Bootstrap, Vanilla JavaScript
- Database: SQLite for development, PostgreSQL for deployment
- Image Gen: Pollinations.ai
