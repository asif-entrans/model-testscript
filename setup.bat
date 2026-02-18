@echo off
echo Installing Python dependencies...
python -m pip install -r requirements.txt

echo.
echo Installing Playwright browsers...
python -m playwright install chromium

echo.
echo Creating example Excel file...
python create_example.py

echo.
echo Setup complete!
echo.
echo To run the application, use: python -m streamlit run app.py
pause

