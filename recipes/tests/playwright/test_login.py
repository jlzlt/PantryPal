import os
import django
import sys
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pantrypal.settings")
django.setup()

from recipes.constants import WEB_ADDRESS


def test_login_success():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{WEB_ADDRESS}/login/")

        page.fill("[data-testid='input-username']", "a")
        page.fill("[data-testid='input-password']", "a")
        page.click("[data-testid='button-login']")
        page.wait_for_url("**/")

        page.wait_for_selector("text=🧄 Ingredients & Filters")
        assert page.locator("text=🧄 Ingredients & Filters").is_visible()

        page.wait_for_selector("text=🍽️ Recipe Suggestions")
        assert page.locator("text=🍽️ Recipe Suggestions").is_visible()

        browser.close()

def test_login_incorrect_password():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{WEB_ADDRESS}/login/")

        page.fill("[data-testid='input-username']", "a")
        page.fill("[data-testid='input-password']", "wrongpassword")
        page.click("[data-testid='button-login']")
        page.wait_for_selector("text=Incorrect password.")
        assert page.locator("text=Incorrect password.").is_visible()
        browser.close()

def test_login_nonexistent_username():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{WEB_ADDRESS}/login/")

        page.fill("[data-testid='input-username']", "idontexistuser")
        page.fill("[data-testid='input-password']", "any_password")
        page.click("[data-testid='button-login']")
        page.wait_for_selector("text=This username does not exist.")
        assert page.locator("text=This username does not exist.").is_visible()
        browser.close()