"""
Setup script to install Playwright browsers for Streamlit Cloud
This runs automatically when the app starts
"""
import os
import subprocess
import sys

def install_playwright_browsers():
    """Install Playwright browsers if not already installed"""
    try:
        # Check if browsers are already installed
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                # Try to get browser path - if it works, browsers are installed
                browser_path = p.chromium.executable_path
                if os.path.exists(browser_path):
                    print("✅ Playwright browsers already installed")
                    return True
            except:
                pass
        
        # Browsers not installed, install them
        print("📦 Installing Playwright browsers...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully")
            return True
        else:
            print(f"❌ Error installing browsers: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️ Could not install browsers automatically: {e}")
        print("💡 You may need to install manually: python -m playwright install chromium")
        return False

# Run on import (for Streamlit Cloud)
if __name__ != "__main__":
    # Only run in Streamlit Cloud environment
    if os.environ.get("STREAMLIT_SERVER_PORT") or os.environ.get("STREAMLIT_SHARING_MODE"):
        install_playwright_browsers()

