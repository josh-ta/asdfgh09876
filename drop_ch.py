from bs4 import BeautifulSoup
from seleniumbase import SB
import random
from urllib.parse import urlparse


class DropCH:
    def __init__(self, url: str):
        self.url = url
        self.event_id = self.extract_event_id()
        self.count = 0
        self.sections = []
       

    def extract_event_id(self):
        parsed_url = urlparse(self.url)
        return parsed_url.path.split('/')[-1]
    
    def extract_availability(self, html):
        soup = BeautifulSoup(html, "html.parser")
            
        sections = [
            el.get("data-section-name")
            for el in soup.select('path[data-component="svg__section"][data-active="true"]')
            if el.get("data-section-name")
            ]
        
        return list(set(sections))

    def run(self):
        with SB(uc=True, ad_block=True, headless=True) as sb:
            sb.activate_cdp_mode(self.url)
            sb.wait_for_element("#map-container > div > div > svg")
            sb.sleep(random.uniform(0.5,0.9))
            
            try:
                sb.wait_for_element_present("#onetrust-banner-sdk", timeout=random.uniform(0.4,0.6))
                sb.remove_element("#onetrust-banner-sdk")
            except:
                pass
            
            sb.sleep(random.uniform(0.5,0.9))

            html = sb.get_html()
            sections = self.extract_availability(html)
            if sections:
                self.sections = sections
                self.count = len(sections)

            sb.save_screenshot(f"{self.event_id}.png", folder="Screenshots")
    