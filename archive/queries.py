from googleapiclient.discovery import build
import csv
from config import API_KEY, cx


def send_query(query):
    """
    Accepts array of queries and returns array of all responses
    """
    data = []
    for q in query:
        data.append(search(q))
    return data

def save_to_csv(data, filename):
    """
    Extracts specific fields and saves them to a CSV file.
    """
    items = data.get('items', [])
    
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Link", "Snippet"])
        
        for item in items:
            writer.writerow([
                item.get("title"), 
                item.get("link"), 
                item.get("snippet")
            ])

def main():
    identifying_queries = []
    analyzing_queries = []
    data = send_query[identifying_queries]
    save_to_csv(data, "filename")
    