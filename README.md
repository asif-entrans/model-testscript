# AI LLM Test Automation

Automate testing of Large Language Models (ChatGPT, Claude, Gemini, and custom LLMs) through browser automation. Upload an Excel sheet with questions, and get back a filled sheet with responses and timing data.

## Features

- 🤖 **Multi-LLM Support**: Test ChatGPT, Claude, Gemini, and **any custom LLM service**
- ➕ **Custom LLM Configuration**: Add your own LLM services with custom selectors
- 📊 **Excel Integration**: Upload questions, download results
- ⏱️ **Performance Metrics**: Track response times for each question
- 🔐 **Session Persistence**: Save login sessions to avoid repeated logins
- 🎯 **Configurable Selectors**: Update selectors if websites change
- 📈 **Progress Tracking**: Real-time progress updates

## Prerequisites

- Python 3.8 or higher
- Windows, macOS, or Linux

## Installation

### Quick Setup (Windows)
**In PowerShell:**
```powershell
.\setup.bat
```

**In Command Prompt:**
```cmd
setup.bat
```

### Quick Setup (Linux/macOS)
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

1. **Clone or download this project**

2. **Install Python dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   python -m playwright install chromium
   ```

4. **Create example Excel file (optional)**:
   ```bash
   python create_example.py
   ```

## Usage

### 1. Prepare Your Excel File

Create an Excel file (`.xlsx`) with the following structure:

| Question | Response | Time Taken (seconds) |
|----------|----------|---------------------|
| What is Python? | | |
| Explain machine learning | | |
| ... | | |

**Note**: The "Question" column is required. "Response" and "Time Taken (seconds)" columns are optional and will be filled automatically.

### 2. Run the Application

```bash
python -m streamlit run app.py
```

**Note:** In PowerShell, you may need to use `.\setup.bat` instead of `setup.bat`

The application will open in your default web browser at `http://localhost:8501`

### 3. First-Time Setup

1. **Select LLM Service**: Choose ChatGPT, Claude, or Gemini from the sidebar
2. **Disable Headless Mode**: Uncheck "Headless Mode" in the sidebar (so you can see the browser)
3. **Upload Excel File**: Click "Browse files" and select your Excel file
4. **Start Test**: Click "🚀 Start Browser Test"
5. **Login**: When the browser window opens, manually log in to the LLM service
6. **Confirm Login**: Click "I'm logged in" button in the app
7. **Wait for Completion**: The automation will run through all questions

### 4. Subsequent Runs

Once you've logged in once, your session is saved:
- You can enable "Headless Mode" to run in the background
- Just upload your Excel file and click "Start Browser Test"
- No need to log in again!

### 5. Download Results

After completion, click "📥 Download Filled Excel Sheet" to get your results.

## Configuration

### Adding Custom LLM Services

You can add your own LLM services (Perplexity, Copilot, etc.):

1. Open the **"➕ Add/Edit Custom LLM Service"** section in the sidebar
2. Click **"+ Create New LLM"**
3. Fill in:
   - **LLM Service Name**: e.g., "Perplexity", "Copilot"
   - **URL**: The website URL
   - **Input Selector**: CSS selector for the input box (see `FINDING_SELECTORS.md`)
   - **Output Selector**: CSS selector for the response area
   - **Submit Method**: "enter" or "button"
   - **Submit Button Selector**: (if using button method)
   - **Wait Selector**: (optional) Selector for "Stop" button
   - **Response Wait Time**: How long to wait for responses
4. Click **"💾 Save LLM Configuration"**
5. Your custom LLM will appear in the dropdown!

**Tip**: Use the browser DevTools (F12) to find selectors. See `FINDING_SELECTORS.md` for detailed instructions.

### Updating Selectors

Websites update frequently, and selectors may break. To update them:

1. Open the "Edit Selectors (Advanced)" section in the sidebar
2. See `FINDING_SELECTORS.md` for a complete guide, or follow these quick steps:
   - **Right-click on the input box** → "Inspect"
   - **Right-click on the highlighted element** in DevTools → "Copy" → "Copy selector"
   - Paste the selector into the app
3. Update the selectors in the app
4. Click "Save Selectors"

### Quick Selector Finding

**For Input Box:**
- Right-click the text input → Inspect → Copy selector
- Common patterns: `#prompt-textarea`, `[contenteditable='true']`, `textarea`

**For Output/Response:**
- Send a test message, wait for response
- Right-click the AI's response → Inspect → Find parent container
- Common patterns: `[data-message-author-role='assistant']`, `.message-content`

**For Submit Button (Gemini):**
- Right-click Send button → Inspect → Copy selector
- Common patterns: `button[aria-label*='Send']`, `button[data-testid*='send']`

📖 **For detailed instructions**, see `FINDING_SELECTORS.md` in the project directory.

## Project Structure

```
model-testscript/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── create_example.py     # Script to generate example Excel file
├── setup.bat             # Windows setup script
├── setup.sh              # Linux/macOS setup script
├── llm_config.json       # Selector configuration (auto-generated)
├── playwright_data/      # Saved browser sessions (auto-generated)
└── example_questions.xlsx # Example Excel template (run create_example.py to generate)
```

## Troubleshooting

### Selectors Not Working

**Problem**: Automation fails to find input/output elements

**Solution**: 
- Websites update frequently. Use browser DevTools to find new selectors
- Update selectors in the "Edit Selectors" section
- Check the console for error messages

### Login Issues

**Problem**: Browser doesn't remember login

**Solution**:
- Make sure "Headless Mode" is disabled on first run
- Manually log in when prompted
- Check that `playwright_data/` folder exists and has write permissions

### Timeout Errors

**Problem**: Script times out waiting for responses

**Solution**:
- Increase "Response Wait Time" in advanced settings
- Check your internet connection
- Some responses take longer - adjust wait time accordingly

### Anti-Bot Detection

**Problem**: Website blocks the automation

**Solution**:
- Keep headless mode disabled
- Increase delays between questions
- Use a slower connection speed (slow_mo parameter)
- Some sites may require CAPTCHA - solve manually if needed

## Advanced Usage

### Custom Configuration

Edit `llm_config.json` directly to customize:
- URLs
- Selectors
- Wait times
- Submit methods

### Batch Processing

Run multiple Excel files by:
1. Processing one file
2. Downloading results
3. Uploading the next file
4. Repeat

## Limitations

- **Rate Limiting**: Some services may rate-limit requests. Add delays between questions if needed.
- **Selector Changes**: Websites update frequently. You may need to update selectors periodically.
- **CAPTCHA**: Some sites may show CAPTCHA challenges that require manual intervention.
- **Response Quality**: This tool tests response generation, not response quality. Manual review is recommended.

## Contributing

Feel free to submit issues or pull requests if you:
- Find bugs
- Have selector updates for new website versions
- Want to add support for new LLM services

## License

This project is provided as-is for testing and automation purposes.

## Disclaimer

This tool is for legitimate testing purposes only. Please respect the terms of service of the LLM platforms you're testing. Use responsibly and don't overload their servers.

