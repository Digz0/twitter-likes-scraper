import argparse
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(os.getenv('CHROMEDRIVER_PATH'))
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login_to_twitter(driver, username, password):
    driver.get("https://twitter.com/login")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))).send_keys(username, Keys.RETURN)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))).send_keys(password, Keys.RETURN)
        time.sleep(5)  # Wait for login to complete
    except TimeoutException:
        logging.error("Login failed: elements not found or timeout occurred")
        return False
    return True

def get_tweet_data(tweet_element):
    data = {'Username': '', 'Tweet': '', 'Image': '', 'Url': ''}
    try:
        data['Username'] = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]').text.strip()
        data['Tweet'] = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]').text
        data['Image'] = tweet_element.find_element(By.CSS_SELECTOR, '[data-testid="tweetPhoto"] img').get_attribute('src')
        data['Url'] = tweet_element.find_element(By.CSS_SELECTOR, 'a[href*="/status/"]').get_attribute('href')
    except NoSuchElementException:
        logging.warning(f"Some elements not found for tweet: {data['Username']}")
    return data

def get_dataframe(driver, output_file, max_tweets=200, scroll_pause_time=2):
    tweet_data_list = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while len(tweet_data_list) < max_tweets:
        for tweet in driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]'):
            tweet_data = get_tweet_data(tweet)
            if tweet_data and tweet_data not in tweet_data_list:
                tweet_data_list.append(tweet_data)
                logging.info(f"Collected {len(tweet_data_list)} tweets")
                if len(tweet_data_list) >= max_tweets:
                    break
                if len(tweet_data_list) % 50 == 0:
                    save_incremental_data(tweet_data_list[-50:], output_file)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            logging.info("Reached end of page or no more tweets to load")
            break
        last_height = new_height
    
    return pd.DataFrame(tweet_data_list)

def save_incremental_data(data_list, output_file, chunk_size=50):
    df = pd.DataFrame(data_list)
    if os.path.exists(output_file):
        df.to_csv(output_file, mode='a', header=False, index=False)
    else:
        df.to_csv(output_file, index=False)
    logging.info(f"Saved {len(data_list)} tweets to {output_file}")

def main(max_tweets, output_file):
    driver = setup_driver()
    
    if not login_to_twitter(driver, os.getenv('TWITTER_USERNAME'), os.getenv('TWITTER_PASSWORD')):
        driver.quit()
        return

    driver.get(f"https://twitter.com/{os.getenv('TWITTER_USERNAME')}/likes")
    time.sleep(5)

    df = get_dataframe(driver, output_file, max_tweets=max_tweets)
    df.to_csv(output_file, index=False)
    logging.info(f"Collected {len(df)} tweets. Data saved to {output_file}")

    driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape liked tweets from a Twitter account")
    parser.add_argument("--max_tweets", type=int, default=200, help="Maximum number of tweets to scrape")
    parser.add_argument("--output", type=str, default="liked_tweets.csv", help="Output CSV file name")
    args = parser.parse_args()

    main(args.max_tweets, args.output)
