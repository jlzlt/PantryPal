import os
import django
import sys
import time
from playwright.sync_api import sync_playwright


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pantrypal.settings")
django.setup()

from recipes.constants import WEB_ADDRESS
from django.contrib.auth import get_user_model

User = get_user_model()

def test_register_success():
    username = "testuser123"
    email = "testuser123@example.com"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{WEB_ADDRESS}/register/")

        page.fill("[data-testid='input-username']", username)
        page.fill("[data-testid='input-email']", email)
        page.fill("[data-testid='input-password']", "testpassword123")
        page.fill("[data-testid='input-confirmation']", "testpassword123")
        page.click("[data-testid='button-register']")
        page.wait_for_url("**/")

        page.wait_for_selector("text=🧄 Ingredients & Filters")
        assert page.locator("text=🧄 Ingredients & Filters").is_visible()

        page.wait_for_selector("text=🍽️ Recipe Suggestions")
        assert page.locator("text=🍽️ Recipe Suggestions").is_visible()

        browser.close()

    try:
        user = User.objects.get(username=username)
        user.delete()
        print(f"Deleted test user: {username}")
    except User.DoesNotExist:
        print(f"Test user {username} not found for cleanup.")

def test_register_username_taken():
    username = "testuser123"
    email = "newemail@example.com"  # Different email to isolate the username check

    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": "testuser123@example.com", "password": "notused"}
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{WEB_ADDRESS}/register/")

        page.fill("[data-testid='input-username']", username)
        page.fill("[data-testid='input-email']", email)
        page.fill("[data-testid='input-password']", "anotherpassword123")
        page.fill("[data-testid='input-confirmation']", "anotherpassword123")
        page.click("[data-testid='button-register']")

        # Wait for the error message to appear
        page.wait_for_selector("text=Username already taken.")

        # Assert error message is visible
        assert page.locator("text=Username already taken.").is_visible()

        browser.close()

    # Clean up test user if we created it here
    if created:
        user.delete()
        print(f"Deleted test user: {username}")

def test_register_password_mismatch():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{WEB_ADDRESS}/register/")

        page.fill("[data-testid='input-username']", "mismatchuser")
        page.fill("[data-testid='input-email']", "mismatch@example.com")
        page.fill("[data-testid='input-password']", "password123")
        page.fill("[data-testid='input-confirmation']", "password456")
        page.click("[data-testid='button-register']")
        page.wait_for_selector("text=Passwords must match.")
        assert page.locator("text=Passwords must match.").is_visible()
        browser.close()

def test_register_invalid_email():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{WEB_ADDRESS}/register/")

        page.fill("[data-testid='input-username']", "invalidemailuser")
        page.fill("[data-testid='input-email']", "notanemail")
        page.fill("[data-testid='input-password']", "password123")
        page.fill("[data-testid='input-confirmation']", "password123")
        page.click("[data-testid='button-register']")
        page.wait_for_selector("text=Please enter a valid email address.")
        assert page.locator("text=Please enter a valid email address.").is_visible()
        browser.close()
