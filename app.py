import warnings
# Suppress deprecation warnings for asyncio event loop policy (deprecated in Python 3.16)
# These warnings appear when using WindowsProactorEventLoopPolicy but the functionality still works
# Must be set BEFORE importing asyncio to catch all warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='asyncio')

import streamlit as st
import pandas as pd
import time
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import json
import threading
import queue
import sys
import asyncio

# Set Windows event loop policy at module level to avoid NotImplementedError with subprocess
# Note: Python 3.12+ uses ProactorEventLoopPolicy by default on Windows, but we set it explicitly
# for compatibility with older Python versions and to ensure subprocess operations work correctly
if sys.platform == 'win32':
    try:
        # Suppress deprecation warnings for this specific code block
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            # Try to set ProactorEventLoopPolicy (supports subprocess operations)
            # This is needed for Playwright's subprocess communication on Windows
            # Note: These methods are deprecated in Python 3.16 but still work in 3.14
            policy = asyncio.WindowsProactorEventLoopPolicy()
            asyncio.set_event_loop_policy(policy)
    except (AttributeError, RuntimeError):
        # If policy setting fails, continue anyway (Python 3.12+ handles this automatically)
        pass

# Configuration
USER_DATA_DIR = "./playwright_data"
CONFIG_FILE = "llm_config.json"

# Default selectors (can be updated via config file)
DEFAULT_CONFIG = {
    "ChatGPT": {
        "url": "https://chatgpt.com",
        "input_selector": "#prompt-textarea",
        "output_selector": "[data-message-author-role='assistant']",
        "submit_method": "enter",  # "enter" or "button"
        "submit_button_selector": None,
        "wait_selector": "[data-testid='stop-button']",  # Wait for this to disappear
        "response_wait_time": 15
    },
    "Claude": {
        "url": "https://claude.ai",
        "input_selector": "div[contenteditable='true'][data-placeholder]",
        "output_selector": "div.message-content, .font-claude-message, [data-message-id]",
        "submit_method": "enter",
        "submit_button_selector": None,
        "wait_selector": "button:has-text('Stop'), .stop-button, [aria-label*='Stop']",  # Wait for this to disappear
        "response_wait_time": 20
    },
    "Gemini": {
        "url": "https://gemini.google.com",
        "input_selector": ".input-area, textarea, [class*='input-area'], [class*='ql-editor']",
        "output_selector": ".markdown, [class*='markdown'], .model-response-text, [class*='message-content']",
        "submit_method": "button",
        "submit_button_selector": "button[aria-label*='Send'], button[aria-label*='send'], button[data-testid*='send']",
        "wait_selector": None,
        "response_wait_time": 20
    }
}

def load_config():
    """Load configuration from file or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults
                for key, value in user_config.items():
                    if key in config:
                        # Update existing LLM config
                        config[key].update(value)
                    else:
                        # Add custom LLM config
                        config[key] = value
                return config
        except Exception as e:
            st.warning(f"Error loading config: {e}. Using defaults.")
    return config

def save_config(config):
    """Save configuration to file"""
    try:
        # Separate default and custom configs for better organization
        config_to_save = {}
        for key, value in config.items():
            if key not in DEFAULT_CONFIG:
                # Custom LLM - save all
                config_to_save[key] = value
            else:
                # Default LLM - only save if modified
                if value != DEFAULT_CONFIG[key]:
                    config_to_save[key] = value
        
        # Always save custom LLMs even if they match defaults structure
        for key, value in config.items():
            if key not in DEFAULT_CONFIG:
                config_to_save[key] = value
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

def wait_for_response(page, config, question_num, total_questions):
    """Wait for LLM response to complete (sync version - kept for compatibility)"""
    wait_time = config.get("response_wait_time", 15)
    wait_selector = config.get("wait_selector")
    
    # Try to wait for the "stop" button to appear and then disappear
    if wait_selector:
        try:
            # Wait for stop button to appear (response started)
            page.wait_for_selector(wait_selector, timeout=5000)
            # Wait for stop button to disappear (response complete)
            page.wait_for_selector(wait_selector, state="hidden", timeout=60000)
        except PlaywrightTimeoutError:
            # Fallback to fixed wait time
            time.sleep(wait_time)
    else:
        # Fixed wait time if no wait selector
        time.sleep(wait_time)
    
    # Additional small delay to ensure content is fully rendered
    time.sleep(2)

async def wait_for_response_async(page, config, question_num, total_questions):
    """Wait for LLM response to complete (async version)"""
    import asyncio
    from playwright.async_api import TimeoutError as AsyncPlaywrightTimeoutError
    
    wait_time = config.get("response_wait_time", 15)
    wait_selector = config.get("wait_selector")
    
    # Try to wait for the "stop" button to appear and then disappear
    if wait_selector:
        try:
            # Wait for stop button to appear (response started)
            await page.wait_for_selector(wait_selector, timeout=5000)
            # Wait for stop button to disappear (response complete)
            await page.wait_for_selector(wait_selector, state="hidden", timeout=60000)
        except AsyncPlaywrightTimeoutError:
            # Fallback to fixed wait time
            await asyncio.sleep(wait_time)
    else:
        # Fixed wait time if no wait selector
        await asyncio.sleep(wait_time)
    
    # Additional small delay to ensure content is fully rendered
    await asyncio.sleep(2)

def get_response_text(page, config, question):
    """Extract response text from the page (sync version - kept for compatibility)"""
    output_selector = config.get("output_selector")
    
    try:
        # Wait for output to appear
        page.wait_for_selector(output_selector, timeout=10000)
        
        # Get all matching elements and take the last one (most recent response)
        elements = page.locator(output_selector).all()
        if elements:
            # Get the last element's text
            response_text = elements[-1].inner_text(timeout=5000)
            return response_text.strip()
        else:
            return "No response found"
    except PlaywrightTimeoutError:
        return "Timeout waiting for response"
    except Exception as e:
        return f"Error extracting response: {str(e)}"

async def get_response_text_async(page, config, question):
    """Extract response text from the page (async version)"""
    from playwright.async_api import TimeoutError as AsyncPlaywrightTimeoutError
    
    output_selector = config.get("output_selector")
    llm_site_name = config.get("_site_name", "")  # Pass site name if available
    
    try:
        # Try multiple selectors for better compatibility
        selectors_to_try = [output_selector]
        if "Claude" in str(config.get("_site_name", "")):
            selectors_to_try.extend([
                "div.message-content",
                ".font-claude-message",
                "[data-message-id]",
                "div[class*='message']",
                "div[class*='Message']"
            ])
        elif "Gemini" in str(config.get("_site_name", "")):
            # For Angular apps, use class selectors that ignore dynamic attributes
            selectors_to_try.extend([
                ".markdown",  # Direct class selector (ignores Angular _ngcontent attributes)
                "[class*='markdown']",  # Partial class match (works with Angular)
                ".model-response-text",
                "[class*='model-response']",
                ".message-content",
                "[class*='message-content']",
                "[data-message-type='model']",
                "div[class*='response']",
                "div[class*='Response']"
            ])
        
        # Wait for any output selector to appear
        element_found = None
        for selector in selectors_to_try:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                elements = await page.locator(selector).all()
                if elements:
                    element_found = elements[-1]  # Get the last (most recent) element
                    break
            except:
                continue
        
        if element_found:
            # Try to get text with multiple methods
            try:
                response_text = await element_found.inner_text(timeout=5000)
            except:
                # Fallback to text_content if inner_text fails
                response_text = await element_found.text_content(timeout=5000)
            
            if response_text and response_text.strip():
                return response_text.strip()
            else:
                return "Response found but empty"
        else:
            # Last resort: try to find any text that appeared after submission
            try:
                # Wait a bit more for content to load
                await asyncio.sleep(2)
                # Try to get all text on page and find the response
                page_text = await page.inner_text("body")
                if page_text:
                    return f"Extracted page text (may contain UI elements): {page_text[:500]}"
            except:
                pass
            return "No response found - selectors may need updating"
    except AsyncPlaywrightTimeoutError:
        return "Timeout waiting for response - response may still be loading"
    except Exception as e:
        return f"Error extracting response: {str(e)}"

def _run_test_thread(questions, config, llm_site_name, headless, results_queue, progress_queue, login_key=None):
    """Run automated tests in a separate thread with async Playwright (to avoid Streamlit asyncio conflicts)"""
    import asyncio
    import sys
    
    # Event loop policy is set at module level, no need to set it again here
    
    async def run_async_tests():
        """Async function to run the tests"""
        from playwright.async_api import async_playwright
        
        try:
            progress_queue.put((0, len(questions), "Starting browser..."))
            progress_queue.put((0, len(questions), f"Headless mode: {headless}"))
            
            # Ensure data directory exists
            try:
                os.makedirs(USER_DATA_DIR, exist_ok=True)
                progress_queue.put((0, len(questions), f"Data directory ready: {USER_DATA_DIR}"))
            except Exception as dir_error:
                error_msg = f"Failed to create data directory: {str(dir_error)}"
                progress_queue.put((0, 1, error_msg))
                results_queue.put(None)
                return
            
            # Initialize Playwright
            try:
                progress_queue.put((0, len(questions), "Initializing Playwright..."))
                async with async_playwright() as p:
                    progress_queue.put((0, len(questions), "Playwright initialized. Launching browser..."))
                    
                    # Launch browser with persistent context (saves login session)
                    progress_queue.put((0, len(questions), f"Launching browser (headless={headless})..."))
                    context = await p.chromium.launch_persistent_context(
                        USER_DATA_DIR,
                        headless=headless,
                        slow_mo=500,  # Adds delay to look more human
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    progress_queue.put((0, len(questions), "Browser launched successfully!"))
                    
                    try:
                        progress_queue.put((0, len(questions), f"Navigating to {config['url']}..."))
                        page = await context.new_page()
                        await page.goto(config["url"], wait_until="networkidle", timeout=30000)
                        
                        progress_queue.put((0, len(questions), "Page loaded. Starting questions..."))
                        
                        total = len(questions)
                        results = []
                        
                        for idx, question in enumerate(questions, 1):
                            if not question or pd.isna(question) or str(question).strip() == "":
                                results.append({
                                    "Response": "Empty question skipped",
                                    "Time Taken (seconds)": 0
                                })
                                progress_queue.put((idx, total, f"Skipped empty question {idx}"))
                                continue
                            
                            progress_queue.put((idx, total, f"Processing question {idx}/{total}: {question[:50]}..."))
                            start_time = time.time()
                            
                            try:
                                # Clear and fill input field
                                input_selector = config["input_selector"]
                                progress_queue.put((idx, total, f"Waiting for input field ({input_selector})..."))
                                
                                # Try multiple selectors if the first one fails (for Gemini/Claude)
                                input_element = None
                                selectors_to_try = [input_selector]
                                if llm_site_name == "Gemini":
                                    # For Angular apps, use class selectors without dynamic attributes
                                    selectors_to_try.extend([
                                        ".input-area",  # Direct class selector (ignores Angular _ngcontent attributes)
                                        "[class*='input-area']",  # Partial class match (works with Angular)
                                        "textarea",
                                        ".ql-editor",
                                        "[contenteditable='true'][role='textbox']",
                                        "[contenteditable='true']"
                                    ])
                                elif llm_site_name == "Claude":
                                    selectors_to_try.extend(["div[contenteditable='true']", "[contenteditable='true'][data-placeholder]", "[contenteditable='true']"])
                                
                                for selector in selectors_to_try:
                                    try:
                                        await page.wait_for_selector(selector, timeout=3000)
                                        input_element = page.locator(selector).first
                                        progress_queue.put((idx, total, f"Found input with selector: {selector}"))
                                        break
                                    except:
                                        continue
                                
                                if not input_element:
                                    raise Exception(f"Could not find input field with any selector: {selectors_to_try}")
                                
                                # Clear existing content - try different methods
                                try:
                                    await input_element.click()
                                    await asyncio.sleep(0.3)
                                    await page.keyboard.press("Control+A")
                                    await asyncio.sleep(0.2)
                                    await page.keyboard.press("Delete")
                                except:
                                    try:
                                        await input_element.fill("")
                                    except:
                                        pass
                                
                                await asyncio.sleep(0.5)
                                
                                # Type the question - use type for contenteditable divs
                                progress_queue.put((idx, total, f"Typing question {idx}..."))
                                question_text = str(question)
                                
                                # For contenteditable divs, use type instead of fill
                                if "contenteditable" in str(selectors_to_try).lower() or llm_site_name in ["Claude", "Gemini"]:
                                    await input_element.click()
                                    await asyncio.sleep(0.3)
                                    await input_element.type(question_text, delay=50)  # Type with delay for contenteditable
                                else:
                                    await input_element.fill(question_text)
                                
                                await asyncio.sleep(1)
                                
                                # Submit the question
                                progress_queue.put((idx, total, f"Submitting question {idx}..."))
                                submit_method = config.get("submit_method", "enter")
                                if submit_method == "button":
                                    submit_btn = config.get("submit_button_selector")
                                    if submit_btn:
                                        # Try multiple button selectors
                                        button_found = False
                                        button_selectors = [submit_btn]
                                        if llm_site_name == "Gemini":
                                            button_selectors.extend([
                                                "button[aria-label*='Send']",
                                                "button[aria-label*='send']",
                                                "button[data-testid*='send']",
                                                "button:has-text('Send')",
                                                "button.send-button"
                                            ])
                                        
                                        for btn_selector in button_selectors:
                                            try:
                                                await page.wait_for_selector(btn_selector, timeout=3000, state="visible")
                                                await page.click(btn_selector)
                                                button_found = True
                                                progress_queue.put((idx, total, f"Clicked submit button: {btn_selector}"))
                                                break
                                            except:
                                                continue
                                        
                                        if not button_found:
                                            progress_queue.put((idx, total, "Button not found, trying Enter key..."))
                                            await page.keyboard.press("Enter")
                                    else:
                                        await page.keyboard.press("Enter")
                                else:
                                    await page.keyboard.press("Enter")
                                
                                # Wait for response
                                progress_queue.put((idx, total, f"Waiting for response to question {idx}..."))
                                await wait_for_response_async(page, config, idx, total)
                                
                                # Extract response
                                progress_queue.put((idx, total, f"Extracting response for question {idx}..."))
                                response_text = await get_response_text_async(page, config, question)
                                
                                end_time = time.time()
                                elapsed = round(end_time - start_time, 2)
                                
                                results.append({
                                    "Response": response_text,
                                    "Time Taken (seconds)": elapsed
                                })
                                
                                progress_queue.put((idx, total, f"✓ Question {idx}/{total} completed in {elapsed}s"))
                                
                            except Exception as e:
                                end_time = time.time()
                                elapsed = round(end_time - start_time, 2)
                                error_msg = f"Error: {str(e)}"
                                import traceback
                                error_details = traceback.format_exc()
                                progress_queue.put((idx, total, f"✗ Question {idx}/{total} failed: {error_msg}"))
                                progress_queue.put((idx, total, f"Error details: {error_details[:200]}"))
                                
                                results.append({
                                    "Response": error_msg,
                                    "Time Taken (seconds)": elapsed
                                })
                            
                            await asyncio.sleep(2)  # Small delay between questions
                        
                        progress_queue.put((total, total, "Closing browser..."))
                        await context.close()
                        results_queue.put(results)
                        progress_queue.put((total, total, "✓ All questions completed!"))
                        
                    except Exception as nav_error:
                        import traceback
                        error_details = traceback.format_exc()
                        error_msg = f"Error during navigation/execution: {str(nav_error)}\nDetails: {error_details[:500]}"
                        progress_queue.put((0, 1, error_msg))
                        try:
                            await context.close()
                        except:
                            pass
                        results_queue.put(None)
                        
            except Exception as browser_error:
                import traceback
                error_details = traceback.format_exc()
                error_msg = f"Failed to launch browser: {str(browser_error)}\nDetails: {error_details[:500]}"
                progress_queue.put((0, 1, error_msg))
                results_queue.put(None)
                return
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Fatal error: {str(e)}\n{error_details[:1000]}"
            progress_queue.put((0, 1, error_msg))
            results_queue.put(None)
    
    # Create new event loop for this thread and run async function
    # Event loop policy is set at module level
    try:
        
        # Create a new event loop with the correct policy
        # We can't use asyncio.run() here because it checks for existing loops
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_async_tests())
        finally:
            loop.close()
    except RuntimeError as e:
        # If there's already a loop running, try a different approach
        if "asyncio.run() cannot be called from a running event loop" in str(e) or "There is no current event loop" in str(e):
            # Create new loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_async_tests())
            finally:
                loop.close()
        else:
            raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"Event loop error: {str(e)}\n{error_details[:1000]}"
        progress_queue.put((0, 1, error_msg))
        results_queue.put(None)

def run_test(questions, config, progress_bar, status_text, llm_site_name):
    """Run automated tests on the LLM website (wrapper that runs in thread)"""
    # Check if login is needed (first time)
    login_key = f"logged_in_{llm_site_name}"
    is_first_run = not st.session_state.get(login_key, False)
    
    if is_first_run:
        status_text.info("🌐 **First run** - Browser will open for login. After logging in, click the button below.")
    
    # Use queues to communicate between threads
    results_queue = queue.Queue()
    progress_queue = queue.Queue()
    
    # Start the test in a separate thread
    # For first run, always disable headless so user can see and log in
    headless = st.session_state.get('headless', False) and not is_first_run
    
    thread = threading.Thread(
        target=_run_test_thread,
        args=(questions, config, llm_site_name, headless, results_queue, progress_queue, login_key),
        daemon=True
    )
    thread.start()
    
    # Show login confirmation button if first run
    if is_first_run:
        if st.button("✅ I'm logged in - Continue", key="login_confirm", type="primary"):
            st.session_state[login_key] = True
            status_text.success("✅ Login confirmed! Automation continuing...")
            st.rerun()
    
    # Monitor progress and update UI
    total = len(questions)
    max_wait_time = 3600  # Maximum 1 hour wait time
    start_wait = time.time()
    
    # Wait for thread to complete, checking progress periodically
    # First, wait a moment for initial messages
    time.sleep(0.5)
    
    while thread.is_alive() and (time.time() - start_wait) < max_wait_time:
        # Check for progress updates
        try:
            while True:
                idx, total_q, message = progress_queue.get_nowait()
                status_text.info(message)
                if total_q > 0:
                    progress_bar.progress(idx / total_q)
        except queue.Empty:
            pass
        
        time.sleep(0.2)  # Small delay to avoid busy waiting
        thread.join(timeout=0.2)  # Check if thread is done
    
    # Get any remaining progress updates
    try:
        while True:
            idx, total_q, message = progress_queue.get_nowait()
            status_text.info(message)
            if total_q > 0:
                progress_bar.progress(idx / total_q)
    except queue.Empty:
        pass
    
    # Wait a bit more for thread to finish
    thread.join(timeout=5)
    
    # Get results
    try:
        # Wait a bit longer for results
        results = results_queue.get(timeout=10)
        if results is None:
            # Get the last error message from progress queue
            last_error = "Unknown error occurred"
            try:
                while True:
                    idx, total_q, message = progress_queue.get_nowait()
                    if "error" in message.lower() or "failed" in message.lower() or "fatal" in message.lower():
                        last_error = message
            except queue.Empty:
                pass
            status_text.error(f"Test run failed: {last_error}")
            return None
        progress_bar.progress(1.0)
        return results
    except queue.Empty:
        # Check if thread is still alive
        if thread.is_alive():
            status_text.warning("Test run is taking longer than expected. Please wait...")
            # Try one more time with longer timeout
            try:
                results = results_queue.get(timeout=30)
                if results is None:
                    status_text.error("Test run failed. Check browser window for details.")
                    return None
                progress_bar.progress(1.0)
                return results
            except queue.Empty:
                status_text.error("Test run timed out. The browser may still be running. Please check the browser window.")
                return None
        else:
            status_text.error("Test run completed but no results were returned. Check browser window for errors.")
            return None

# --- Streamlit UI ---
st.set_page_config(
    page_title="AI LLM Test Automation",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI LLM Test Automation")
st.markdown("Automate testing of ChatGPT, Claude, Gemini, and any custom LLM service through browser automation")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Load config
    config = load_config()
    
    llm_site = st.selectbox("Select LLM Service", list(config.keys()))
    site_config = config[llm_site]
    
    # Custom LLM Management
    with st.expander("➕ Add/Edit Custom LLM Service"):
        st.caption("Add your own LLM service or edit existing ones")
        
        # List of existing LLMs
        existing_llms = list(config.keys())
        selected_llm_to_edit = st.selectbox("Edit existing LLM (or create new)", ["+ Create New LLM"] + existing_llms, key="llm_editor")
        
        if selected_llm_to_edit == "+ Create New LLM":
            new_llm_name = st.text_input("LLM Service Name", placeholder="e.g., Perplexity, Copilot, etc.", key="new_llm_name")
            is_new = True
        else:
            new_llm_name = st.text_input("LLM Service Name", value=selected_llm_to_edit, key="edit_llm_name")
            is_new = False
        
        if new_llm_name:
            col1, col2 = st.columns(2)
            with col1:
                new_url = st.text_input("URL", value=config.get(selected_llm_to_edit, {}).get("url", "") if not is_new else "", key="new_url")
            with col2:
                new_input_selector = st.text_input("Input Selector", value=config.get(selected_llm_to_edit, {}).get("input_selector", "") if not is_new else "", key="new_input")
            
            new_output_selector = st.text_input("Output Selector", value=config.get(selected_llm_to_edit, {}).get("output_selector", "") if not is_new else "", key="new_output")
            
            col3, col4 = st.columns(2)
            with col3:
                current_submit = config.get(selected_llm_to_edit, {}).get("submit_method", "enter") if not is_new else "enter"
                new_submit_method = st.selectbox("Submit Method", ["enter", "button"], index=0 if current_submit == "enter" else 1, key="new_submit_method")
            with col4:
                new_submit_button = st.text_input("Submit Button Selector (if using button)", value=config.get(selected_llm_to_edit, {}).get("submit_button_selector", "") if not is_new else "", key="new_submit_btn")
            
            new_wait_selector = st.text_input("Wait Selector (optional - for 'Stop' button)", value=config.get(selected_llm_to_edit, {}).get("wait_selector", "") if not is_new else "", key="new_wait")
            new_wait_time = st.number_input("Response Wait Time (seconds)", min_value=5, max_value=60, value=config.get(selected_llm_to_edit, {}).get("response_wait_time", 15) if not is_new else 15, key="new_wait_time")
            
            col_save, col_delete = st.columns(2)
            with col_save:
                if st.button("💾 Save LLM Configuration", type="primary", key="save_llm"):
                    if new_llm_name and new_url and new_input_selector and new_output_selector:
                        # Create/update LLM config
                        config[new_llm_name] = {
                            "url": new_url,
                            "input_selector": new_input_selector,
                            "output_selector": new_output_selector,
                            "submit_method": new_submit_method,
                            "submit_button_selector": new_submit_button if new_submit_button else None,
                            "wait_selector": new_wait_selector if new_wait_selector else None,
                            "response_wait_time": int(new_wait_time)
                        }
                        
                        # If editing and name changed, remove old entry
                        if not is_new and selected_llm_to_edit != new_llm_name:
                            if selected_llm_to_edit in config:
                                del config[selected_llm_to_edit]
                        
                        if save_config(config):
                            st.success(f"✅ LLM '{new_llm_name}' saved successfully!")
                            st.rerun()
                    else:
                        st.error("Please fill in all required fields (Name, URL, Input Selector, Output Selector)")
            
            with col_delete:
                if not is_new and selected_llm_to_edit not in DEFAULT_CONFIG:
                    if st.button("🗑️ Delete Custom LLM", type="secondary", key="delete_llm"):
                        if selected_llm_to_edit in config:
                            del config[selected_llm_to_edit]
                            if save_config(config):
                                st.success(f"✅ LLM '{selected_llm_to_edit}' deleted!")
                                st.rerun()
                elif not is_new:
                    st.caption("Default LLMs cannot be deleted")
    
    st.subheader("Browser Settings")
    headless_mode = st.checkbox("Headless Mode", value=False, help="Run browser in background (disable to see automation)")
    st.session_state.headless = headless_mode
    
    st.subheader("Advanced Settings")
    
    # Test Playwright button
    if st.button("🔧 Test Playwright Installation", help="Click to verify Playwright is working correctly"):
        test_status = st.empty()
        test_status.info("Testing Playwright in background thread...")
        
        def test_playwright_thread(result_queue):
            """Test Playwright in a separate thread with new event loop"""
            import asyncio
            import sys
            try:
                # Event loop policy is already set at module level
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def test_async():
                    from playwright.async_api import async_playwright
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=True)
                        page = await browser.new_page()
                        await page.goto("https://example.com", timeout=10000)
                        title = await page.title()
                        await browser.close()
                    return title
                
                title = loop.run_until_complete(test_async())
                loop.close()
                result_queue.put(("success", f"✅ Playwright is working! Test page title: {title}"))
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                try:
                    loop.close()
                except:
                    pass
                result_queue.put(("error", f"❌ Playwright test failed: {str(e)}\n\nTry running: python -m playwright install chromium\n\nDetails: {error_details[:500]}"))
        
        # Run test in thread
        test_queue = queue.Queue()
        test_thread = threading.Thread(target=test_playwright_thread, args=(test_queue,), daemon=True)
        test_thread.start()
        
        # Wait for result
        import time
        max_wait = 10
        start_time = time.time()
        while test_thread.is_alive() and (time.time() - start_time) < max_wait:
            time.sleep(0.2)
            test_thread.join(timeout=0.2)
        
        # Get result
        try:
            status, message = test_queue.get(timeout=2)
            if status == "success":
                test_status.success(message)
            else:
                test_status.error(message)
        except queue.Empty:
            test_status.warning("⏳ Test is taking longer than expected. Playwright may still be installing browsers. Check the terminal for details.")
    
    if st.expander("Edit Selectors (Advanced)"):
        # st.caption("⚠️ Selectors may change if websites update. Update these if automation fails.")
        # st.info("💡 **Need help finding selectors?** See `FINDING_SELECTORS.md` for a detailed guide on using browser DevTools to find the correct selectors.")
        
        new_input = st.text_input("Input Selector", value=site_config["input_selector"])
        new_output = st.text_input("Output Selector", value=site_config["output_selector"])
        new_wait = st.text_input("Wait Selector (optional)", value=site_config.get("wait_selector", ""))
        new_wait_time = st.number_input("Response Wait Time (seconds)", min_value=5, max_value=60, value=site_config.get("response_wait_time", 15))
        
        if st.button("Save Selectors"):
            config[llm_site]["input_selector"] = new_input
            config[llm_site]["output_selector"] = new_output
            config[llm_site]["wait_selector"] = new_wait if new_wait else None
            config[llm_site]["response_wait_time"] = int(new_wait_time)
            if save_config(config):
                st.success("Selectors saved!")
                st.rerun()

# Main content area
uploaded_file = st.file_uploader("📤 Upload Excel File with Questions", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        # Check for required columns
        if 'Question' not in df.columns:
            st.error("❌ Excel file must have a 'Question' column!")
            st.stop()
        
        # Initialize response columns if they don't exist
        if 'Response' not in df.columns:
            df['Response'] = ""
        if 'Time Taken (seconds)' not in df.columns:
            df['Time Taken (seconds)'] = ""
        
        st.success(f"✅ Loaded {len(df)} questions from Excel file")
        st.dataframe(df.head(10), width='stretch')
        
        if st.button("🚀 Start Browser Test", type="primary"):
            questions = df['Question'].tolist()
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Run tests
            results = run_test(questions, site_config, progress_bar, status_text, llm_site)
            
            if results:
                # Update dataframe with results
                df['Response'] = [r['Response'] for r in results]
                df['Time Taken (seconds)'] = [r['Time Taken (seconds)'] for r in results]
                
                progress_bar.progress(1.0)
                status_text.success("✅ All tests completed!")
                
                # Display results
                st.subheader("📊 Results")
                st.dataframe(df, width='stretch', height=400)
                
                # Download button
                output_filename = f"results_{llm_site}_{int(time.time())}.xlsx"
                excel_buffer = pd.ExcelWriter(output_filename, engine='openpyxl')
                df.to_excel(excel_buffer, index=False, sheet_name='Results')
                excel_buffer.close()
                
                with open(output_filename, 'rb') as f:
                    st.download_button(
                        "📥 Download Filled Excel Sheet",
                        f.read(),
                        file_name=output_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # Clean up
                if os.path.exists(output_filename):
                    os.remove(output_filename)
            else:
                # Additional error info if run_test returned None
                status_text.error("❌ Test run was cancelled or failed. Check the status messages above for details. If a browser window opened, check it for any errors or login requirements.")
                
    except Exception as e:
        st.error(f"❌ Error reading Excel file: {str(e)}")
        st.exception(e)

# Instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    ### Step-by-Step Guide:
    
    1. **Prepare Excel File**: Create an Excel file with a column named "Question" containing your test questions.
       - Optional: Include "Response" and "Time Taken (seconds)" columns (will be filled automatically)
    
    2. **First Run Setup**:
       - Uncheck "Headless Mode" in the sidebar
       - Click "Start Browser Test"
       - A browser window will open - **log in manually** to the LLM service
       - Click "I'm logged in" button
       - The automation will start
    
    3. **Subsequent Runs**:
       - Your login session is saved, so you can enable headless mode
       - Just upload your Excel and click "Start Browser Test"
    
    4. **Download Results**: After completion, download the filled Excel sheet
    
    ### Troubleshooting:
    - **Selectors not working?** Websites update frequently. Use the "Edit Selectors" section to update them.
    - **How to find selectors?** Right-click the input box → Inspect → Copy the CSS selector
    - **Getting blocked?** Try disabling headless mode and adding delays between questions
    """)

# Footer
st.markdown("---")
st.caption("💡 Tip: Keep the browser window visible on first run to ensure login is successful")

