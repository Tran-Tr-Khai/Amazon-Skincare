import csv
import time
import random
import logging
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("scraper_log.log", encoding="utf-8")]
)

class AmazonScraper:
    def __init__(self, url_template, num_pages=2, scroll_times=5, output_file="products.csv"):
        self.url_template = url_template
        self.num_pages = num_pages
        self.scroll_times = scroll_times
        self.output_file = output_file
        self.headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/115.0",
            ]),
            "Accept-Language": "en-US,en;q=0.5"
        }
        self.session = requests.Session()
        self.driver = None

    # Khởi tạo và quản lý WebDriver
    def _setup_driver(self):
        chrome_options = Options() 
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("disable-infobars")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Thêm các header để giả lập trình duyệt thực
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        driver.set_page_load_timeout(60)
        return driver

    def _get_driver(self):
        if not self.driver:
            self.driver = self._setup_driver()
            logging.info("Initialized new WebDriver")
        try:
            # Kiểm tra session còn sống bằng cách lấy URL hiện tại
            self.driver.current_url
        except Exception as e:
            logging.warning(f"Session lost: {e}. Restarting WebDriver.")
            try:
                self.driver.quit()
            except:
                pass  # Bỏ qua nếu không đóng được driver cũ
            self.driver = self._setup_driver()
        return self.driver

    def _close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver closed successfully.")
            except Exception as e:
                logging.warning(f"Failed to close WebDriver: {e}")
            finally:
                self.driver = None

    def _scroll_page(self):
        driver = self._get_driver()
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)  # Cuộn xuống cuối một lần
        time.sleep(10)  # Chờ 10 giây để nội dung tải
        final_products = driver.find_elements(By.CLASS_NAME, "gridItemRoot")
        logging.info(f"Total products found after scrolling: {len(final_products)}")

    def _fetch_page(self, url, use_selenium=False, scroll=False):
        if use_selenium or scroll:
            try:
                driver = self._get_driver()
                driver.get(url)
                if scroll:
                    self._scroll_page()  # Cuộn trang nếu cần
                else:
                    time.sleep(5)  # Chờ tải trang thông thường
                soup = BeautifulSoup(driver.page_source, "html.parser")
                logging.info(f"Loaded page with Selenium: {url}")
                return soup
            except Exception as e:
                logging.warning(f"Selenium failed for {url}: {e}")
                return None
        else:
            try:
                response = self.session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                logging.info(f"Loaded page with requests: {url}")
                return soup
            except requests.RequestException as e:
                logging.warning(f"Requests failed for {url}: {e}")
                return None
            
    # Phân tích danh sách sản phẩm hàng đầu
    def _parse_top_products(self, page_num):
        url = self.url_template.format(page_num)
        soup = self._fetch_page(url, use_selenium=True, scroll=True)  # Dùng Selenium và cuộn
        if not soup:
            logging.error(f"Failed to load page {page_num}")
            return []
        
        products = soup.find_all("div", attrs={"id": "gridItemRoot"})
        data = []
        for product in products:
            id_tag = product.find("div", attrs={"data-asin": True})
            top = product.find("span", class_="zg-bdg-text")
            link = product.find("a", attrs={"class": "a-link-normal aok-block"})
            rating = product.find("span", class_="a-size-small")
            price = product.find("span", class_=["_cDEzb_p13n-sc-price_3mJ9Z", "p13n-sc-price"])
            item = {
                "id": id_tag["data-asin"] if id_tag and id_tag["data-asin"] else "N/A",
                "top": top.text.strip() if top else "N/A",
                "link": f"https://www.amazon.com{link['href']}" if link else "N/A",
                "rating_count": rating.text.strip() if rating else "N/A",
                "price": price.text.strip() if price else "N/A"
            }
            data.append(item)
        logging.info(f"Scraped {len(data)} products from page {page_num}")
        return data
    
    # Phân tích chi tiết sản phẩm
    def _parse_product_details(self, soup, link):
        breadcrumbs = [a.text.strip() for a in soup.find_all("a", class_="a-link-normal a-color-tertiary")]
        skin_type = breadcrumbs[2] if len(breadcrumbs) > 2 else "N/A"
        category = breadcrumbs[-1] if breadcrumbs else "N/A"
        if not breadcrumbs:
            logging.warning(f"No breadcrumbs found for {link}")

        brand_tag = soup.find("span", class_="a-size-base a-text-bold", string="Brand")
        brand = brand_tag.find_next("span", class_="a-size-base po-break-word").text.strip() if brand_tag else "N/A"

        social_proof = soup.find("div", id="socialProofingAsinFaceout_feature_div")
        bought_info = "N/A"
        if social_proof:
            title_tag = social_proof.find("span", id="social-proofing-faceout-title-tk_bought")
            if title_tag:
                bought_text = title_tag.find("span", class_="a-text-bold")
                bought_info = bought_text.text.strip() if bought_text else "N/A"
                if "in past month" in title_tag.text:
                    bought_info += " in past month"

        return {"skin_type": skin_type, "category": category, "brand": brand, "bought_info": bought_info}

    # Lưu dữ liệu vào CSV
    def _save_to_csv(self, data):
        if not data:
            logging.warning("No data to save.")
            return
        with open(self.output_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Saved {len(data)} products to {self.output_file}")

    # Hàm chính để chạy scraper
    def scrape(self):
        all_data = []
        try: 
            for page in range(1, self.num_pages + 1):
                logging.info(f"Scraping page {page}")
                top_products = self._parse_top_products(page)
                for product in top_products:
                    link = product["link"]
                    if link == "N/A":
                        logging.info(f"Skipping product with no link: {product['id']}")
                        continue
                    # Thử dùng requests trước
                    soup = self._fetch_page(link)
                    if soup and not soup.find("div", id="wayfinding-breadcrumbs_feature_div"):
                        # Nếu không tìm thấy breadcrumbs, chuyển sang Selenium
                        logging.info(f"Breadcrumbs not found with requests, switching to Selenium for {link}")
                        soup = self._fetch_page(link, use_selenium=True)
                    if soup:
                        details = self._parse_product_details(soup, link)
                        all_data.append({**product, **details})
                        logging.info(f"Scraped details for product {product['id']}")
                    else:
                        logging.error(f"Failed to load page for {link}")
                    time.sleep(random.uniform(5, 10))
            self._save_to_csv(all_data)
        finally: 
            self._close_driver()

if __name__ == "__main__":
    url_template = "https://www.amazon.com/Best-Sellers-Beauty-Personal-Care-Skin-Care-Products/zgbs/beauty/11060451/ref=zg_bs_nav_beauty_1?pg={}"
    scraper = AmazonScraper(url_template, num_pages=2, scroll_times=5, output_file="raw.csv")
    scraper.scrape()