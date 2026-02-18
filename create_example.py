"""
Script to create an example Excel file for testing
Run this after installing dependencies: python create_example.py
"""
import pandas as pd

# Create example questions
questions = [
    "What is Python?",
    "Explain machine learning in simple terms",
    "What are the benefits of using Python for data science?",
    "How does a neural network work?",
    "What is the difference between AI and ML?",
    "What is natural language processing?",
    "Explain the concept of deep learning",
    "What are the main types of machine learning?",
    "How do you handle missing data in a dataset?",
    "What is overfitting in machine learning?"
]

# Create DataFrame
df = pd.DataFrame({
    'Question': questions,
    'Response': [''] * len(questions),
    'Time Taken (seconds)': [''] * len(questions)
})

# Save to Excel
df.to_excel('example_questions.xlsx', index=False)
print("Example Excel file 'example_questions.xlsx' created successfully!")
print(f"   Contains {len(questions)} sample questions")

