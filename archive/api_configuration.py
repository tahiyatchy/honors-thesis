from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import csv, requests, http
import json


def get_search_results(api_key, search_engine_id, query):
    
    params = {
        'API_KEY': api_key,
        'cx': search_engine_id,
        'q': query
    }

    response = requests.get(url, params=params)

# Execution variables
API_KEY = "AIzaSyDmOAQqFMUHHKweUr4fFQa_4VB_mRVqqxg"
CX = "5686e09ce64f54ca2"
SEARCH_QUERY = "uterus, trimester"

# Fetch and read JSON
results = get_search_results(API_KEY, CX, SEARCH_QUERY)

# Isolate and read the specific search items from the JSON dictionary
"""
if 'items' in results:
    for item in results['items']:
        print(item['title'])
        print(item['link'])
"""