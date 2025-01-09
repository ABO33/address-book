import csv
import json

def process_csv(file):
    try:
        data = []
        csv_reader = csv.DictReader(file.stream.decode('utf-8').splitlines())
        for row in csv_reader:
            data.append(row)
        return data
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return None

def process_json(file):
    try:
        return json.load(file)
    except Exception as e:
        print(f"Error processing JSON: {e}")
        return None
