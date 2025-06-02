from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.options.android import UiAutomator2Options
import time
import pandas as pd


def init_appium_driver():
    print("🔧 Initializing Appium driver...")
    options = UiAutomator2Options()
    options.platformName = "Android"
    options.platformVersion = "12"  # Adjust to your device version if necessary
    options.deviceName = "10BE6713CA0025A"
    options.appPackage = "in.amazon.mShop.android.shopping"
    options.appActivity = "com.amazon.mShop.home.HomeActivity"
    options.noReset = True
    options.newCommandTimeout = 600
    options.automationName = "UiAutomator2"
    
    # Notice the correct Appium server URL format
    driver = webdriver.Remote("http://localhost:4723", options=options)
    print("✅ Driver initialized")
    return driver


def launch_amazon_app(driver):
    print("🚀 Launching Amazon app via mobile command...")
    try:
        driver.execute_script("mobile: startActivity", {
            "appPackage": "in.amazon.mShop.android.shopping",
            "appActivity": "com.amazon.mShop.home.HomeActivity",
            "intentAction": "android.intent.action.MAIN",
            "intentCategory": "android.intent.category.LAUNCHER",
            "flags": ["0x10200000"]  # FLAG_ACTIVITY_NEW_TASK | FLAG_ACTIVITY_RESET_TASK_IF_NEEDED
        })
        time.sleep(5)
        print("✅ Amazon app started")
    except Exception as e:
        print(f"❌ Error launching Amazon app: {e}")
        return False
    return True


def check_current_activity(driver):
    try:
        activity = driver.current_activity
        print(f"📱 Current activity: {activity}")
        return activity
    except Exception as e:
        print(f"❌ Could not get current activity: {e}")
        return None


def search_and_scrape(driver, search_term, max_scrolls=3):
    wait = WebDriverWait(driver, 20)

    try:
        search_icon = wait.until(EC.element_to_be_clickable((AppiumBy.ACCESSIBILITY_ID, "Search")))
        search_icon.click()
        time.sleep(2)
    except Exception as e:
        print(f"❌ Failed to click search icon: {e}")
        return []

    try:
        search_box = wait.until(EC.presence_of_element_located((AppiumBy.ID, "in.amazon.mShop.android.shopping:id/rs_search_src_text")))
    except:
        print("⚠️ ID-based search box not found, trying fallback XPath")
        try:
            search_box = wait.until(EC.presence_of_element_located((AppiumBy.XPATH, "//android.widget.EditText[@text='Search']")))
        except Exception as e:
            print(f"❌ Could not find search input. Saving page source. Error: {e}")
            with open("page_dump.xml", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return []

    search_box.send_keys(search_term)
    driver.press_keycode(66)  # Press ENTER
    time.sleep(3)

    product_data = []
    scroll_count = 0

    while scroll_count < max_scrolls:
        print(f"\n🔃 Scroll {scroll_count + 1}")

        products = driver.find_elements(AppiumBy.XPATH, "//android.view.View[@text and contains(@text, '₹')]")

        if not products:
            print("⚠️ No price-tagged views found. Consider checking page layout or increasing scroll time.")
            break

        for idx, product in enumerate(products):
            try:
                text = product.get_attribute("text")
                lines = text.split("\n")
                title = lines[0] if lines else "No Title"
                price = next((line for line in lines if "₹" in line), "No Price")
                print(f"📦 Product {idx + 1}: Title = {title}, Price = {price}")
                product_data.append({"Title": title, "Price": price})
            except Exception as e:
                print(f"⚠️ Error extracting product {idx + 1}: {e}")

        driver.swipe(500, 1600, 500, 600, 800)
        time.sleep(3)
        scroll_count += 1

    return product_data


def main():
    driver = init_appium_driver()
    time.sleep(3)

    # Launch the app explicitly
    if not launch_amazon_app(driver):
        driver.quit()
        return

    current_activity = check_current_activity(driver)
    if not current_activity or "amazon" not in current_activity.lower():
        print("❌ Amazon app is not in foreground. Check if it's installed and launched correctly.")
        driver.quit()
        return

    search_terms = ['atta', 'cookies']
    all_results = []

    for term in search_terms:
        print(f"\n🔍 Searching for: {term}")
        results = search_and_scrape(driver, term, max_scrolls=3)
        all_results.extend(results)

    driver.quit()

    df = pd.DataFrame(all_results)
    df.to_csv("amazon_app_scrape.csv", index=False)
    print("\n✅ Data saved to amazon_app_scrape.csv")


if __name__ == "__main__":
    main()
