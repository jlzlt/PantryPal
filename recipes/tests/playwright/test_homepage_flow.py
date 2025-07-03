from playwright.sync_api import sync_playwright
from environment import *
from recipes.constants import WEB_ADDRESS

def test_generate_recipe_as_guest():
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
        # Wait for exactly one recipe card to appear
        page.wait_for_selector(".card.h-100.shadow-sm")
        assert page.locator(".card.h-100.shadow-sm").count() == 1
        browser.close()

def test_generate_and_save_recipe_logged_in():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Log in
        page.goto(f"{WEB_ADDRESS}/login/")
        page.fill("[data-testid='input-username']", "a")
        page.fill("[data-testid='input-password']", "a")
        page.click("[data-testid='button-login']")
        page.wait_for_url("**/")
        page.wait_for_selector("text=🧄 Ingredients & Filters")
        # Select to generate 1 recipe
        page.select_option("#num_recipes", "1")
        # Click the generate button
        page.click("[data-testid='button-generate']")
        page.wait_for_selector("text=Generating recipes...")
        page.wait_for_selector(".card.h-100.shadow-sm")
        assert page.locator(".card.h-100.shadow-sm").count() == 1
        # Click save recipe button
        page.click("[data-testid='button-save-recipe']")
        # Wait for button text to change to 'Remove from Saved'
        page.wait_for_selector(".button-text:text('Remove from Saved')")
        assert page.locator(".button-text:text('Remove from Saved')").is_visible()
        # Click again to remove from saved
        page.click("[data-testid='button-save-recipe']")
        page.wait_for_selector(".button-text:text('💾 Save Recipe')")
        assert page.locator(".button-text:text('💾 Save Recipe')").is_visible()
        browser.close() 