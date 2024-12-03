import requests
import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def parse_sanrio_products_links(page):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    response = requests.get(f'https://www.kawaii-limited.com/brands/sanrio?page={page}', headers={'user-agent': user_agent})

    soup = BeautifulSoup(response.text, 'lxml')
    divs = soup.find_all(class_='product-box')

    links = []
    for div in divs:
        href = div.find('a').get('href')
        links.append(href)

    return links

def parse_barcodes(link):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    response = requests.get(f'https://www.kawaii-limited.com{link}', headers={'user-agent': user_agent})

    soup = BeautifulSoup(response.text, 'lxml')

    dt = soup.find("dt", string="Barcode")
    if dt:
        barcode = dt.find_next_sibling("dd").text
    else:
        return None

    dt = soup.find("dt", string="Modal No.")
    if dt:
        sanrio_id = dt.find_next_sibling("dd").text
    else:
        return None

    return (barcode, sanrio_id)

def parse_sanrio(sanrio_id):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 5)
    result = []

    driver.get('https://shop.sanrio.co.jp')

    driver.implicitly_wait(10)
    search_input = driver.find_element(By.ID, "form_freeword")
    search_input.send_keys(sanrio_id)
    search_button = driver.find_element(By.CSS_SELECTOR, "#form_freeword + button")
    search_button.click()
    driver.implicitly_wait(10)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    element = soup.find("li", class_="c-goods-item")
    if element:
        name = element.find("p", class_="c-goods-item__name").text
        price = element.find("p", class_="c-goods-item__price").text

        return (name, price)
    else:
        return None


if __name__ == '__main__':
    filename = 'output.db'

    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    sql = """
        create table if not exists sanrio_products (
            barcode text,
            sanrio_id text,
            name text,
            price text
        )
    """
    cursor.execute(sql)

    links = parse_sanrio_products_links(1)
    for link in links:
        result = parse_barcodes(link)
        if result is not None:
            (barcode, sanrio_id) = result
            sanrio_data = parse_sanrio(sanrio_id)
            if sanrio_data is not None:
                (name, price) = sanrio_data
                cursor.execute("""
                    insert into sanrio_products (barcode, sanrio_id, name, price)
                    values (?, ?, ?, ?)
                """, (barcode, sanrio_id, name, price))

    conn.commit()
    conn.close()
