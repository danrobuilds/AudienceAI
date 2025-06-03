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
        self.setup_driver(headless)
        self.scraped_posts = []
        
    def setup_driver(self, headless):
        # Configures Chrome driver options for scraping
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        # Hides the webdriver flag from navigator
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def search_posts(self, keyword, max_posts=50):
        print(f"Searching for posts with keyword: {keyword}")
        
        search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword}&sortBy=%22date_posted%22"
        self.driver.get(search_url)
        
        posts_collected = 0
        scroll_attempts = 0
        max_scrolls = 20
        
        seen_post_ids = set() # Avoids processing duplicate posts during scrolling

        while posts_collected < max_posts and scroll_attempts < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4)) # Random delay to mimic human behavior
            
            # General selector for activity posts
            posts = self.driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2")

            new_posts_found_this_scroll = 0
            for post_element in posts:
                post_id_element = post_element.get_attribute("data-urn")
                if not post_id_element:
                    post_id_element = post_element.get_attribute("id") 
                
                if post_id_element and post_id_element in seen_post_ids:
                    continue 
                
                if post_id_element:
                    seen_post_ids.add(post_id_element)

                if posts_collected >= max_posts:
                    break
                    
                try:
                    post_data = self._extract_post_data_from_search_result(post_element)
                    if post_data and self.meets_criteria(post_data):
                        self.scraped_posts.append(post_data)
                        posts_collected += 1
                        new_posts_found_this_scroll +=1
                        print(f"Collected post {posts_collected}/{max_posts}")
                        
                except Exception as e:
                    print(f"Error extracting post data from search result: {e}")
                    continue
                    
                time.sleep(random.uniform(1, 2)) # Random delay between processing posts
            
            if new_posts_found_this_scroll == 0:
                print("No new posts found in this scroll attempt.")

            scroll_attempts += 1
            if scroll_attempts >= max_scrolls:
                print("Reached max scroll attempts.")
            
        print(f"Finished collecting {len(self.scraped_posts)} posts from search.")

    def scrape_posts_from_urls(self, post_urls):
        print(f"Starting to scrape {len(post_urls)} posts from URLs...")
        for i, url in enumerate(post_urls):
            print(f"Scraping post {i+1}/{len(post_urls)}: {url}")
            self.driver.get(url)
            time.sleep(random.uniform(3, 5)) # Wait for page to load

            try:
                WebDriverWait(self.driver, 20).until(
                    # Common elements indicating a post page has loaded. Adjust if needed.
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
            time.sleep(random.uniform(1, 3)) 
        print(f"Finished scraping {len(self.scraped_posts)} posts from URLs.")


    def _extract_post_data_from_search_result(self, post_element):
        # Extracts data from a post element found in search results.
        post_data = {
            'author_name': '', 'author_headline': '', 'followers': 0,
            'content': '', 'reactions': 0, 'comments': 0, 'shares': 0,
            'post_url': '', 'timestamp': ''
        }
        try:
            author_element = post_element.find_element(By.CSS_SELECTOR, ".update-components-actor__name span[aria-hidden='true']")
            post_data['author_name'] = author_element.text.strip()

            try:
                headline_element = post_element.find_element(By.CSS_SELECTOR, ".update-components-actor__description")
                post_data['author_headline'] = headline_element.text.strip()
            except NoSuchElementException:
                post_data['author_headline'] = "N/A"
            
            try:
                content_element = post_element.find_element(By.CSS_SELECTOR, ".feed-shared-update-v2__description .text-view-model, .feed-shared-text .text-view-model")
                post_data['content'] = content_element.text.strip()
            except NoSuchElementException:
                try:
                    content_element = post_element.find_element(By.CSS_SELECTOR, ".update-components-text")
                    post_data['content'] = content_element.text.strip()
                except NoSuchElementException:
                     post_data['content'] = "N/A"
            
            try:
                social_counts_container = post_element.find_element(By.CSS_SELECTOR, ".social-details-social-counts__social-proof")
                
                try:
                    reactions_element = social_counts_container.find_element(By.CSS_SELECTOR, "button[aria-label*='reaction'], li[class*='reactions'] button")
                    reactions_text = reactions_element.text or reactions_element.get_attribute("aria-label")
                    post_data['reactions'] = self.extract_number_from_text(reactions_text)
                except NoSuchElementException:
                    post_data['reactions'] = 0
                
                try:
                    comments_link = social_counts_container.find_element(By.CSS_SELECTOR, "button[aria-label*='comment'], a[href*='comments']")
                    comments_text = comments_link.text or comments_link.get_attribute("aria-label")
                    post_data['comments'] = self.extract_number_from_text(comments_text)
                except NoSuchElementException:
                     post_data['comments'] = 0

            except NoSuchElementException:
                post_data['reactions'] = 0
                post_data['comments'] = 0

            try:
                post_urn = post_element.get_attribute("data-urn")
                if post_urn: # Construct permalink if URN is available
                    post_data['post_url'] = f"https://www.linkedin.com/feed/update/{post_urn}/"
            except NoSuchElementException:
                post_data['post_url'] = "N/A"

        except Exception as e:
            print(f"Error extracting data from search result post element: {e}")
            return None 
            
        return post_data
        
    def _extract_post_data_from_current_page(self, current_url):
        # Extracts data from the currently loaded single post page.
        post_data = {
            'Unnamed: 0': None, 
            'name': '',
            'headline': '',
            'location': 'N/A', 
            'followers': 0,
            'connections': 0, 
            'about': 'N/A', 
            'time_spent': 'N/A', 
            'content': '', 
            'content_links': current_url, 
            'media_type': 'N/A', 
            'media_url': 'N/A', 
            'num_hashtags': 0, 
            'hashtag_followers': 0, 
            'hashtags': 'N/A', 
            'reactions': 0, 
            'comments': 0, 
            'views': 0, 
            'votes': 0 
        }
        
        try:
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "article, .feed-shared-update-v2, .activity-outlet")) 
            )
        except TimeoutException:
            print("Timeout waiting for main post content on page.")
            return None

        # Candidate selectors for the primary post container
        possible_post_containers = [
            self.driver.find_elements(By.CSS_SELECTOR, "article"),
            self.driver.find_elements(By.CSS_SELECTOR, ".feed-shared-update-v2[data-urn]"), 
            self.driver.find_elements(By.CSS_SELECTOR, ".activity-content.content") 
        ]
        
        post_container = None
        for elements in possible_post_containers:
            if elements:
                post_container = elements[0] 
                break
        
        if not post_container:
            print("Could not find the main post container on the page.")
            return None

        try:
            try:
                author_element = post_container.find_element(By.CSS_SELECTOR, ".update-components-actor__name span[aria-hidden='true'], .actor__name")
                post_data['name'] = author_element.text.strip()
            except NoSuchElementException:
                try: # Fallback for different author structures (e.g., article pages)
                    author_element = post_container.find_element(By.CSS_SELECTOR, "a[data-tracking-control-name*='author'] span[aria-hidden='true']")
                    post_data['name'] = author_element.text.strip()
                except NoSuchElementException:
                     post_data['name'] = "N/A"

            try:
                headline_element = post_container.find_element(By.CSS_SELECTOR, ".update-components-actor__description, .actor__description")
                post_data['headline'] = headline_element.text.strip()
            except NoSuchElementException:
                post_data['headline'] = "N/A"
            
            try:
                content_element = post_container.find_element(By.CSS_SELECTOR, ".feed-shared-update-v2__description .text-view-model, .update-components-text, .article-body")
                post_data['content'] = content_element.text.strip() 
            except NoSuchElementException:
                try: # Fallback for other content structures
                    content_element = post_container.find_element(By.CSS_SELECTOR, ".feed-shared-text__text-view, .break-words") 
                    post_data['content'] = content_element.get_attribute("innerText").strip() 
                except NoSuchElementException:
                    post_data['content'] = "N/A"

            # Locate the social details bar for engagement metrics
            social_bar = None
            social_bar_selectors = [
                "div.feed-shared-social-actions", 
                "div.social-details-social-activity", 
                "div[class*='social-details-social-counts']",
                "ul[class*='social-details-social-counts']" 
            ]
            for selector in social_bar_selectors:
                try:
                    WebDriverWait(post_container, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    social_bar = post_container.find_element(By.CSS_SELECTOR, selector)
                    if social_bar: 
                        break 
                except (NoSuchElementException, TimeoutException):
                    continue
            
            if social_bar: 
                try: # Reactions count
                    reactions_element = social_bar.find_element(By.CSS_SELECTOR, "span[class*='reactions-count']")
                    reactions_text = reactions_element.text.strip()
                except NoSuchElementException:
                    try: # Fallback for reactions
                        reactions_element = social_bar.find_element(By.CSS_SELECTOR, "button[aria-label*='reaction'], span[aria-label*='reaction']")
                        reactions_text = reactions_element.text.strip() or reactions_element.get_attribute("aria-label")
                        if not reactions_text: # Further fallback if text/aria-label is empty
                            try: reactions_text = reactions_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip()
                            except: reactions_text = "0" 
                    except NoSuchElementException:
                        reactions_text = "0"
                post_data['reactions'] = self.extract_number_from_text(reactions_text) 
                
                try: # Comments count
                    comments_element = social_bar.find_element(By.CSS_SELECTOR, "button[class*='social-details-social-counts__comments'], button[data-test-id='comments-button']")
                    comments_text = comments_element.text.strip()
                    if not comments_text: 
                         comments_text = comments_element.get_attribute("aria-label")
                         if not comments_text: # Further fallback
                            try: comments_text = comments_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip()
                            except: comments_text = "0"
                except NoSuchElementException:
                    try: # Fallback for comments
                        comments_element = social_bar.find_element(By.CSS_SELECTOR, "a[href*='#comment'], button[aria-label*='comment']")
                        comments_text = comments_element.text.strip() or comments_element.get_attribute("aria-label")
                        if not comments_text: # Further fallback
                            try: comments_text = comments_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip()
                            except: comments_text = "0"
                    except NoSuchElementException:
                        comments_text = "0"
                post_data['comments'] = self.extract_number_from_text(comments_text) 
            else:
                print(f"Social engagement bar not found for {current_url}. Reactions/comments will be 0.")
                post_data['reactions'] = 0 
                post_data['comments'] = 0 
            
        except Exception as e:
            print(f"Error extracting data from post page {current_url}: {e}")
            return None 
            
        return post_data
    
    def extract_number_from_text(self, text):
        # Extracts number from text like '1,234 reactions' or '1.2K comments'
        import re
        if not text: return 0
        text = text.lower()
        
        multiplier = 1
        if 'k' in text:
            multiplier = 1000
            text = text.replace('k', '')
        elif 'm' in text:
            multiplier = 1000000
            text = text.replace('m', '')

        numbers = re.findall(r'[\d\.,]+', text) # Allows for decimals and commas
        if numbers:
            try:
                num_str = numbers[0].replace(',', '')
                return int(float(num_str) * multiplier)
            except ValueError: # Handles cases where conversion might fail
                return 0 
        return 0
    
    def meets_criteria(self, post_data):
        # Example criteria. Follower count is not available when scraping from direct URLs.
        return (post_data['reactions'] >= 10 and 
                post_data['comments'] >= 2) 
    
    def save_to_csv(self, filename="linkedin_posts.csv"):
        if not self.scraped_posts:
            print("No new posts to save")
            return
            
        df = pd.DataFrame(self.scraped_posts)
        
        # Ensures CSV column order matches the target influencers_data_filtered.csv structure
        csv_column_order = [
            'Unnamed: 0', 'name', 'headline', 'location', 'followers', 'connections', 
            'about', 'time_spent', 'content', 'content_links', 'media_type', 
            'media_url', 'num_hashtags', 'hashtag_followers', 'hashtags', 
            'reactions', 'comments', 'views', 'votes'
        ]
        
        df = df.reindex(columns=csv_column_order) # Reorders/adds columns to match target

        file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0
        
        if file_exists:
            df.to_csv(filename, mode='a', header=False, index=False) # Append if file exists
            print(f"Appended {len(self.scraped_posts)} posts to {filename}")
        else:
            df.to_csv(filename, index=False) # Write new file with header
            print(f"Saved {len(self.scraped_posts)} new posts to {filename}")
        
        self.scraped_posts = [] # Clear list after saving
    
    def close(self):
        if self.driver:
            self.driver.quit()
            print("Browser closed.")

def main():
    print("LinkedIn Post Scraper (URL Mode - No Login)")
    print("WARNING: Scraping may violate LinkedIn's Terms of Service.")
    print("Consider using LinkedIn's official API instead.")
    print("Ensure posts are publicly accessible without login for best results.")
    
    # Hardcoded URLs for initial scraping, enter comma-separated LinkedIn post URLs

    urls_input = "https://www.linkedin.com/posts/ashish-shukla-life-coach_humanresources-career-jobsearch-activity-7334043380038942721-HUK9?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/rbccawang_too-many-students-never-get-the-chance-to-activity-7327755483312730113-C-BX?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_the-perfect-age-to-start-a-startup-isnt-activity-7329128517592301568-WUzw?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_the-paypal-mafia-is-the-best-founding-team-activity-7307747695312404482-3vx4?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_my-co-founder-and-i-live-in-nyc-making-40k-activity-7300152631585296385-wfV6?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_first-i-handed-in-my-notice-then-they-offered-activity-7292180110772760579-GP_m?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_a-year-ago-a-founder-raised-20m-at-a-200m-activity-7290368128721502208-mKeQ?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_last-month-i-watched-a-startups-entire-activity-7288556164114448386-awYy?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_3-months-ago-two-of-my-childhood-best-friends-activity-7285657095926919170-Zs75?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_stanford-has-8054-undergrads-one-of-them-activity-7282395578603323392-mBom?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_since-freshman-year-at-harvard-i-have-changed-activity-7280583641422823424-X0Pn?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_harvard-had-54008-apply-last-year-with-a-activity-7277322130109677568-wzvv?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_on-the-surface-i-have-raised-3m-gotten-activity-7274423150262550528-RTkP?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_last-year-we-got-into-yc-and-raised-3m-activity-7265001442283851776-MH_7?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333896158341156864-1Q1P?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333534379438219266-XTqN?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_this-woman-sold-her-book-club-for-900m-activity-7332808993653829632-AkDl?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333175504436436992-WFAa?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7330638996395491329-IWi5?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7329194790741254145-GgJ1?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7330638996395491329-IWi5?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7323386909169266689-vvXr?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7321966975860047872-MMey?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/olivermolander_artificialintelligence-activity-7332320138823729152-qc6r?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/vatsalppatel_satya-nadella-id-say-maybe-20-30-of-activity-7333556138216456192-Svva?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/manuvanderveeren_incredibly-excited-to-announce-that-we-activity-7333397705320243200-GWGX?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/activity-7324427305412419584-UMsx?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts"
    post_urls = [url.strip() for url in urls_input.split(',') if url.strip()]

    if not post_urls:
        print("No URLs provided for direct scraping.")
    
    output_csv_file = "influencers_data_filtered.csv" 

    scraper = LinkedInScraper(headless=True) # Set headless=True for server/background runs
    
    try:

        if post_urls:
            scraper.scrape_posts_from_urls(post_urls)
            if scraper.scraped_posts: 
                 scraper.save_to_csv(output_csv_file)
            else:
                print("No data was scraped from the provided URLs.")
        
    except Exception as e:
        print(f"An error occurred during the scraping process: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
