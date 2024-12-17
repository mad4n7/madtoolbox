import os
import re
from collections import defaultdict
import csv
import PyPDF2


def extract_text_from_pdf(pdf_path, start_word):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        found_start_word = False
        for page in reader.pages:
            page_text = page.extract_text()
            if not found_start_word:
                start_index = page_text.find(start_word)
                if start_index != -1:
                    found_start_word = True
                    page_text = page_text[start_index:]
                else:
                    page_text = ''
            text += page_text
    return text


def process_statements(folder_path, start_word):
    transactions = defaultdict(float)

    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            text = extract_text_from_pdf(pdf_path, start_word)

            # Regular expression pattern to match transaction data
            pattern = r'(\d{2}/\d{2}/\d{4})\s+(.*?)\s+(\$?\d+\.\d{2})'
            matches = re.findall(pattern, text)

            for date, description, amount in matches:
                key = description.strip()
                transactions[key] += float(amount.replace('$', ''))

    return transactions


def save_to_csv(transactions, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Description', 'Total Amount'])
        for description, amount in transactions.items():
            writer.writerow([description, f'${amount:.2f}'])


# Ask for folder path during execution
folder_path = input("Enter the path to the folder containing PDF statements: ")
folder_path = os.path.abspath(folder_path)

# Ask for start word
start_word = input("Enter the word after which the code should start reading the pdf transactions: ")

# Ensure the folder exists
if not os.path.isdir(folder_path):
    print(f"Error: The folder '{folder_path}' does not exist.")
else:
    output_file = os.path.join(folder_path, 'credit_card_summary.csv')

    transactions = process_statements(folder_path, start_word)
    save_to_csv(transactions, output_file)
    print(f"Results saved to {output_file}")