# Twitter Likes Scraper

A Python script to scrape liked tweets from a Twitter account using Selenium.

## Features

- Automatically logs into Twitter
- Navigates to the user's likes page
- Scrolls through and collects data from liked tweets
- Saves tweet data (username, tweet text, image URL, tweet URL) to a CSV file

## Requirements

- Python 3.x
- Selenium
- ChromeDriver
- pandas
- python-dotenv

## Setup

1. Clone this repository
2. Install required packages: `pip install selenium pandas python-dotenv`
3. Download ChromeDriver and update the path in the `.env` file
4. Create a `.env` file with your Twitter credentials and ChromeDriver path

## Usage

Run the script: `python twitter_scraper.py`

## Note

This script is for educational purposes only. Be aware that web scraping may violate Twitter's terms of service. Use responsibly and at your own risk.
