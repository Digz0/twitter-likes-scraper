import argparse, logging, time, os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    return webdriver.Chrome(service=Service(os.getenv('CHROMEDRIVER_PATH')), options=options)

def login_to_twitter(driver, username, password):
    driver.get("https://twitter.com/login")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))).send_keys(username, Keys.RETURN)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))).send_keys(password, Keys.RETURN)
        time.sleep(5)
        return True
    except TimeoutException:
        logging.error("Login failed: elements not found or timeout occurred")
        return False

def get_tweet_data(tweet):
    data = {'Username': '', 'Tweet': '', 'Image': '', 'Url': ''}
    try:
        data['Username'] = tweet.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]').text.strip()
        data['Tweet'] = tweet.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]').text
        data['Image'] = tweet.find_element(By.CSS_SELECTOR, '[data-testid="tweetPhoto"] img').get_attribute('src')
        data['Url'] = tweet.find_element(By.CSS_SELECTOR, 'a[href*="/status/"]').get_attribute('href')
    except NoSuchElementException:
        pass
    return data

def get_tweets(driver, max_tweets=200):
    tweets = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while len(tweets) < max_tweets:
        for tweet in driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]'):
            tweet_data = get_tweet_data(tweet)
            if tweet_data and tweet_data not in tweets:
                tweets.append(tweet_data)
                logging.info(f"Collected {len(tweets)} tweets")
                if len(tweets) >= max_tweets:
                    break
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    return pd.DataFrame(tweets)

def main(max_tweets, output_file):
    driver = setup_driver()
    try:
        if not login_to_twitter(driver, os.getenv('TWITTER_USERNAME'), os.getenv('TWITTER_PASSWORD')):
            return

        driver.get(f"https://twitter.com/{os.getenv('TWITTER_USERNAME')}/likes")
        time.sleep(5)

        df = get_tweets(driver, max_tweets=max_tweets)
        df.to_csv(output_file, index=False)
        logging.info(f"Collected {len(df)} tweets. Data saved to {output_file}")

    finally:
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape liked tweets from a Twitter account")
    parser.add_argument("--max_tweets", type=int, default=200, help="Maximum number of tweets to scrape")
    parser.add_argument("--output", type=str, default="liked_tweets.csv", help="Output CSV file name")
    args = parser.parse_args()

    main(args.max_tweets, args.output)
