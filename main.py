import os
import json
import time
from typing import Dict, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY in .env file")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def setup_driver() -> webdriver.Chrome:
    """Set up and return a Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_subreddit_suggestion(topic: str) -> str:
    """Use Gemini to suggest the most relevant subreddit for a topic."""
    prompt = f"""Given the topic '{topic}', what would be the most active and relevant subreddit to find discussions about it? 
    Return ONLY the subreddit name without 'r/' or any other text."""
    
    response = model.generate_content(prompt)
    return response.text.strip()

def scrape_subreddit(subreddit_name: str) -> Dict:
    """Scrape the top posts from a subreddit."""
    driver = setup_driver()
    subreddit_data = {
        'name': subreddit_name,
        'posts': []
    }
    
    try:
        # Navigate to the subreddit
        url = f'https://www.reddit.com/r/{subreddit_name}/'
        driver.get(url)
        
        # Wait for posts to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="post-container"]'))
        )
        
        # Get post elements
        post_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="post-container"]')[:5]
        
        for post in post_elements:
            try:
                post_data = {
                    'title': post.find_element(By.TAG_NAME, 'h3').text,
                    'upvotes': post.find_element(By.CSS_SELECTOR, '[data-click-id="upvote"]')\
                        .find_element(By.XPATH, "following-sibling::*[1]")\
                        .get_attribute('innerText'),
                    'comments': post.find_element(By.CSS_SELECTOR, '[data-click-id="comments"]')\
                        .get_attribute('innerText').replace(' Comments', '')
                }
                subreddit_data['posts'].append(post_data)
            except NoSuchElementException:
                continue
                
    finally:
        driver.quit()
        
    return subreddit_data

def analyze_posts(subreddit_data: Dict) -> str:
    """Use Gemini to analyze the posts and provide insights."""
    prompt = f"""Analyze these Reddit posts from r/{subreddit_data['name']} and provide a brief summary of the main discussions and trends:
    {json.dumps(subreddit_data['posts'], indent=2)}
    
    Format your response in a clear, concise way with bullet points."""
    
    response = model.generate_content(prompt)
    return response.text

def main():
    """Main function to run the Reddit AI agent."""
    print("\n🤖 Welcome to the Reddit AI Agent!\n")
    
    while True:
        topic = input("\nEnter a topic to analyze (or 'quit' to exit): ").strip()
        if topic.lower() == 'quit':
            break
            
        print("\n🔍 Finding the most relevant subreddit...")
        subreddit = get_subreddit_suggestion(topic)
        print(f"📍 Selected subreddit: r/{subreddit}")
        
        print("\n🌐 Scraping top posts...")
        subreddit_data = scrape_subreddit(subreddit)
        
        if not subreddit_data['posts']:
            print("❌ No posts found. The subreddit might be private or not accessible.")
            continue
            
        print("\n🧠 Analyzing posts...")
        analysis = analyze_posts(subreddit_data)
        
        print("\n📊 Analysis Results:")
        print(analysis)
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main() 