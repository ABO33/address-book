import pandas as pd
import csv
import json
import io

def process_csv(file):
    """
    Processes a CSV file and returns a list of dictionaries representing the rows.
    """
    try:
        data = []
        # Wrap the file stream in a text wrapper
        text_stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        csv_reader = csv.DictReader(text_stream)
        for row in csv_reader:
            data.append(row)
        return data
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return None


def process_json(file):
    """
    Processes a JSON file and returns the loaded data.
    """
    try:
        return json.load(file)
    except Exception as e:
        print(f"Error processing JSON: {e}")
        return None


def process_excel(file):
    """
    Processes an Excel file and returns a list of dictionaries representing the rows.
    """
    try:
        data = []
        # Use pandas to read the Excel file
        excel_data = pd.read_excel(file.stream)
        # Convert to a list of dictionaries
        data = excel_data.to_dict(orient='records')
        return data
    except Exception as e:
        print(f"Error processing Excel: {e}")
        return None
