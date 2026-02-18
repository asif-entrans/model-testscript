# Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Dependencies

**Windows (PowerShell):**
```powershell
.\setup.bat
```

**Windows (Command Prompt):**
```cmd
setup.bat
```

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**Or manually:**
```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
python create_example.py
```

## Step 2: Prepare Your Excel File

Create an Excel file with a column named **"Question"**. Example:

| Question |
|----------|
| What is Python? |
| Explain machine learning |
| How does AI work? |

Optional columns (will be filled automatically):
- `Response`
- `Time Taken (seconds)`

Or use the example file: `example_questions.xlsx` (run `python create_example.py` to create it)

## Step 3: Run the Application

```bash
python -m streamlit run app.py
```

The app will open at `http://localhost:8501`

## Step 4: First Run - Login Setup

1. **Select LLM Service** (ChatGPT, Claude, or Gemini) from sidebar
2. **Uncheck "Headless Mode"** (so you can see the browser)
3. **Upload your Excel file**
4. **Click "🚀 Start Browser Test"**
5. **A browser window opens** - manually log in to the LLM service
6. **Click "I'm logged in"** button in the app
7. **Wait for completion** - automation runs through all questions

## Step 5: Download Results

After completion, click **"📥 Download Filled Excel Sheet"** to get your results with responses and timing data.

## Next Runs

Once logged in once, your session is saved! You can:
- Enable "Headless Mode" to run in background
- Just upload Excel and click "Start Browser Test"
- No need to log in again!

## Troubleshooting

**Selectors not working?**
- Websites update frequently
- Use "Edit Selectors" in sidebar to update them
- Right-click input box → Inspect → Copy CSS selector

**Can't log in?**
- Make sure headless mode is OFF on first run
- Check browser window opened correctly
- Try refreshing the page manually

**Timeout errors?**
- Increase "Response Wait Time" in advanced settings
- Check internet connection
- Some responses take longer

## Need Help?

See the full [README.md](README.md) for detailed documentation.

