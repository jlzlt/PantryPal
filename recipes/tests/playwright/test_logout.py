import os
import django
import sys
from playwright.sync_api import sync_playwright
from environment import *
from recipes.constants import WEB_ADDRESS

def test_logout_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Log in first
        page.goto(f"{WEB_ADDRESS}/login/")
        page.fill("[data-testid='input-username']", "a")
        page.fill("[data-testid='input-password']", "a")
        page.click("[data-testid='button-login']")
        page.wait_for_url("**/")
        page.wait_for_selector("text=🧄 Ingredients & Filters")
        assert page.locator("text=🧄 Ingredients & Filters").is_visible()

        # Open user dropdown first
        page.click("[data-testid='toggle-user-dropdown']")
        # Click logout using data-testid
        page.click("[data-testid='button-logout']")
        page.wait_for_url("**/")
        page.wait_for_selector("text=🧄 Ingredients & Filters")
        assert page.locator("text=🧄 Ingredients & Filters").is_visible()
        browser.close() 