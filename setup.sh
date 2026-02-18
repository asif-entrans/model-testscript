#!/bin/bash

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Installing Playwright browsers..."
playwright install chromium

echo ""
echo "Creating example Excel file..."
python create_example.py

echo ""
echo "Setup complete!"
echo ""
echo "To run the application, use: streamlit run app.py"

