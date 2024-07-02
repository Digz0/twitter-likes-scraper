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

load_dotenv()

# Set up Chrome and navigate to Twitter
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
service = Service(os.getenv('CHROMEDRIVER_PATH'))
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get("https://twitter.com/login")

# Login process
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))).send_keys(os.getenv('TWITTER_USERNAME'), Keys.RETURN)
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))).send_keys(os.getenv('TWITTER_PASSWORD'), Keys.RETURN)
time.sleep(5)

# Navigate to likes page
driver.get(f"https://twitter.com/{os.getenv('TWITTER_USERNAME')}/likes")
time.sleep(5)

def get_tweet_data(tweet_element):
    data = {'Username': '', 'Tweet': '', 'Image': '', 'Url': ''}
    try:
        data['Username'] = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]').text.strip()
        data['Tweet'] = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]').text
        data['Image'] = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetPhoto"] img').get_attribute('src')
        data['Url'] = tweet_element.find_element(By.CSS_SELECTOR, 'a[href*="/status/"]').get_attribute('href')
    except:
        pass
    return data

def get_dataframe(max_tweets=200):
    tweet_data_list = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while len(tweet_data_list) < max_tweets:
        for tweet in driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]'):
            tweet_data = get_tweet_data(tweet)
            if tweet_data and tweet_data not in tweet_data_list:
                tweet_data_list.append(tweet_data)
                print(f"Collected {len(tweet_data_list)} tweets")
                if len(tweet_data_list) >= max_tweets:
                    break
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    return pd.DataFrame(tweet_data_list)

# Collect tweets and save to CSV
df = get_dataframe(max_tweets=200)
df.to_csv('liked_tweets.csv', index=False)
print(f"Collected {len(df)} tweets.")
