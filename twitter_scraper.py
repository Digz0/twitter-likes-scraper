from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Chrome options
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# Set up the ChromeDriver
service = Service(os.getenv('CHROMEDRIVER_PATH'))
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate to Twitter login page
driver.get("https://twitter.com/login")
time.sleep(5)  # Wait for the page to load

# Wait for the username field and enter the username
username_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
)
username_field.send_keys(os.getenv('TWITTER_USERNAME'))
username_field.send_keys(Keys.RETURN)

# Wait for the password field and enter the password
password_field = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
)
password_field.send_keys(os.getenv('TWITTER_PASSWORD'))
password_field.send_keys(Keys.RETURN)

# Wait for the login process to complete
time.sleep(5)

# Navigate to your likes page
driver.get(f"https://twitter.com/{os.getenv('TWITTER_USERNAME')}/likes")
time.sleep(10)

def scroll_to_end():
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scroll_down(scroll_amount=1000):
    driver.execute_script(f"window.scrollTo(0, window.scrollY + {scroll_amount})")

def parse_tweets():
    return driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')

def get_tweet_data(tweet_element):
    data = {}
    
    try:
        username_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
        data['Username'] = username_element.text.strip()
    except:
        data['Username'] = ''
    
    try:
        tweet_text_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
        data['Tweet'] = tweet_text_element.text
    except:
        data['Tweet'] = ''
    
    try:
        image_element = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetPhoto"]')
        data['Image'] = image_element.find_element(By.TAG_NAME, 'img').get_attribute('src')
    except:
        data['Image'] = ''
    
    try:
        data['Url'] = tweet_element.find_element(By.CSS_SELECTOR, 'a[href*="/status/"]').get_attribute('href')
    except:
        data['Url'] = ''
    
    return data

def get_dataframe(max_tweets=200, scroll_pause_time=2):
    tweet_data_list = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while len(tweet_data_list) < max_tweets:
        tweets = parse_tweets()
        
        for tweet in tweets:
            try:
                tweet_data = get_tweet_data(tweet)
                if tweet_data and tweet_data not in tweet_data_list:
                    tweet_data_list.append(tweet_data)
                    print(f"Collected {len(tweet_data_list)} tweets")
                    
                    if len(tweet_data_list) >= max_tweets:
                        break
            except Exception as e:
                print(f"Error processing tweet: {e}")
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    return pd.DataFrame(tweet_data_list)

# Call the function to get the DataFrame
df = get_dataframe(max_tweets=200)  # Adjust max_tweets as needed

# Save the DataFrame to a CSV file
df.to_csv('liked_tweets.csv', index=False)

print(f"Collected {len(df)} tweets.")