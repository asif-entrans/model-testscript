# How to Find Input and Output Selectors

This guide will help you find the correct CSS selectors for ChatGPT, Claude, and Gemini when the default selectors stop working.

## Step-by-Step Guide

### 1. Open Browser DevTools

**Chrome/Edge:**
- Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
- Or right-click anywhere on the page → "Inspect" or "Inspect Element"

**Firefox:**
- Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)

### 2. Find the Input Selector

#### Method 1: Right-Click Method (Easiest)
1. **Right-click on the text input box** (where you type your question)
2. Select **"Inspect"** or **"Inspect Element"**
3. The element will be highlighted in the DevTools
4. **Right-click on the highlighted element** in DevTools
5. Select **"Copy"** → **"Copy selector"** or **"Copy CSS selector"**
6. This gives you the exact selector (e.g., `#prompt-textarea` or `.ql-editor`)

#### Method 2: Manual Inspection
1. Click the **Elements** tab in DevTools
2. Click the **element picker icon** (top-left, looks like a cursor with a box)
3. **Hover over the input box** on the page
4. Click on it - it will highlight in DevTools
5. Look at the element's attributes:
   - **ID**: Use `#id-name` (e.g., `#prompt-textarea`)
   - **Class**: Use `.class-name` (e.g., `.ql-editor`)
   - **Attribute**: Use `[attribute='value']` (e.g., `[contenteditable='true']`)

### 3. Find the Output Selector

1. **Send a test message** to the LLM (type something and submit)
2. **Wait for the response** to appear
3. **Right-click on the response text** (the AI's reply)
4. Select **"Inspect"**
5. The response element will be highlighted
6. **Look for a unique identifier**:
   - Check the **parent container** - often the response is in a div with a specific class
   - Look for attributes like `data-message-id`, `data-role`, etc.
   - Common patterns:
     - `div.message-content`
     - `div[data-message-author-role='assistant']`
     - `.model-response-text`

### 4. Find the Submit Button Selector (for Gemini)

1. **Right-click on the Send/Submit button**
2. Select **"Inspect"**
3. Look for:
   - `aria-label` attribute (e.g., `button[aria-label='Send message']`)
   - `data-testid` attribute (e.g., `button[data-testid='send-button']`)
   - Class name (e.g., `button.send-button`)

### 5. Find the Wait Selector (Optional)

This is the "Stop generating" button that appears while the AI is responding.

1. **Send a message** and watch for the "Stop" button to appear
2. **Right-click on the Stop button** while it's visible
3. Select **"Inspect"**
4. Copy its selector
5. The script will wait for this button to disappear (meaning response is complete)

## Common Selector Patterns

### ChatGPT
- **Input**: Usually `#prompt-textarea` or `textarea[placeholder*='message']`
- **Output**: `[data-message-author-role='assistant']` or `div.message`
- **Wait**: `[data-testid='stop-button']` or `button:has-text('Stop')`

### Claude
- **Input**: `div[contenteditable='true']` or `[contenteditable='true'][data-placeholder]`
- **Output**: `div.message-content` or `.font-claude-message` or `[data-message-id]`
- **Wait**: `button:has-text('Stop')` or `[aria-label*='Stop']`

### Gemini
- **Input**: `.input-area` or `[class*='input-area']` (Angular app - ignore `_ngcontent` attributes)
- **Output**: `.markdown` or `[class*='markdown']` (Angular app - ignore `_ngcontent` attributes)
- **Submit Button**: `button[aria-label*='Send']` or `button[data-testid*='send']`
- **Wait**: Usually not needed (uses fixed wait time)
- **Note**: Gemini uses Angular, so selectors like `.input-area[_ngcontent-ng-c787856502]` won't work. Use `.input-area` or `[class*='input-area']` instead.

## Testing Your Selectors

### In Browser Console

1. Open DevTools Console (press `F12`, then click "Console" tab)
2. Test your selector:

```javascript
// Test if input selector works
document.querySelector("YOUR_INPUT_SELECTOR")

// Test if output selector works (after getting a response)
document.querySelectorAll("YOUR_OUTPUT_SELECTOR")

// Test if button selector works
document.querySelector("YOUR_BUTTON_SELECTOR")
```

If it returns `null` or an empty array, the selector is wrong. If it returns an element, it's correct!

### In Playwright Codegen (Advanced)

1. Run: `python -m playwright codegen https://claude.ai` (or gemini.google.com)
2. Interact with the page in the browser window
3. Playwright will generate code with the correct selectors
4. Copy the selectors from the generated code

## Tips for Better Selectors

1. **Prefer IDs over classes** - IDs are unique and less likely to change
2. **Use attribute selectors** - `[data-testid='...']` or `[aria-label='...']` are often stable
3. **Avoid overly specific selectors** - `div.container > div.wrapper > div.content` breaks easily
4. **Use partial matches** - `[aria-label*='Send']` matches "Send message" or "Send"
5. **Test multiple selectors** - Have fallbacks ready

## Updating Selectors in the App

1. Open the Streamlit app
2. Go to **"Edit Selectors (Advanced)"** in the sidebar
3. Paste your new selector
4. Click **"Save Selectors"**
5. The new selector will be saved to `llm_config.json`

## Example: Finding Claude's Input Selector

1. Go to https://claude.ai
2. Press `F12` to open DevTools
3. Click the element picker (cursor icon)
4. Click on the text input area
5. In DevTools, you'll see something like:
   ```html
   <div contenteditable="true" data-placeholder="Message Claude..." class="ProseMirror">
   ```
6. Good selectors to try:
   - `div[contenteditable='true'][data-placeholder]` (most specific)
   - `div[contenteditable='true']` (more general)
   - `.ProseMirror` (if class is stable)

## Example: Finding Gemini's Selectors (Angular App)

**Important**: Gemini uses Angular, which adds dynamic `_ngcontent-ng-c*` attributes that change!

1. Go to https://gemini.google.com
2. Press `F12` to open DevTools
3. Right-click the input box → Inspect
4. You'll see something like:
   ```html
   <div class="input-area" _ngcontent-ng-c787856502>
   ```
5. **❌ DON'T use**: `.input-area[_ngcontent-ng-c787856502]` (the `_ngcontent` part changes!)
6. **✅ DO use**: 
   - `.input-area` (class selector - ignores Angular attributes)
   - `[class*='input-area']` (partial match - works with Angular)

7. For output, you'll see:
   ```html
   <div class="markdown" _ngcontent-ng-c369148791>
   ```
8. **✅ Use**: 
   - `.markdown` (class selector)
   - `[class*='markdown']` (partial match)

**Key Rule**: When you see `_ngcontent-ng-c*` attributes, **ignore them** and use just the class name!

## Troubleshooting

**Selector not working?**
- The website may have updated
- Try a more general selector (remove some specificity)
- Check if element is inside an iframe (may need special handling)
- Wait longer - some elements load dynamically

**Multiple elements found?**
- Use `.first` or `.last` in Playwright
- Make selector more specific
- Use `:nth-child()` if needed

**Element not visible?**
- Add `state="visible"` in Playwright: `await page.wait_for_selector(selector, state="visible")`
- Wait for page to fully load
- Check if element is hidden with CSS

## Quick Reference

| What to Find | How to Find It |
|-------------|----------------|
| Input box | Right-click input → Inspect → Copy selector |
| Output/Response | Right-click AI response → Inspect → Find parent container |
| Submit button | Right-click Send button → Inspect → Copy selector |
| Stop button | Right-click Stop button (while generating) → Inspect |

## Need Help?

If you're stuck:
1. Check the browser console for errors
2. Look at the status messages in the Streamlit app
3. Try the Playwright codegen tool for automatic selector detection
4. Use simpler, more general selectors as fallbacks

