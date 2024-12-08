import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse

class HubSpotGuideCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited_urls = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

    def fetch_page(self, url):
        if url in self.visited_urls:
            return None

        self.visited_urls.add(url)

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # More aggressive content extraction
            content_selectors = [
                'main', 
                'article', 
                'div.content', 
                'body', 
                '#main-content',
                'div[role="main"]'
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # Extract links
            links = [
                urljoin(url, a['href']) 
                for a in soup.find_all('a', href=True) 
                if a['href'].startswith('/') or a['href'].startswith('https://developers.hubspot.com')
            ]
            
            return {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'content': main_content.get_text(strip=True, separator=' ') if main_content else '',
                'links': links
            }
        
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def crawl(self, max_pages=50):
        pages = []
        to_visit = [self.base_url]
        
        while to_visit and len(pages) < max_pages:
            current_url = to_visit.pop(0)
            page_info = self.fetch_page(current_url)
            
            if page_info:
                pages.append(page_info)
                
                # Add new links to visit
                for link in page_info.get('links', []):
                    if (link not in self.visited_urls and 
                        '/beta-docs/guides' in link and 
                        link not in to_visit):
                        to_visit.append(link)
        
        return pages

def main():
    base_url = 'https://developers.hubspot.com/beta-docs/guides'
    crawler = HubSpotGuideCrawler(base_url)
    results = crawler.crawl()

    # Save to JSON
    with open('hubspot_guides_content.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Crawled {len(results)} pages. Content saved to hubspot_guides_content.json")

if __name__ == "__main__":
    main()