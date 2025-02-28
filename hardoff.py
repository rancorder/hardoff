import os
import requests
import time
import traceback
import concurrent.futures
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import threading

# 環境変数から API トークンとルーム ID を取得
CHATWORK_API_TOKEN = os.getenv("CHATWORK_API_TOKEN")
CHATWORK_ROOM_ID = os.getenv("CHATWORK_ROOM_ID")

LOG_FILE = "hardoff_log.txt"
URLS = {
    "OFF_camera": {"url": "https://netmall.hardoff.co.jp/cate/0001000300020002/"},
    "OFF_dejicame": {"url": "https://netmall.hardoff.co.jp/cate/00010003000200010001/"},
    "OFF_lens": {"url": "https://netmall.hardoff.co.jp/cate/000100030001/"},
    "OFF_accessory": {"url": "https://netmall.hardoff.co.jp/cate/000100030003/"},
    "OFF_analog": {"url": "https://netmall.hardoff.co.jp/cate/00010004000100010003/"},
    "OFF_binoculars": {"url": "https://netmall.hardoff.co.jp/cate/000100030005/"},
}

previous_data = {}
first_run = True

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"- [{timestamp}] {message.ljust(50)}"
    print(log_entry, flush=True)  # Renderのログに出力
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry + "\n")

def send_chatwork_notification(site_name, product_name, price, url):
    if not CHATWORK_API_TOKEN or not CHATWORK_ROOM_ID:
        log_message("⚠️ ChatWork APIの環境変数が設定されていません。")
        return

    headers = {"X-ChatWorkToken": CHATWORK_API_TOKEN}
    message = (
        f"📢 *{site_name} に新商品が追加されました！*\n"
        f"🛒 商品名: {product_name}\n"
        f"💰 価格: {price}\n"
        f"🔗 [商品ページはこちら]({url})"
    )
    payload = {"body": message}
    url_endpoint = f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/messages"
    try:
        response = requests.post(url_endpoint, headers=headers, data=payload)
        if response.status_code == 200:
            log_message(f"📢 Chatwork通知送信成功: {message}")
        else:
            log_message(f"⚠️ Chatwork通知失敗: {response.text}")
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Chatwork通知エラー: {e}")

def fetch_and_compare(url, site_name, first_run=False, timeout=20):
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless=new")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())

    try:
        log_message(f"🌐 {site_name} からデータ取得中...")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        items = soup.find_all("div", class_="item-infowrap")
        if not items:
            log_message(f"⚠️ {site_name}: 商品情報が見つかりませんでした。")
            return None

        product_list = {}
        for item in items:
            name = item.find("div", class_="item-name").get_text(strip=True) if item.find("div", class_="item-name") else "N/A"
            price = item.find("span", class_="item-price-en").get_text(strip=True) if item.find("span", class_="item-price-en") else "N/A"
            product_list[name] = {"name": name, "price": price}
        
        log_message(f"✅ {site_name}: データ取得完了。商品数: {len(product_list)} 件")
        return product_list
    except Exception as e:
        log_message(f"❌ {site_name} のデータ取得失敗: {e}")
        log_message(traceback.format_exc())
        return None

def monitor_site(site_name, url):
    global first_run
    while True:
        log_message(f"🔍 {site_name} を巡回中...")
        new_data = fetch_and_compare(url, site_name, first_run)
        if new_data is not None:
            previous_data[site_name] = new_data
        if first_run:
            log_message("🚀 初回記録完了。通常監視モードへ移行。")
            first_run = False
        time.sleep(30)

def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(monitor_site, site_name, config["url"]): site_name for site_name, config in URLS.items()}
        for future in concurrent.futures.as_completed(futures):
            site_name = futures[future]
            try:
                future.result()
            except Exception as e:
                log_message(f"❌ スレッドエラー ({site_name}): {e}")

if __name__ == "__main__":
    main()
