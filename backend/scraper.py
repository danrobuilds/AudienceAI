import time
import csv
import random
import os
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
        
    def search_posts(self, keyword, max_posts=50):
        """Search for posts with specific keywords"""
        print(f"Searching for posts with keyword: {keyword}")
        
        # Navigate to search
        search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword}&sortBy=%22date_posted%22"
        self.driver.get(search_url)
        
        posts_collected = 0
        scroll_attempts = 0
        max_scrolls = 20
        
        # Store seen post IDs to avoid duplicates if any during scrolling
        seen_post_ids = set()

        while posts_collected < max_posts and scroll_attempts < max_scrolls:
            # Scroll to load more posts
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
            
            # Find all post containers
            # Using a more general selector for activity posts
            posts = self.driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2")

            new_posts_found_this_scroll = 0
            for post_element in posts:
                post_id_element = post_element.get_attribute("data-urn") # A common attribute for post URNs
                if not post_id_element: # Try another common attribute if the first is not found
                    post_id_element = post_element.get_attribute("id") 
                
                if post_id_element and post_id_element in seen_post_ids:
                    continue # Skip already processed post
                
                if post_id_element:
                    seen_post_ids.add(post_id_element)

                if posts_collected >= max_posts:
                    break
                    
                try:
                    # Pass the driver to extract_post_data if it needs to interact further with the page for this post
                    post_data = self._extract_post_data_from_search_result(post_element)
                    if post_data and self.meets_criteria(post_data): # Ensure post_data is not None
                        self.scraped_posts.append(post_data)
                        posts_collected += 1
                        new_posts_found_this_scroll +=1
                        print(f"Collected post {posts_collected}/{max_posts}")
                        
                except Exception as e:
                    print(f"Error extracting post data from search result: {e}")
                    continue
                    
                # Random delay between posts
                time.sleep(random.uniform(1, 2))
            
            if new_posts_found_this_scroll == 0:
                print("No new posts found in this scroll attempt.")

            scroll_attempts += 1
            if scroll_attempts >= max_scrolls:
                print("Reached max scroll attempts.")
            
        print(f"Finished collecting {len(self.scraped_posts)} posts from search.")

    def scrape_posts_from_urls(self, post_urls):
        """Scrape data from a list of LinkedIn post URLs."""
        print(f"Starting to scrape {len(post_urls)} posts from URLs...")
        for i, url in enumerate(post_urls):
            print(f"Scraping post {i+1}/{len(post_urls)}: {url}")
            self.driver.get(url)
            time.sleep(random.uniform(3, 5)) # Wait for page to load

            try:
                WebDriverWait(self.driver, 20).until(
                    # Wait for a common element that indicates a post page has loaded
                    # This selector might need adjustment based on actual post page structure
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-shared-update-v2, .main-feed__container, article")) 
                )
                post_data = self._extract_post_data_from_current_page(url)
                if post_data:
                    self.scraped_posts.append(post_data)
                    print(f"Successfully scraped: {url}")
                else:
                    print(f"Could not extract data for: {url}")
            except TimeoutException:
                print(f"Timeout loading post page: {url}")
            except Exception as e:
                print(f"Error scraping post {url}: {e}")
            time.sleep(random.uniform(1, 3)) # Delay between requests
        print(f"Finished scraping {len(self.scraped_posts)} posts from URLs.")


    def _extract_post_data_from_search_result(self, post_element):
        """Extract data from a single post element found in search results."""
        post_data = {
            'author_name': '', 'author_headline': '', 'followers': 0,
            'content': '', 'reactions': 0, 'comments': 0, 'shares': 0,
            'post_url': '', 'timestamp': ''
        }
        try:
            # Extract author name
            # More robust selector for actor name
            author_element = post_element.find_element(By.CSS_SELECTOR, ".update-components-actor__name span[aria-hidden='true']")
            post_data['author_name'] = author_element.text.strip()

            # Extract author headline
            try:
                # More robust selector for actor description/headline
                headline_element = post_element.find_element(By.CSS_SELECTOR, ".update-components-actor__description")
                post_data['author_headline'] = headline_element.text.strip()
            except NoSuchElementException:
                post_data['author_headline'] = "N/A"
            
            # Extract post content
            try:
                # Selector for feed shared text content
                content_element = post_element.find_element(By.CSS_SELECTOR, ".feed-shared-update-v2__description .text-view-model, .feed-shared-text .text-view-model")
                post_data['content'] = content_element.text.strip()
            except NoSuchElementException:
                # Fallback for other content structures
                try:
                    content_element = post_element.find_element(By.CSS_SELECTOR, ".update-components-text")
                    post_data['content'] = content_element.text.strip()
                except NoSuchElementException:
                     post_data['content'] = "N/A"
            
            # Extract engagement metrics (Reactions, Comments)
            # These selectors are for typical feed items.
            try:
                # Combined selector for social detail counts
                social_counts_container = post_element.find_element(By.CSS_SELECTOR, ".social-details-social-counts__social-proof")
                
                try:
                    reactions_element = social_counts_container.find_element(By.CSS_SELECTOR, "button[aria-label*='reaction'], li[class*='reactions'] button")
                    # Extracting number from the button's text or aria-label.
                    # This might need adjustment based on how LinkedIn displays this.
                    reactions_text = reactions_element.text or reactions_element.get_attribute("aria-label")
                    post_data['reactions'] = self.extract_number_from_text(reactions_text)
                except NoSuchElementException:
                    post_data['reactions'] = 0
                
                try:
                    # A more specific selector for comments count might be needed.
                    # This targets a button that often displays comment counts.
                    comments_link = social_counts_container.find_element(By.CSS_SELECTOR, "button[aria-label*='comment'], a[href*='comments']")
                    comments_text = comments_link.text or comments_link.get_attribute("aria-label")
                    post_data['comments'] = self.extract_number_from_text(comments_text)
                except NoSuchElementException:
                     post_data['comments'] = 0

            except NoSuchElementException:
                post_data['reactions'] = 0
                post_data['comments'] = 0

            # Post URL - Attempt to find a permalink
            try:
                # permalink_element = post_element.find_element(By.CSS_SELECTOR, "a.feed-shared-update-v2__control-menu")
                # if permalink_element:
                #     post_data['post_url'] = permalink_element.get_attribute('href') # This might not be the direct permalink
                # Heuristic: If data-urn is available, construct a possible permalink
                post_urn = post_element.get_attribute("data-urn")
                if post_urn:
                    post_data['post_url'] = f"https://www.linkedin.com/feed/update/{post_urn}/"
            except NoSuchElementException:
                post_data['post_url'] = "N/A"

        except Exception as e:
            print(f"Error extracting data from search result post element: {e}")
            return None # Return None if essential data cannot be extracted
            
        return post_data
        
    def _extract_post_data_from_current_page(self, current_url):
        """Extract data from the currently loaded single post page."""
        # Updated to match the exact CSV structure provided by the user
        post_data = {
            'Unnamed: 0': None,
            'name': '',
            'headline': '',
            'location': 'N/A', # User confirmed lowercase, default N/A
            'followers': 0,
            'connections': 0, # Placeholder
            'about': 'N/A', # Placeholder
            'time_spent': 'N/A', # Placeholder
            'content': '', # User confirmed this key for post text
            'content_links': current_url, # URL of the post
            'media_type': 'N/A', # Placeholder
            'media_url': 'N/A', # Placeholder
            'num_hashtags': 0, # Placeholder
            'hashtag_followers': 0, # Placeholder
            'hashtags': 'N/A', # Placeholder
            'reactions': 0, # User confirmed this key
            'comments': 0, # User confirmed this key
            'views': 0, # Placeholder
            'votes': 0 # Placeholder
        }
        
        # Wait for the main content of the post to be visible
        # This selector should target a unique container for the post details on its own page.
        # It's often an <article> tag or a div with a specific role or class.
        try:
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "article, .feed-shared-update-v2, .activity-outlet")) # General selectors for post container
            )
        except TimeoutException:
            print("Timeout waiting for main post content on page.")
            return None

        # Try to find the primary post container
        # These are candidate selectors. The actual one might vary.
        possible_post_containers = [
            self.driver.find_elements(By.CSS_SELECTOR, "article"),
            self.driver.find_elements(By.CSS_SELECTOR, ".feed-shared-update-v2[data-urn]"), # More specific if URN is present
            self.driver.find_elements(By.CSS_SELECTOR, ".activity-content.content") # Another common pattern
        ]
        
        post_container = None
        for elements in possible_post_containers:
            if elements:
                post_container = elements[0] # Use the first one found
                break
        
        if not post_container:
            print("Could not find the main post container on the page.")
            return None

        try:
            # Extract author name
            # Look for elements like '.actor-name', '.update-components-actor__name', or similar within the post_container
            try:
                author_element = post_container.find_element(By.CSS_SELECTOR, ".update-components-actor__name span[aria-hidden='true'], .actor__name")
                post_data['name'] = author_element.text.strip()
            except NoSuchElementException:
                # Fallback for cases where the structure is different, e.g. on article pages
                try:
                    author_element = post_container.find_element(By.CSS_SELECTOR, "a[data-tracking-control-name*='author'] span[aria-hidden='true']")
                    post_data['name'] = author_element.text.strip()
                except NoSuchElementException:
                     post_data['name'] = "N/A"


            # Extract author headline
            try:
                headline_element = post_container.find_element(By.CSS_SELECTOR, ".update-components-actor__description, .actor__description")
                post_data['headline'] = headline_element.text.strip()
            except NoSuchElementException:
                post_data['headline'] = "N/A"
            
            # Extract post content
            # This selector needs to be robust for different post types (text, article, image with text)
            try:
                content_element = post_container.find_element(By.CSS_SELECTOR, ".feed-shared-update-v2__description .text-view-model, .update-components-text, .article-body")
                post_data['content'] = content_element.text.strip() # Key confirmed by user
            except NoSuchElementException:
                # Fallback for other content structures if the above fails
                try:
                    content_element = post_container.find_element(By.CSS_SELECTOR, ".feed-shared-text__text-view, .break-words") # Common classes for post text
                    post_data['content'] = content_element.get_attribute("innerText").strip() # Key confirmed by user
                except NoSuchElementException:
                    post_data['content'] = "N/A"

            # Extract engagement metrics (Reactions, Comments)
            # Locate the social details bar first
            social_bar = None
            social_bar_selectors = [
                "div.feed-shared-social-actions", 
                "div.social-details-social-activity", 
                "div[class*='social-details-social-counts']",
                "ul[class*='social-details-social-counts']" # Common container for counts
            ]
            for selector in social_bar_selectors:
                try:
                    WebDriverWait(post_container, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    social_bar = post_container.find_element(By.CSS_SELECTOR, selector)
                    if social_bar: # Found a social bar
                        break 
                except (NoSuchElementException, TimeoutException):
                    continue
            
            if social_bar: 
                # Reactions within the social bar
                try:
                    # Try a very specific class for reaction counts first
                    reactions_element = social_bar.find_element(By.CSS_SELECTOR, "span[class*='reactions-count']")
                    reactions_text = reactions_element.text.strip()
                except NoSuchElementException:
                    # Fallback to buttons or spans with aria-label
                    try:
                        reactions_element = social_bar.find_element(By.CSS_SELECTOR, "button[aria-label*='reaction'], span[aria-label*='reaction']")
                        reactions_text = reactions_element.text.strip() or reactions_element.get_attribute("aria-label")
                        if not reactions_text:
                            try: reactions_text = reactions_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip()
                            except: reactions_text = "0" # ensure it's a string for extract_number
                    except NoSuchElementException:
                        reactions_text = "0"
                post_data['reactions'] = self.extract_number_from_text(reactions_text) # Key confirmed by user
                
                # Comments within the social bar
                try:
                    # Try a specific class for comments count, often on a button
                    comments_element = social_bar.find_element(By.CSS_SELECTOR, "button[class*='social-details-social-counts__comments'], button[data-test-id='comments-button']")
                    comments_text = comments_element.text.strip()
                    if not comments_text: # If button text is empty, check aria-label or inner span
                         comments_text = comments_element.get_attribute("aria-label")
                         if not comments_text:
                            try: comments_text = comments_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip()
                            except: comments_text = "0"
                except NoSuchElementException:
                    # Fallback to other common patterns for comments link/button
                    try:
                        comments_element = social_bar.find_element(By.CSS_SELECTOR, "a[href*='#comment'], button[aria-label*='comment']")
                        comments_text = comments_element.text.strip() or comments_element.get_attribute("aria-label")
                        if not comments_text:
                            try: comments_text = comments_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip()
                            except: comments_text = "0"
                    except NoSuchElementException:
                        comments_text = "0"
                post_data['comments'] = self.extract_number_from_text(comments_text) # Key confirmed by user
            else:
                print(f"Social engagement bar not found for {current_url}. Reactions/comments will be 0.")
                post_data['reactions'] = 0 # Key confirmed by user
                post_data['comments'] = 0 # Key confirmed by user
            
        except Exception as e:
            print(f"Error extracting data from post page {current_url}: {e}")
            return None # Return None if there's an issue
            
        return post_data
    
    def extract_number_from_text(self, text):
        """Extract number from text like '1,234 reactions' or '1.2K comments'."""
        import re
        if not text: return 0
        text = text.lower()
        
        # Handle K for thousands, M for millions
        multiplier = 1
        if 'k' in text:
            multiplier = 1000
            text = text.replace('k', '')
        elif 'm' in text:
            multiplier = 1000000
            text = text.replace('m', '')

        # Remove non-numeric characters except for comma and period (for decimals)
        numbers = re.findall(r'[\d\.,]+', text)
        if numbers:
            try:
                # Take the first number found, remove commas, convert to float (for K/M cases), then int
                num_str = numbers[0].replace(',', '')
                return int(float(num_str) * multiplier)
            except ValueError:
                return 0 # In case of conversion error
        return 0
    
    def get_follower_count(self, profile_url):
        """Get follower count from profile (use sparingly - not used in URL scraping mode)"""
        # This would require navigating to the profile page
        # Implementation would be similar but requires careful rate limiting
        return 0 # Placeholder
    
    def meets_criteria(self, post_data):
        """Check if post meets our criteria (Not directly used in URL scraping mode, but kept for potential reuse)"""
        # Example criteria, can be adjusted. Follower count is not available in URL scraping.
        return (post_data['reactions'] >= 10 and 
                post_data['comments'] >= 2) 
    
    def save_to_csv(self, filename="linkedin_posts.csv"):
        """Save or append scraped posts to CSV"""
        if not self.scraped_posts:
            print("No new posts to save")
            return
            
        df = pd.DataFrame(self.scraped_posts)
        
        # Define the target CSV column order to match influencers_data_filtered.csv
        # This is the exact order provided by the user
        csv_column_order = [
            'Unnamed: 0', 'name', 'headline', 'location', 'followers', 'connections', 
            'about', 'time_spent', 'content', 'content_links', 'media_type', 
            'media_url', 'num_hashtags', 'hashtag_followers', 'hashtags', 
            'reactions', 'comments', 'views', 'votes'
        ]
        
        # Reorder DataFrame columns to match the CSV structure
        # This ensures correct alignment when appending without headers.
        # Columns in csv_column_order not in df will be added as NaN.
        # Columns in df not in csv_column_order will be dropped.
        df = df.reindex(columns=csv_column_order)

        # Check if file exists to append or write new
        file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0
        
        if file_exists:
            # Append without header
            df.to_csv(filename, mode='a', header=False, index=False)
            print(f"Appended {len(self.scraped_posts)} posts to {filename}")
        else:
            # Write new file with header
            df.to_csv(filename, index=False)
            print(f"Saved {len(self.scraped_posts)} new posts to {filename}")
        
        # Clear the list after saving to avoid duplicates if called multiple times
        self.scraped_posts = [] 
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed.")

def main():
    """Main function to run the scraper"""
    print("LinkedIn Post Scraper (URL Mode - No Login)")
    print("WARNING: Scraping may violate LinkedIn's Terms of Service.")
    print("Consider using LinkedIn's official API instead.")
    print("Ensure posts are publicly accessible without login for best results.")
    
    # urls_input = input("Enter comma-separated LinkedIn post URLs: ")
    urls_input = "https://www.linkedin.com/posts/ashish-shukla-life-coach_humanresources-career-jobsearch-activity-7334043380038942721-HUK9?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/rbccawang_too-many-students-never-get-the-chance-to-activity-7327755483312730113-C-BX?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_the-perfect-age-to-start-a-startup-isnt-activity-7329128517592301568-WUzw?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_the-paypal-mafia-is-the-best-founding-team-activity-7307747695312404482-3vx4?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_my-co-founder-and-i-live-in-nyc-making-40k-activity-7300152631585296385-wfV6?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_first-i-handed-in-my-notice-then-they-offered-activity-7292180110772760579-GP_m?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_a-year-ago-a-founder-raised-20m-at-a-200m-activity-7290368128721502208-mKeQ?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_last-month-i-watched-a-startups-entire-activity-7288556164114448386-awYy?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_3-months-ago-two-of-my-childhood-best-friends-activity-7285657095926919170-Zs75?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_stanford-has-8054-undergrads-one-of-them-activity-7282395578603323392-mBom?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_since-freshman-year-at-harvard-i-have-changed-activity-7280583641422823424-X0Pn?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_harvard-had-54008-apply-last-year-with-a-activity-7277322130109677568-wzvv?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_on-the-surface-i-have-raised-3m-gotten-activity-7274423150262550528-RTkP?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_last-year-we-got-into-yc-and-raised-3m-activity-7265001442283851776-MH_7?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333896158341156864-1Q1P?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333534379438219266-XTqN?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_this-woman-sold-her-book-club-for-900m-activity-7332808993653829632-AkDl?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333175504436436992-WFAa?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7330638996395491329-IWi5?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7329194790741254145-GgJ1?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7330638996395491329-IWi5?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7323386909169266689-vvXr?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7321966975860047872-MMey?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/olivermolander_artificialintelligence-activity-7332320138823729152-qc6r?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/vatsalppatel_satya-nadella-id-say-maybe-20-30-of-activity-7333556138216456192-Svva?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/manuvanderveeren_incredibly-excited-to-announce-that-we-activity-7333397705320243200-GWGX?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/activity-7324427305412419584-UMsx?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts"
    post_urls = [url.strip() for url in urls_input.split(',') if url.strip()]

    if not post_urls:
        print("No URLs provided. Exiting.")
        return

    output_csv_file = "influencers_data_filtered.csv" # Target CSV file

    scraper = LinkedInScraper(headless=False) # Consider headless=True for non-interactive runs
    
    try:
        scraper.scrape_posts_from_urls(post_urls)
        if scraper.scraped_posts: # Check if any posts were actually scraped
             scraper.save_to_csv(output_csv_file)
        else:
            print("No data was scraped from the provided URLs.")
        
    except Exception as e:
        print(f"An error occurred during the scraping process: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
