import json
import asyncio
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from queries import analyzing_queries, identifying_queries

# Configuration
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)
SEARCH_ENGINE_BASE_URL = "https://cse.google.com/cse?cx=5686e09ce64f54ca2#gsc.tab=0&gsc.sort=&gsc.q="
PAGES_TO_SCRAPE = 2

async def fetch_search_results(browser, query, target_pages=PAGES_TO_SCRAPE):
    page = await browser.new_page()
    encoded_query = urllib.parse.quote(query)
    target_url = f"{SEARCH_ENGINE_BASE_URL}{encoded_query}"
    html_contents = []
    
    try:
        # Wait until network activity settles for initial load
        await page.goto(target_url, wait_until="networkidle", timeout=30000)
        
        for current_page in range(1, target_pages + 1):               
            html_content = await page.content()
            html_contents.append(html_content)
            
            # Navigate to the next page if not on the final requested page
            if current_page < target_pages:
                next_page_str = str(current_page + 1)
                next_page_locator = page.locator(f'.gsc-cursor-page:has-text("{next_page_str}")').first
                
                if await next_page_locator.count() > 0:
                    await next_page_locator.click()
                    # Wait for network activity to settle after clicking the pagination cursor
                    await page.wait_for_load_state("networkidle")
                    # Optional brief timeout to allow DOM replacement
                    await page.wait_for_timeout(1000) 
                else:
                    break  # Pagination element not found, exit loop early
                
        return html_contents
    except Exception as e:
        print(f"Error executing query '{query}': {e}")
        return html_contents
    finally:
        await page.close()

def parse_serp_to_dict(html_contents, query):
    """
    Parses SERP HTML, extracting relevant search result fields while filtering out images.
    """
    results_data = []
    seen_urls = set()
    
    # Common image extensions and patterns to filter out
    image_filters = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp')

    # Iterate over each HTML page content in the list
    for html_content in html_contents:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Selectors for Google Custom Search Engine (CSE)
        result_blocks = soup.select('.gsc-webResult.gsc-result')

        for block in result_blocks:
            # CSE often has multiple a.gs-title tags per result (e.g., for thumbnails).
            # Iterate through them to find the first one that actually contains text.
            title_elements = block.select('a.gs-title')
            title_element = None
            
            for el in title_elements:
                if el.get_text(strip=True):
                    title_element = el
                    break
                    
            # Skip if no valid text title is found
            if not title_element:
                continue
                
            url = title_element.get('href', "No URL")
            
            # Filter out URLs that point directly to images or Google Image endpoints
            url_lower = url.lower()
            if url_lower.endswith(image_filters) or "imgres?" in url_lower:
                continue

            title = title_element.get_text(strip=True)
            snippet_element = block.select_one('.gs-snippet')
            snippet = snippet_element.get_text(strip=True) if snippet_element else "No Snippet"
            
            if url and url != "No URL" and url not in seen_urls:
                seen_urls.add(url)
                results_data.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet
                })
    
    return {
        "query": query,
        "total_results_extracted": len(results_data),
        "results": results_data
    }

async def main():
    # Define execution targets
    execution_targets = [
        {"file": OUTPUT_DIR / "analyzing.json", "queries": analyzing_queries},
        {"file": OUTPUT_DIR / "identifying.json", "queries": identifying_queries}
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        for target in execution_targets:
            current_queries = target["queries"]
            current_output_file = target["file"]
            extracted_data = []
            
            print(f"--- Starting batch for {current_output_file.name} ---")
            
            for query in current_queries:
                print(f"Executing search for: {query}")
                html_list = await fetch_search_results(browser, query)
                
                if html_list:
                    serp_data = parse_serp_to_dict(html_list, query)
                    extracted_data.append(serp_data)
                    print(f"Extracted {serp_data['total_results_extracted']} total results for '{query}'.")
                    
                # Enforce a delay to respect server load and mitigate rate limiting blocks
                await asyncio.sleep(3)
                
            # Export to JSON
            with open(current_output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)
                
            print(f"Extraction complete. Data saved to {current_output_file}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())