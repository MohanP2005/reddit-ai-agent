from flask import Flask, render_template, request, jsonify
import os
import json
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

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY in .env file")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

def setup_driver():
    """Set up and return a Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_subreddit_suggestion(topic: str) -> str:
    """Use Gemini to suggest the most relevant subreddit for a topic."""
    prompt = f"""Given the topic '{topic}', what would be the most active and relevant subreddit to find discussions about it? 
    Return ONLY the subreddit name without 'r/' or any other text."""
    
    response = model.generate_content(prompt)
    return response.text.strip()

def scrape_subreddit(subreddit_name: str) -> dict:
    """Scrape the top posts from a subreddit."""
    driver = setup_driver()
    subreddit_data = {
        'name': subreddit_name,
        'posts': []
    }
    
    try:
        url = f'https://old.reddit.com/r/{subreddit_name}/'
        driver.get(url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "thing"))
        )
        
        post_elements = driver.find_elements(By.CLASS_NAME, "thing")[:5]
        
        for post in post_elements:
            try:
                title_element = post.find_element(By.CLASS_NAME, "title")
                title = title_element.text
                url = title_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                score = post.find_element(By.CLASS_NAME, "score").text
                comments = post.find_element(By.CLASS_NAME, "comments").text.split()[0]
                
                post_data = {
                    'title': title,
                    'url': url,
                    'upvotes': score if score != "•" else "hidden",
                    'comments': comments
                }
                subreddit_data['posts'].append(post_data)
            except NoSuchElementException:
                continue
            except Exception as e:
                print(f"Error processing post: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error accessing subreddit: {str(e)}")
    finally:
        driver.quit()
        
    return subreddit_data

def analyze_posts(subreddit_data: dict) -> str:
    """Use Gemini to analyze the posts and provide insights."""
    prompt = f"""Analyze these Reddit posts from r/{subreddit_data['name']} and provide a brief summary of the main discussions and trends.
    For each point in your analysis, include the relevant post title and its URL.
    
    Posts data:
    {json.dumps(subreddit_data['posts'], indent=2)}
    
    Format your response in a clear, concise way with bullet points. For each point, make sure to include the post URL as a reference."""
    
    response = model.generate_content(prompt)
    return response.text

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    topic = request.json.get('topic')
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400
    
    try:
        # Get subreddit suggestion
        subreddit = get_subreddit_suggestion(topic)
        
        # Scrape posts
        subreddit_data = scrape_subreddit(subreddit)
        
        if not subreddit_data['posts']:
            return jsonify({
                'error': 'No posts found. The subreddit might be private or not accessible.'
            }), 404
        
        # Analyze posts
        analysis = analyze_posts(subreddit_data)
        
        return jsonify({
            'subreddit': subreddit,
            'analysis': analysis,
            'raw_data': subreddit_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8000) 