# Deploying to Streamlit Cloud

This guide will help you deploy the AI LLM Test Automation app to Streamlit Cloud.

## Prerequisites

1. A GitHub account
2. Your project pushed to a GitHub repository
3. A Streamlit Cloud account (free at https://streamlit.io/cloud)

## Step 1: Prepare Your Repository

Make sure your repository has these files:
- `app.py` - Main application
- `requirements.txt` - Python dependencies
- `packages.txt` - System packages (for Playwright browsers) - **NO COMMENTS ALLOWED!**
- `.streamlit/config.toml` - Streamlit configuration (optional)

**⚠️ IMPORTANT**: The `packages.txt` file must contain ONLY package names, one per line, with NO comments or blank lines with text. Streamlit Cloud will try to install everything in that file as a package!

## Step 2: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Connect your GitHub repository
4. Select your repository and branch
5. Set the main file path: `app.py`
6. Click "Deploy"

## Step 3: Install Playwright Browsers (Important!)

**Streamlit Cloud doesn't automatically install Playwright browsers.** You need to do this manually:

### Option 1: Using Streamlit Cloud's Console (Recommended)

1. After deployment, go to your app's settings
2. Open the "Advanced settings" or "Console"
3. Run this command:
   ```bash
   playwright install chromium
   ```
4. Restart your app

### Option 2: Add to requirements.txt (Alternative)

Add this to your `requirements.txt`:
```
playwright>=1.40.0
```

Then create a `postinstall` script or use Streamlit's `on_startup` hook.

### Option 3: Manual Installation via Console

1. In Streamlit Cloud, go to your app
2. Click the "⋮" menu → "Manage app" → "Reboot app"
3. In the logs, you'll see if browsers need installation
4. Use the Streamlit Cloud console to run: `playwright install chromium`

## Step 4: Verify Installation

1. Once deployed, click the "🔧 Test Playwright Installation" button in the sidebar
2. If it shows "✅ Playwright is working!", you're all set!
3. If it shows an error, browsers may not be installed - see Step 3

## Troubleshooting

### "Executable doesn't exist" Error

This means Playwright browsers aren't installed. Solutions:

1. **Use Streamlit Cloud Console:**
   - Go to your app settings
   - Open console/terminal
   - Run: `playwright install chromium`

2. **Add to deployment script:**
   Create a file `.streamlit/on_startup.py`:
   ```python
   import subprocess
   import sys
   subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
   ```

3. **Contact Streamlit Support:**
   - Some Streamlit Cloud instances may need special configuration
   - Check Streamlit Cloud documentation for Playwright support

### Browser Installation Takes Time

- First deployment may take 5-10 minutes to install browsers
- Be patient during the first run
- Subsequent deployments are faster

### Memory Issues

- Playwright browsers use significant memory
- If you get memory errors, consider:
  - Using headless mode only
  - Reducing concurrent operations
  - Upgrading your Streamlit Cloud plan

## Alternative: Use Docker (Advanced)

If Streamlit Cloud doesn't work, you can deploy using Docker:

1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   
   RUN apt-get update && apt-get install -y \
       libnss3 libatk-bridge2.0-0 libdrm2 \
       libxkbcommon0 libgbm1 libasound2 \
       && rm -rf /var/lib/apt/lists/*
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   RUN playwright install chromium
   
   COPY . .
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. Deploy to a platform that supports Docker (Heroku, Railway, etc.)

## Notes

- **Free Tier Limitations**: Streamlit Cloud free tier may have resource limits
- **Browser Size**: Chromium is ~200MB, so first deployment takes time
- **Session Persistence**: Browser sessions are saved in `playwright_data/` folder
- **Headless Mode**: Recommended for Streamlit Cloud to save resources

## Support

If you encounter issues:
1. Check Streamlit Cloud logs
2. Verify Playwright browsers are installed
3. Test locally first to ensure everything works
4. Check Streamlit Cloud status page

