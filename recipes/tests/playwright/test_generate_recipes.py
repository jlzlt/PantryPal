from playwright.sync_api import sync_playwright
from environment import *
from recipes.constants import WEB_ADDRESS

def test_generate_recipes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{WEB_ADDRESS}/")

        # Select to generate 1 recipe
        page.select_option("#num_recipes", "1")

        # Click the generate button
        page.click("[data-testid='button-generate']")

        # Wait for the loading screen
        page.wait_for_selector("text=Generating recipes...")

        # Wait for at least one recipe card to appear
        page.wait_for_selector(".card.h-100.shadow-sm")
        assert page.locator(".card.h-100.shadow-sm").count() == 1

        browser.close() 