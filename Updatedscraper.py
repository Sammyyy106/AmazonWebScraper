# Required Libraries
import re
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize WebDriver
def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(), options=options)
    return driver

# Set Pincode on Amazon
def set_pincode(driver, pincode):
    driver.get("https://www.amazon.in/")
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.element_to_be_clickable((By.ID, "nav-global-location-popover-link"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "GLUXZipUpdateInput"))).send_keys(str(pincode))
        wait.until(EC.element_to_be_clickable((By.ID, "GLUXZipUpdate"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "GLUXConfirmClose"))).click()
    except:
        print(f"Failed to set pincode {pincode}")

# Main Scraping Function
def scrape_amazon(driver, search_term, pincode, num_pages=2):
    wait = WebDriverWait(driver, 10)
    all_products = []
    seen_titles = set()

    for page in range(1, num_pages + 1):
        url = f"https://www.amazon.in/s?k={search_term}&page={page}"
        driver.get(url)

        try:
            wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']")))
        except:
            continue

        products = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")
        print(f"Scraping page {page} for '{search_term}' in pincode {pincode} — {len(products)} products found")

        for product in products:
            try:
                title = product.find_element(By.XPATH, ".//h2//span").text.strip()
            except:
                title = "No Title"
            if title in seen_titles:
                continue
            seen_titles.add(title)

            try:
                link_elem = product.find_element(By.XPATH, ".//a[@class='a-link-normal s-no-outline']")
                link = link_elem.get_attribute('href')
            except:
                link = "No Link"

            try:
                price = product.find_element(By.XPATH, ".//span[@class='a-price-whole']").text.replace(',', '').strip()
            except:
                try:
                    price = product.find_element(By.XPATH, ".//span[@class='a-offscreen']").text.replace('₹', '').replace(',', '').strip()
                except:
                    price = "No Price"

            try:
                mrp_elem = product.find_element(By.XPATH, ".//span[@class='a-price a-text-price' and @data-a-strike='true']//span[@class='a-offscreen']")
                raw_price = mrp_elem.get_attribute("textContent")
                mrp = raw_price.replace('₹', '').replace(',', '').strip()
            except:
                mrp = "No Price"

            try:
                discount_percent = round(100 * (float(mrp) - float(price)) / float(mrp), 2) if price != "No Price" and mrp != "No Price" else 0.0
            except:
                discount_percent = 0.0

            try:
                grammage_match = re.search(r'(\d+\.?\d*\s?(ml|g|kg|l))', title.lower())
                grammage = grammage_match.group(0) if grammage_match else "No Grammage"
            except:
                grammage = "No Grammage"

            try:
                badge = product.find_element(By.XPATH, ".//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'deal')]")
                deal_tag = badge.text.strip()
            except:
                deal_tag = "No Deal"

            try:
                qty = product.find_element(By.XPATH, ".//span[contains(text(),'bought in past month')]").text.strip()
            except:
                qty = "No data"

            try:
                rating = product.find_element(By.XPATH, ".//span[@class='a-icon-alt']").get_attribute("textContent").split()[0]
            except:
                rating = "No Rating"

            try:
                reviews = product.find_element(By.XPATH, ".//a[contains(@aria-label,'ratings')]/span").text.strip()
            except:
                reviews = "No Reviews"

            try:
                ad_elem = product.find_element(By.XPATH, ".//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sponsored')]")
                ad_status = "Ad"
            except:
                ad_status = "Not Ad"

            product_data = {
                'Title': title,
                'Grammage': grammage,
                'Selling Price': price,
                'MRP': mrp,
                'Discount %': discount_percent,
                'Deal Tags': deal_tag,
                'Quantity Bought': qty,
                'Rating': rating,
                'Reviews': reviews,
                'Link': link,
                'Ad/Not Ad': ad_status,
                'Date': datetime.now().strftime("%d-%m-%Y"),
                'Search Term': search_term,
                'Pincode': pincode,
                'Category': search_term,
            }
            all_products.append(product_data)

    return all_products

# Function to scrape for multiple terms and pincodes
def scrape_multiple_combinations(search_terms, pincodes, num_pages=2):
    combined_data = []
    driver = init_driver()
    for pincode in pincodes:
        set_pincode(driver, pincode)
        for term in search_terms:
            results = scrape_amazon(driver, term, pincode, num_pages)
            combined_data.extend(results)
    driver.quit()

    df = pd.DataFrame(combined_data)
    today_date = datetime.now().strftime("%Y-%m-%d")
    base_filename = f"amazon_scrape_{today_date}"
    df.to_excel(f"{base_filename}.xlsx", index=False)
    df.to_csv(f"{base_filename}.csv", index=False)
    df.to_json(f"{base_filename}.json", orient="records", lines=True)
    print(f"\nSaved results as {base_filename}.xlsx, .csv, and .json")

# Example usage
search_terms = ['right shift', 'atta','cookies']
pincodes = [560005,560064]
scrape_multiple_combinations(search_terms, pincodes, num_pages=2)
