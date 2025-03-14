import time
import csv
import os
import random
import pandas as pd
import re
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Folder configurations
CSV_FOLDER = "output"
os.makedirs(CSV_FOLDER, exist_ok=True)
input_file = "pincode.csv"
output_urls_file = f"{CSV_FOLDER}/business_urls.csv"
output_details_file = f"{CSV_FOLDER}/business_details.csv"


df = pd.read_csv(input_file)
postal_codes = df["postalCode"].astype(str).unique()

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    
    # Use installed Chrome in Docker
    if os.environ.get('GOOGLE_CHROME_BIN'):
        options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
    
    # Try different paths for chromedriver
    chromedriver_paths = [
        os.environ.get('CHROMEDRIVER_PATH'),
        '/usr/local/bin/chromedriver',
        '/usr/local/bin/chromedriver-linux64/chromedriver'
    ]
    
    for path in chromedriver_paths:
        if path and os.path.exists(path):
            print(f"Using chromedriver at: {path}")
            
            return webdriver.Chrome(service=Service(path), options=options)
    
    # Fallback to webdriver manager
    print("No chromedriver found in predefined paths, using webdriver-manager")

    return webdriver.Chrome(options=options)

driver = init_driver()
business_urls = set()

def clean_text(text):
    if text:
        text = re.sub(r"[^\x20-\x7E]", "", text)
        return text.strip()
    return "N/A"

def get_google_maps_urls(postal_code, max_retries=3):
    search_query = f"Home Appliances in {postal_code}, Singapore"
    search_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
    
    print(f"\nSearching for: {search_query} (Pincode: {postal_code})")

    for attempt in range(max_retries):
        try:
            driver.get(search_url)
            time.sleep(random.randint(5, 8))

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/place/')]"))
            )
        except Exception as e:
            error_msg = f"Error on attempt {attempt+1}/{max_retries} for {postal_code}: {str(e)}"
            print(error_msg)
            
            continue

        try:
            results_container = driver.find_elements(By.XPATH, "//div[@role='feed']")
            if not results_container:
                message = f"No results container found for {postal_code}, skipping..."
                print(message)

                return []

            for _ in range(10):
                driver.execute_script("arguments[0].scrollTop += 1000;", results_container[0])
                time.sleep(random.uniform(2, 4))

            urls = []
            elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/place/')]")
            count = 0
            for element in elements:
                url = element.get_attribute("href")
                if url and url not in business_urls:
                    business_urls.add(url)
                    urls.append(url)
                    count += 1
                if count >= 5:
                    break

            if urls:
                message = f"Found {len(urls)} businesses for Pincode {postal_code}"
                print(message)

                return urls
        except Exception as e:
            error_msg = f"Error processing results for {postal_code}: {str(e)}"
            print(error_msg)
            
            continue

    message = f"No valid results for {postal_code} after {max_retries} attempts"
    print(message)
    
    return []


with open(output_urls_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Business URL"])
    
    for index, postal_code in enumerate(postal_codes):
        urls = get_google_maps_urls(postal_code)
        for url in urls:
            writer.writerow([url])
        file.flush()
 
        message = f"Completed processing for Pincode {postal_code} ({index+1}/{len(postal_codes)})"
        print(message)
        
        if (index + 1) % 10 == 0:
            restart_msg = "Restarting WebDriver to prevent session timeout..."
            print(restart_msg)

            driver.quit()
            driver = init_driver()

driver.quit()


def get_google_maps_details(url):
    try:
        driver.get(url)
        time.sleep(random.randint(3, 6))

        details = {
            "Name": "N/A",
            "Address": "N/A",
            "Phone": "N/A",
            "Rating": "N/A",
            "Reviews": "N/A",
            "Plus Code": "N/A",
            "Website": "N/A",
            "Google Maps URL": url
        }
        
        # Try to get name
        try:
            if driver.find_elements(By.XPATH, "//h1[contains(@class, 'DUwDvf')]"):
                details["Name"] = clean_text(driver.find_element(By.XPATH, "//h1[contains(@class, 'DUwDvf')]").text)
        except:
            pass
            
        # Try to get address
        try:
            if driver.find_elements(By.XPATH, "//button[@data-tooltip='Copy address']"):
                details["Address"] = clean_text(driver.find_element(By.XPATH, "//button[@data-tooltip='Copy address']").text)
        except:
            pass
            
        # Try to get phone
        try:
            if driver.find_elements(By.XPATH, "//button[@data-tooltip='Copy phone number']"):
                details["Phone"] = clean_text(driver.find_element(By.XPATH, "//button[@data-tooltip='Copy phone number']").text)
        except:
            pass
            
        # Try to get rating
        try:
            if driver.find_elements(By.XPATH, "//span[@class='MW4etd']"):
                details["Rating"] = clean_text(driver.find_element(By.XPATH, "//span[@class='MW4etd']").text)
        except:
            pass
            
        # Try to get reviews
        try:
            if driver.find_elements(By.XPATH, "//span[@class='UY7F9']"):
                details["Reviews"] = clean_text(driver.find_element(By.XPATH, "//span[@class='UY7F9']").text)
        except:
            pass
            
        # Try to get plus code
        try:
            if driver.find_elements(By.XPATH, "//button[@data-tooltip='Copy plus code']"):
                details["Plus Code"] = clean_text(driver.find_element(By.XPATH, "//button[@data-tooltip='Copy plus code']").text)
        except:
            pass
            
        # Try to get website
        try:
            if driver.find_elements(By.XPATH, "//a[contains(@aria-label, 'Visit') or contains(@href, 'http')]"):
                details["Website"] = clean_text(driver.find_element(By.XPATH, "//a[contains(@aria-label, 'Visit') or contains(@href, 'http')]").get_attribute("href"))
        except:
            pass
        
        return details
    except Exception as e:
        error_msg = f"Error scraping details for {url}: {str(e)}"
        print(error_msg)
        
        return {
            "Name": "Error",
            "Address": "Error",
            "Phone": "Error",
            "Rating": "Error",
            "Reviews": "Error", 
            "Plus Code": "Error",
            "Website": "Error",
            "Google Maps URL": url
        }

driver = init_driver()

# Check if business_urls.csv exists
if os.path.exists(output_urls_file):
    with open(output_urls_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        urls = [row[0] for row in reader]
    
    total_urls = len(urls)
    message = f"Found {total_urls} URLs to process for details..."
    print(message)
    
    with open(output_details_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Address", "Phone", "Rating", "Reviews", "Plus Code", "Website", "Google Maps URL"])
        
        for index, url in enumerate(urls):
            details = get_google_maps_details(url)
            writer.writerow([
                details["Name"], 
                details["Address"], 
                details["Phone"], 
                details["Rating"], 
                details["Reviews"], 
                details["Plus Code"], 
                details["Website"], 
                details["Google Maps URL"]
            ])
            file.flush()

            if (index + 1) % 20 == 0:
                restart_msg = f"♻️ Restarting WebDriver to prevent session timeout... ({index+1}/{total_urls})"
                print(restart_msg)
                
                driver.quit()
                driver = init_driver()
else:
    error_msg = f"URLs file {output_urls_file} not found. Skipping business details collection."
    print(error_msg)

driver.quit()

# Final completion notification with summary statistics
if os.path.exists(output_details_file):
    try:
        # Get some basic stats from the output file
        df_results = pd.read_csv(output_details_file)
        valid_results = len(df_results[df_results["Name"] != "Error"])
        avg_rating = df_results[df_results["Rating"] != "N/A"][df_results["Rating"] != "Error"]["Rating"].astype(float).mean()
        has_website = len(df_results[df_results["Website"] != "N/A"][df_results["Website"] != "Error"])
        has_phone = len(df_results[df_results["Phone"] != "N/A"][df_results["Phone"] != "Error"])
        
        completion_msg = f"Scraping complete! Data saved to {output_details_file}"
        print(completion_msg)

    except Exception as e:
        # Simpler completion message if stats calculation fails
        completion_msg = f"Scraping complete! Data saved to {output_details_file}"
        print(completion_msg)

else:
    # If no output file exists
    completion_msg = "Scraping process completed but no output file was generated."
    print(completion_msg)
