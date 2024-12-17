import PyPDF2
import re
import csv
import os

def read_pdf_file(file_path):
    with open(file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return ' '.join(page.extract_text() for page in pdf_reader.pages)

def extract_transactions(text):
    pattern = r'\d{2}/\d{2}\s+\d{2}/\d{2}\s+(.+?)\s+(?:\S+\s+){2}\d+\s+(\d+\.\d{2})'
    return re.findall(pattern, text)

def normalize_description(description):
    # Remove trailing spaces and periods
    return description.rstrip(' .')

def sum_transactions(transactions):
    transaction_sums = {}
    for description, amount in transactions:
        description = normalize_description(description)
        amount = float(amount)
        transaction_sums[description] = transaction_sums.get(description, 0) + amount
    return transaction_sums

def save_to_csv(transaction_sums, csv_file):
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Description', 'Total Amount'])
        for description, amount in sorted(transaction_sums.items()):
            writer.writerow([description, f"{amount:.2f}"])

def main():
    folder_path = input("Enter the folder path containing the PDF files: ")
    csv_file = input("Enter the output CSV file name: ")
    transactions = []
    files_read = []
    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            file_path = os.path.join(folder_path, file)
            text = read_pdf_file(file_path)
            transactions.extend(extract_transactions(text))
            files_read.append(file)
    transaction_sums = sum_transactions(transactions)
    save_to_csv(transaction_sums, csv_file)
    print("Files read:")
    for file in files_read:
        print(file)

if __name__ == "__main__":
    main()