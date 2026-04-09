import json
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Configuration
async def fetch_article_html(browser, url):
    """Fetches the rendered HTML of a target article."""
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return await page.content()
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None
    finally:
        await page.close()

def extract_article_text(html_content):
    """
    Parses HTML to extract sequential heading and paragraph text.
    Uses generic heuristics to locate the main content body.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.extract()
    
    container = soup.select_one('article, main, .post-content, .entry-content, .article-body, .content')
    
    target_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']
    
    if container:
        elements = container.find_all(target_tags)
    else:
        elements = soup.find_all(target_tags)
        
    extracted_parts = []
    
    for el in elements:
        text = el.get_text(strip=True)
        if not text:
            continue
            
        # Append Markdown-style hashes to identify heading levels
        if el.name.startswith('h'):
            level = int(el.name[1])
            extracted_parts.append(f"{'#' * level} {text}")
        else:
            extracted_parts.append(text)
            
    extracted_text = "\n\n".join(extracted_parts)
    
    return extracted_text if extracted_text else "No extractable text found"

async def main():
    for i in range(2):
        if i == 0:
            TARGET_FILE = Path("data/analyzing.json")
        elif i == 1:
            TARGET_FILE = Path("data/identifying.json")
        i+=1
        if not TARGET_FILE.exists():
            print(f"Fatal Error: Target file {TARGET_FILE} not found. Execute the SERP scraper first.")
            continue

        # Load previously extracted SERP data
        with open(TARGET_FILE, 'r', encoding='utf-8') as f:
            serp_data = json.load(f)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )

            for query_block in serp_data:
                print(f"Processing query group: {query_block.get('query')}")
                
                for result in query_block.get('results', []):
                    url = result.get('url')
                    
                    if not url or url == "No URL" or not url.startswith('http'):
                        result['full_article_text'] = "Invalid URL"
                        continue
                    
                    print(f"  Fetching: {url}")
                    html = await fetch_article_html(browser, url)
                    
                    if html:
                        result['full_article_text'] = extract_article_text(html)
                    else:
                        result['full_article_text'] = "Failed to fetch document"
                        
                    await asyncio.sleep(2)

            await browser.close()

        # Overwrite the exact target file with the augmented data
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            json.dump(serp_data, f, indent=4, ensure_ascii=False)

        print(f"Deep scraping complete. Augmented data saved to {TARGET_FILE}")

if __name__ == "__main__":
    asyncio.run(main())