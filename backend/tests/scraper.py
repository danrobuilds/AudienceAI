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
import requests
import base64
from langchain_ollama import ChatOllama

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
        
        # Add options to prevent login persistence
        chrome_options.add_argument("--incognito")  # Use incognito mode
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        # Note: NOT disabling JavaScript as it's needed for LinkedIn functionality
        
        self.driver = webdriver.Chrome(options=chrome_options)
        # Hides the webdriver flag from navigator
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Clear any existing cookies/session data
        self.clear_browser_data()
        
    def clear_browser_data(self):
        """Clear cookies and local storage to ensure no login session exists"""
        try:
            # Navigate to LinkedIn first to set the domain context
            self.driver.get("https://www.linkedin.com")
            time.sleep(2)
            
            # Clear all cookies
            self.driver.delete_all_cookies()
            
            # Clear local storage and session storage
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            
            print("Browser data cleared - ensuring no login session exists")
            
        except Exception as e:
            print(f"Warning: Could not clear browser data: {e}")
    
    def verify_not_logged_in(self):
        """Verify that we're not logged in by checking for login indicators"""
        try:
            self.driver.get("https://www.linkedin.com")
            time.sleep(3)
            
            # Check for login indicators
            login_indicators = [
                "Sign in",
                "Join now", 
                "sign-in-form",
                "login-form"
            ]
            
            page_source = self.driver.page_source.lower()
            
            logged_in_indicators = [
                "feed-identity-module",
                "global-nav__me",
                "nav-item__profile-member-photo"
            ]
            
            is_logged_in = any(indicator in page_source for indicator in logged_in_indicators)
            has_login_form = any(indicator in page_source for indicator in login_indicators)
            
            if is_logged_in:
                print("⚠️  WARNING: You appear to be logged in! This may violate LinkedIn's TOS.")
                print("Please log out of LinkedIn in all browser windows and clear browser data.")
                return False
            elif has_login_form:
                print("✅ Confirmed: Not logged in - login form detected")
                return True
            else:
                print("⚠️  Cannot determine login status - proceed with caution")
                return True
                
        except Exception as e:
            print(f"Could not verify login status: {e}")
            return True
    
    def scrape_raw_content_from_urls(self, post_urls):
        """Phase 1: Scrape raw content and image URLs (no LLM processing)"""
        print(f"🔍 Phase 1: Scraping raw content from {len(post_urls)} URLs...")
        
        for i, url in enumerate(post_urls):
            print(f"📄 Scraping raw content {i+1}/{len(post_urls)}: {url}")
            
            try:
                self.driver.get(url)
                time.sleep(random.uniform(3, 5))

                # Wait for page to load and extract content
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".break-words"))
                )
                
                content_element = self.driver.find_element(By.CSS_SELECTOR, ".break-words")
                content = content_element.text.strip()
                
                # Find images in the post
                image_urls = []
                try:
                    img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='licdn.com']")
                    print(f"📸 Found {len(img_elements)} LinkedIn images")
                    
                    for img in img_elements:
                        src = img.get_attribute('src')
                        
                        # Only capture actual post content images
                        if src and ('feedshare' in src or 'media-exp' in src or 
                                   ('dms/image' in src and 'aero-v1' not in src and 'profile-displaybackgroundimage' not in src and 'profile-displayphoto' not in src and 'comment-image-shrink' not in src and 'article-cover_image-shrink' not in src)):
                            image_urls.append(src)
                            print(f"✓ Found post content image: {src}")
                            
                except Exception as e:
                    print(f"⚠️ Error finding images: {e}")
                
                # Store raw post data (no LLM processing yet)
                raw_post_data = {
                    'content': content,
                    'content_url': url,
                    'image_urls': image_urls[0] if image_urls else '',  # First image URL only
                    'processing_status': 'raw'
                }
                
                self.scraped_posts.append(raw_post_data)
                print(f"✅ Successfully scraped raw content: {url}")
                
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
                # Add failed entry to track issues
                failed_post_data = {
                    'content': f"ERROR: Failed to scrape - {str(e)}",
                    'content_url': url,
                    'image_urls': '',
                    'processing_status': 'failed'
                }
                self.scraped_posts.append(failed_post_data)
                
            time.sleep(random.uniform(1, 3))
        
        print(f"📊 Phase 1 Complete: Scraped {len(self.scraped_posts)} posts")
    
    def save_raw_data_to_csv(self, filename="raw_linkedin_posts.csv"):
        """Save raw scraped data to intermediate CSV"""
        if not self.scraped_posts:
            print("⚠️ No raw data to save")
            return
            
        df = pd.DataFrame(self.scraped_posts)
        
        # Raw CSV column order
        raw_csv_columns = ['content', 'content_url', 'image_urls', 'processing_status']
        df = df.reindex(columns=raw_csv_columns)

        df.to_csv(filename, index=False)
        print(f"💾 Saved {len(self.scraped_posts)} raw posts to {filename}")
        
        # Clear scraped posts after saving
        self.scraped_posts = []
    
    def process_raw_data_with_llms(self, raw_csv_filename="raw_linkedin_posts.csv"):
        """Phase 2: Process raw data with LLMs to generate descriptions and target audiences"""
        print(f"🤖 Phase 2: Processing raw data with LLMs...")
        
        # Load raw data
        try:
            df = pd.read_csv(raw_csv_filename)
            print(f"📂 Loaded {len(df)} raw posts from {raw_csv_filename}")
        except Exception as e:
            print(f"❌ Error loading raw data: {e}")
            return
        
        processed_posts = []
        
        for i, row in df.iterrows():
            if row['processing_status'] == 'failed':
                print(f"⏭️ Skipping failed post: {row['content_url']}")
                continue
                
            print(f"🔬 Processing post {i+1}/{len(df)}: {row['content_url']}")
            
            content = row['content']
            # Handle NaN values from pandas (which are float) and empty strings
            image_url = row['image_urls'] if pd.notna(row['image_urls']) else ''
            image_urls = [image_url] if image_url else []  # Single image URL or empty list
            
            # Process images with LLava
            image_descriptions = []
            for img_url in image_urls:
                if img_url.strip():
                    try:
                        description = self.get_contextual_image_description(img_url.strip(), content)
                        if description:
                            image_descriptions.append(description)
                            print(f"✓ Generated image description: {description[:100]}...")
                    except Exception as e:
                        print(f"⚠️ Error processing image {img_url}: {e}")
            
            # Generate target audience with Llama
            media_description = ' | '.join(image_descriptions) if image_descriptions else ''
            target_audience = self.analyze_target_audience(content, media_description)
            
            # Create final post data
            processed_post = {
                'target_audience': target_audience,
                'content': content,
                'content_url': row['content_url'],
                'media_description': media_description
            }
            
            processed_posts.append(processed_post)
            print(f"✅ Successfully processed: {row['content_url']}")
            
            # Small delay between LLM calls
            time.sleep(random.uniform(1, 2))
        
        print(f"🎉 Phase 2 Complete: Processed {len(processed_posts)} posts with LLMs")
        return processed_posts

    def analyze_target_audience(self, post_content, image_descriptions):
        """Analyze post content and contextual image descriptions to determine target audience"""
        try:
            # Initialize Ollama text model
            llm = ChatOllama(
                model="llama3.1:8b",  # Fast text model for analysis
            )
            
            from langchain_core.messages import HumanMessage
            
            analysis_prompt = f"""
            Analyze this LinkedIn post content and contextual image descriptions to determine the target audience in a few sentences:

            Post Content:
            {post_content}

            Contextual Image Descriptions:
            {image_descriptions}

            Based on the content, tone, hashtags, and visual context, identify the specific target audience. Consider:
            - Professional level 
            - Industry focus and sector
            - Job functions or roles
            - Career stage and aspirations
            - Specific interests or pain points being addressed
            - How the visual content supports the messaging
            - What type of professional would find this content valuable

            Provide a detailed target audience description in NO MORE THAN a few sentences. Focus on who would find this content most valuable and actionable.

            NO PREAMBLE OR CONVERSATIONAL FILLER. JUST THE TARGET AUDIENCE DESCRIPTION ITSELF.
            """
            
            message = HumanMessage(content=analysis_prompt)
            
            print("🎯 Analyzing target audience...")
            result = llm.invoke([message])
            
            target_audience = result.content.strip()
            print(f"✓ Target audience identified: {target_audience}")
            return target_audience
                
        except Exception as e:
            print(f"❌ Error analyzing target audience: {e}")
            return "LinkedIn professionals"

    def get_contextual_image_description(self, image_url, post_content):
        """Generate a contextual description for an image using post content"""
        try:
            # Download the image
            print(f"🖼️ Processing image: {image_url[:50]}...")
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                print(f"❌ Failed to download image: {response.status_code}")
                return None
            
            # Convert image to base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            # Initialize Ollama vision model
            llm = ChatOllama(
                model="llava:7b",  # Smaller, faster vision model
                temperature=0.1
            )
            
            # Create contextual message with image
            from langchain_core.messages import HumanMessage
            
            contextual_prompt = f"""
            Analyze this image in the context of the LinkedIn post content:

            Post Content:
            {post_content}

            Please provide a brief, but detailed, contextual description about how the image relates to, strengthens, and enhances the post content:

            Explain:
            - The type of image (e.g. photo, video, graphic, etc.)
            - What it shows in relation to the content (company logo, employee photo, product diagram, etc.)
            - How this complements and strengthens the post content

            Keep it concise and to the point. Use no more than a few sentences.
            """
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": contextual_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            )
            
            print("🔍 Generating contextual image description...")
            result = llm.invoke([message])
            
            return result.content.strip()
                
        except Exception as e:
            print(f"❌ Error generating contextual image description: {e}")
            return None

    def save_final_data_to_csv(self, processed_posts, filename="linkedin_posts.csv"):
        """Save final processed data to CSV"""
        if not processed_posts:
            print("⚠️ No processed data to save")
            return
            
        df = pd.DataFrame(processed_posts)
        
        # Final CSV column order
        final_csv_columns = ['target_audience', 'content', 'content_url', 'media_description']
        df = df.reindex(columns=final_csv_columns)

        file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0
        
        if file_exists:
            df.to_csv(filename, mode='a', header=False, index=False)
            print(f"📄 Appended {len(processed_posts)} processed posts to {filename}")
        else:
            df.to_csv(filename, index=False)
            print(f"📄 Saved {len(processed_posts)} processed posts to {filename}")
    
    def close(self):
        if self.driver:
            self.driver.quit()
            print("🔒 Browser closed.")

# Main ------------------------------------------------------------------------------------------------

def main():
    print("🚀 LinkedIn Post Scraper with Two-Phase Processing")
    print("Phase 1: Scrape raw content and image URLs")
    print("Phase 2: Process with LLMs for descriptions and target audiences")
    print("WARNING: Scraping may violate LinkedIn's Terms of Service.")
    print("Consider using LinkedIn's official API instead.")
    print("Ensure posts are publicly accessible without login for best results.")
    
    # Hardcoded URLs for initial scraping
    urls_input1 = "https://www.linkedin.com/posts/ashish-shukla-life-coach_humanresources-career-jobsearch-activity-7334043380038942721-HUK9?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/rbccawang_too-many-students-never-get-the-chance-to-activity-7327755483312730113-C-BX?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_the-perfect-age-to-start-a-startup-isnt-activity-7329128517592301568-WUzw?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_the-paypal-mafia-is-the-best-founding-team-activity-7307747695312404482-3vx4?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_my-co-founder-and-i-live-in-nyc-making-40k-activity-7300152631585296385-wfV6?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_first-i-handed-in-my-notice-then-they-offered-activity-7292180110772760579-GP_m?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_a-year-ago-a-founder-raised-20m-at-a-200m-activity-7290368128721502208-mKeQ?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_last-month-i-watched-a-startups-entire-activity-7288556164114448386-awYy?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_3-months-ago-two-of-my-childhood-best-friends-activity-7285657095926919170-Zs75?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_stanford-has-8054-undergrads-one-of-them-activity-7282395578603323392-mBom?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_since-freshman-year-at-harvard-i-have-changed-activity-7280583641422823424-X0Pn?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_harvard-had-54008-apply-last-year-with-a-activity-7277322130109677568-wzvv?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_on-the-surface-i-have-raised-3m-gotten-activity-7274423150262550528-RTkP?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/albert-mao_last-year-we-got-into-yc-and-raised-3m-activity-7265001442283851776-MH_7?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333896158341156864-1Q1P?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333534379438219266-XTqN?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_this-woman-sold-her-book-club-for-900m-activity-7332808993653829632-AkDl?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7333175504436436992-WFAa?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7330638996395491329-IWi5?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7329194790741254145-GgJ1?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7330638996395491329-IWi5?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7323386909169266689-vvXr?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/justine-juillard_femalefounder-activity-7321966975860047872-MMey?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/olivermolander_artificialintelligence-activity-7332320138823729152-qc6r?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/vatsalppatel_satya-nadella-id-say-maybe-20-30-of-activity-7333556138216456192-Svva?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/manuvanderveeren_incredibly-excited-to-announce-that-we-activity-7333397705320243200-GWGX?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts,https://www.linkedin.com/posts/activity-7324427305412419584-UMsx?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/clemens-christoph-191886239_unpopular-opinion-ycs-startup-school-activity-7340998895021219841-L3QT?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts"
    urls_input2 = "https://www.linkedin.com/posts/jpsingaraju_if-you-ship-we-will-hire-you-this-past-activity-7337902766666764289-F6On?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/sjnyoon_biography-is-one-of-the-east-coasts-fastest-growing-activity-7341929871574515712-Oc0J?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/sjnyoon_i-am-looking-for-cracked-ml-engineers-us-activity-7336546537184907265-Qhvs?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/milannaropanth_im-hiring-founding-engineers-and-founding-activity-7321982996184514560-NaCn?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_my-mom-raised-me-as-a-single-parent-7-days-activity-7340015294368620544-3sm4?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_she-had-no-internship-no-warm-intros-no-activity-7346594575718731777-3Oo0?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/dara-ladjevardian_big-news-weve-raised-a-16m-series-a-led-ugcPost-7343303064402935808--nTI?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/eunicelai1_not-doing-anything-this-summer-hate-your-ugcPost-7344374007875485696-6tsg?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_excited-to-announce-im-still-single-not-activity-7342291476124418049-q4sc?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_after-attending-yc-ai-startup-school-the-activity-7341155012573597698-_mFD?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_elon-musk-got-rejected-from-a-job-at-netscape-activity-7340735992317865984-nwIm?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/chulucas_i-graduated-from-harvard-this-is-long-overdue-ugcPost-7340064779232796673-mJit?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_cracked-founders-and-builders-only-back-activity-7338976074858405892-lIc2?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_theres-no-playbook-for-breaking-into-startups-activity-7337840911579549696-QT4r?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_i-miss-the-younger-version-of-me-the-one-activity-7333947674770948098-fiIY?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/kasey-zhang_you-shouldnt-use-structured-output-mode-activity-7333915812342255617-jol1?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_still-looking-for-a-summer-internship-here-activity-7332852680534499329-wufO?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_if-youre-scared-of-investing-in-yourself-activity-7329618402648449024-e6We?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_no-internship-this-summer-good-that-means-activity-7327408689462546435-YO03?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/rich-zou_im-excited-to-share-that-after-multiple-activity-7315899545500930048-7b0a?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/ayaan-parikh_heres-the-photo-rahul-vijayan-and-i-took-activity-7345532124701040640-X5d1?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/luis-von-ahn-duolingo_people-always-ask-me-why-duolingo-is-headquartered-activity-7343986421214441472-30Kj?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/allan-guo_99-of-yc-founders-are-too-soft-500k-activity-7333929928045801474-CAWM?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/lawrenceliuu_i-got-hit-by-a-car-a-week-before-our-yc-launch-activity-7332854468079665153-oqrF?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/allan-guo_my-cofounder-was-hit-by-a-car-one-week-before-activity-7331059719156957184-owHS?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/benleejamin_linkedin-and-instagram-had-their-moment-activity-7317956702765539329-Xm0F?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/benleejamin_heres-all-of-the-jobs-i-didnt-get-l-activity-7330277421100732417-zgeK?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, https://www.linkedin.com/posts/benleejamin_ive-gotten-6-serious-job-offers-heres-activity-7325205839533809666-FC39?utm_source=share&utm_medium=member_desktop&rcm=ACoAADkZGWkB04tJGESNDVHaPixureBEadG9mts, "
    urls_input = urls_input1 + urls_input2

    post_urls = [url.strip() for url in urls_input.split(',') if url.strip()]

    if not post_urls:
        print("❌ No URLs provided for scraping.")
        return
    
    # File names
    raw_csv_file = "raw_linkedin_posts.csv"
    final_csv_file = "influencers_data_filtered.csv"

    scraper = LinkedInScraper(headless=True)
    
    try:
        # Verify not logged in
        if not scraper.verify_not_logged_in():
            print("❌ Aborting: Please ensure you're not logged in to LinkedIn")
            return

        # Phase 1: Scrape raw content and image URLs
        print(f"\n{'='*50}")
        print("🔍 PHASE 1: SCRAPING RAW CONTENT")
        print(f"{'='*50}")
        
        scraper.scrape_raw_content_from_urls(post_urls)
        scraper.save_raw_data_to_csv(raw_csv_file)
        
        # Phase 2: Process with LLMs
        print(f"\n{'='*50}")
        print("🤖 PHASE 2: PROCESSING WITH LLMs")
        print(f"{'='*50}")
        
        processed_posts = scraper.process_raw_data_with_llms(raw_csv_file)
        
        if processed_posts:
            scraper.save_final_data_to_csv(processed_posts, final_csv_file)
            print(f"\n🎉 SUCCESS! Final data saved to {final_csv_file}")
        else:
            print("❌ No posts were successfully processed.")
        
    except Exception as e:
        print(f"❌ An error occurred during the scraping process: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()





# def search_posts(self, keyword, max_posts=50):
    #     print(f"Searching for posts with keyword: {keyword}")
        
    #     search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword}&sortBy=%22date_posted%22"
    #     self.driver.get(search_url)
        
    #     posts_collected = 0
    #     scroll_attempts = 0
    #     max_scrolls = 20
        
    #     seen_post_ids = set() # Avoids processing duplicate posts during scrolling

    #     while posts_collected < max_posts and scroll_attempts < max_scrolls:
    #         self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #         time.sleep(random.uniform(2, 4)) # Random delay to mimic human behavior
            
    #         # General selector for activity posts
    #         posts = self.driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2")

    #         new_posts_found_this_scroll = 0
    #         for post_element in posts:
    #             post_id_element = post_element.get_attribute("data-urn")
    #             if not post_id_element:
    #                 post_id_element = post_element.get_attribute("id") 
                
    #             if post_id_element and post_id_element in seen_post_ids: