import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd

class LinkedInScraper:
    def __init__(self, headless=False):
        """Initialize the LinkedIn scraper"""
        self.setup_driver(headless)
        self.scraped_posts = []
        
    def setup_driver(self, headless):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login(self, email, password):
        """Login to LinkedIn"""
        print("Logging into LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        
        # Wait for login form
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        # Enter credentials
        self.driver.find_element(By.ID, "username").send_keys(email)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for login to complete
        time.sleep(5)
        print("Login completed")
        
    def search_posts(self, keyword, max_posts=50):
        """Search for posts with specific keywords"""
        print(f"Searching for posts with keyword: {keyword}")
        
        # Navigate to search
        search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword}&sortBy=%22date_posted%22"
        self.driver.get(search_url)
        
        posts_collected = 0
        scroll_attempts = 0
        max_scrolls = 20
        
        while posts_collected < max_posts and scroll_attempts < max_scrolls:
            # Scroll to load more posts
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
            
            # Find all post containers
            posts = self.driver.find_elements(By.CSS_SELECTOR, "[data-id^='urn:li:activity:']")
            
            for post in posts[posts_collected:]:
                if posts_collected >= max_posts:
                    break
                    
                try:
                    post_data = self.extract_post_data(post)
                    if self.meets_criteria(post_data):
                        self.scraped_posts.append(post_data)
                        posts_collected += 1
                        print(f"Collected post {posts_collected}/{max_posts}")
                        
                except Exception as e:
                    print(f"Error extracting post data: {e}")
                    continue
                    
                # Random delay between posts
                time.sleep(random.uniform(1, 2))
            
            scroll_attempts += 1
            
        print(f"Finished collecting {len(self.scraped_posts)} posts")
        
    def extract_post_data(self, post_element):
        """Extract data from a single post"""
        post_data = {
            'author_name': '',
            'author_headline': '',
            'followers': 0,
            'content': '',
            'reactions': 0,
            'comments': 0,
            'shares': 0,
            'post_url': '',
            'timestamp': ''
        }
        
        try:
            # Extract author name
            author_element = post_element.find_element(By.CSS_SELECTOR, ".update-components-actor__name")
            post_data['author_name'] = author_element.text.strip()
            
            # Extract author headline
            try:
                headline_element = post_element.find_element(By.CSS_SELECTOR, ".update-components-actor__description")
                post_data['author_headline'] = headline_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract post content
            try:
                content_element = post_element.find_element(By.CSS_SELECTOR, ".feed-shared-text")
                post_data['content'] = content_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract engagement metrics
            try:
                # Reactions
                reactions_element = post_element.find_element(By.CSS_SELECTOR, "[aria-label*='reaction']")
                reactions_text = reactions_element.get_attribute("aria-label")
                post_data['reactions'] = self.extract_number_from_text(reactions_text)
                
                # Comments
                comments_element = post_element.find_element(By.CSS_SELECTOR, "[aria-label*='comment']")
                comments_text = comments_element.get_attribute("aria-label")
                post_data['comments'] = self.extract_number_from_text(comments_text)
                
            except NoSuchElementException:
                pass
            
            # Get follower count by visiting profile (optional - can be slow)
            # post_data['followers'] = self.get_follower_count(author_profile_url)
            
        except Exception as e:
            print(f"Error extracting post data: {e}")
            
        return post_data
    
    def extract_number_from_text(self, text):
        """Extract number from text like '1,234 reactions'"""
        import re
        numbers = re.findall(r'[\d,]+', text)
        if numbers:
            return int(numbers[0].replace(',', ''))
        return 0
    
    def get_follower_count(self, profile_url):
        """Get follower count from profile (use sparingly)"""
        # This would require navigating to the profile page
        # Implementation would be similar but requires careful rate limiting
        return 0
    
    def meets_criteria(self, post_data):
        """Check if post meets our criteria"""
        return (post_data['reactions'] >= 300 and 
                post_data['followers'] < 10000)  # Note: follower count needs to be implemented
    
    def save_to_csv(self, filename="linkedin_posts.csv"):
        """Save scraped posts to CSV"""
        if not self.scraped_posts:
            print("No posts to save")
            return
            
        df = pd.DataFrame(self.scraped_posts)
        df.to_csv(filename, index=False)
        print(f"Saved {len(self.scraped_posts)} posts to {filename}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

def main():
    """Main function to run the scraper"""
    # WARNING: LinkedIn scraping may violate their Terms of Service
    # Use responsibly and consider LinkedIn's API instead
    
    print("LinkedIn Post Scraper")
    print("WARNING: This may violate LinkedIn's Terms of Service")
    print("Consider using LinkedIn's official API instead")
    
    # Get credentials (you should use environment variables in production)
    email = input("Enter your LinkedIn email: ")
    password = input("Enter your LinkedIn password: ")
    keyword = input("Enter search keyword: ")
    
    scraper = LinkedInScraper(headless=False)
    
    try:
        scraper.login(email, password)
        scraper.search_posts(keyword, max_posts=20)  # Start with small number
        scraper.save_to_csv("scraped_linkedin_posts.csv")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
