import re

import requests
from scrapy import Selector
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.remote_connection import LOGGER
import logging
import time
import os
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image

proxy_host = "proxy.crawlera.com"
proxy_port = "8011"
proxy_auth = "913da34079284ae5918cd2696843698f:"  # Make sure to include ':' at the end
proxies = {"https": "http://{}@{}:{}/".format(proxy_auth, proxy_host, proxy_port),
           "http": "http://{}@{}:{}/".format(proxy_auth, proxy_host, proxy_port)}
script_dir = os.path.dirname(os.path.abspath(__file__))
verify = False  # os.path.join(script_dir, 'zyte-ca.crt')


# def scrape_property(property_url):
#     url = property_url
#     headers = {
#         'authority': 'streeteasy.com',
#         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         'accept-language': 'en-US,en;q=0.9',
#         'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'document',
#         'sec-fetch-mode': 'navigate',
#         'sec-fetch-site': 'none',
#         'sec-fetch-user': '?1',
#         'upgrade-insecure-requests': '1',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
#     }
#     response = requests.get(url, headers=headers, proxies=proxies, verify=verify)
#     print("Response -> ", response)
#     css_response = Selector(text=response.text)
#     print('css_response', css_response)
#     # raw_units = css_response.css(".address.BuildingUnit-address a")
#     raw_units = css_response.css(".BuildingUnit-table tbody tr")
#     print('raw_units', raw_units)
#     units = []
#     for raw_unit in raw_units:
#         price = raw_unit.css('.BuildingUnit-price .price::text').get()
#         cleaned_price = re.sub(r'\D', '', price)
#         units.append({
#             'title': raw_unit.css('.address.BuildingUnit-address a::text').get(),
#             'url': raw_unit.css('.address.BuildingUnit-address a::attr(href)').get(),
#             'price': cleaned_price,
#             'beds': raw_unit.css('.BuildingUnit-bedrooms::text').get(),
#             'baths': raw_unit.css('.BuildingUnit-bathrooms::text').get(),
#         })
#     return units

def scrape_property(property_url):
    url = property_url
    headers = {
        'authority': 'streeteasy.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    response = requests.get(url, headers=headers, proxies=proxies, verify=verify)
    print("Response -> ", response)
    css_response = Selector(text=response.text)
    # raw_units = css_response.css(".address.BuildingUnit-address a")
    # units = []
    # for raw_unit in raw_units:
    #     units.append({
    #         'title': raw_unit.css('::text').get(),
    #         'url': raw_unit.css('::attr(href)').get()
    #     })
    raw_units = css_response.css(".BuildingUnit-table tbody tr")
    print('raw_units', raw_units)
    units = []
    for raw_unit in raw_units:
        price = raw_unit.css('.BuildingUnit-price .price::text').get()
        cleaned_price = re.sub(r'\D', '', price)
        units.append({
            'title': raw_unit.css('.address.BuildingUnit-address a::text').get(),
            'url': raw_unit.css('.address.BuildingUnit-address a::attr(href)').get(),
            'price': cleaned_price,
            'beds': raw_unit.css('.BuildingUnit-bedrooms::text').get().strip(),
            'baths': raw_unit.css('.BuildingUnit-bathrooms::text').get().strip(),
        })
    return units





def scrape_unit(unit_url):
    headers = {
        'authority': 'streeteasy.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    response = requests.get(unit_url, proxies=proxies, verify=verify, headers=headers)
    try:
        net_ef_rent = response.text.split('netEffectivePrice":"')[1].split('"')[0]
    except:
        net_ef_rent = ''
    response = Selector(text=response.text)

    item = {'title': response.css(".building-title a::text").get('').split(" #")[0],
            'unit': response.css(".building-title a::text").get('').split(" #")[-1],
            'complete_title': response.css(".building-title a::text").get('')}
    raw_price = " ".join([i.strip() for i in response.css(".price *::text").extract() if i.strip()])
    beds = response.xpath("//div[@class='details_info']/ul/li[contains(text(),'bed')]/text()").get('')
    print(f"beds {beds}")
    if beds:
        item['beds'] = beds.replace('beds', '').replace('bed', '').strip()
        print(f"item beds {item['beds']}")
    else:
        item['beds'] = '0'

    baths = response.css(".last_detail_cell::text").get('').split(" ")[0]
    item['baths'] = baths
    raw_price = raw_price.replace(",", "")
    raw_price = ''.join(filter(str.isdigit, raw_price))
    item['price'] = 0
    if net_ef_rent:
        net_ef_rent = net_ef_rent.replace(",", "").replace("$", "")
        item['price'] = float((int(net_ef_rent)))
    else:
        if raw_price:
            item['price'] = float(int(raw_price))
    item['image_urls'] = ','.join(
        [x for x in response.css('.jsFlickityImageWrapper img::attr(data-src-original)').extract()])
    item['image_paths'] = [f"images/{count + 1}.jpg" for count in
                          range(0, len(item['image_urls'].split(',')))]

    description_1 = " ".join(response.css("#full-content p *::text").extract())
    description_2 = []
    detail_nodes = response.xpath("//script[contains(text(),'rentalPricesAndTerms')]/text()").get('')
    if detail_nodes:
        detail_nodes = detail_nodes.split('=')[1].strip()
        try:
            free_months = detail_nodes.split('freeMonths":')[1].split(',')[0]
        except:
            free_months = ''
        try:
            lease_months = detail_nodes.split('leaseTerm":')[1].split(',')[0]
        except:
            lease_months = ''
        if free_months and lease_months:
            description_2 = '{} Month Free , {}-Month Lease'.format(free_months, lease_months)
        item['description'] = '{} {}'.format(description_1, description_2)
    else:
        item['description'] = description_1
    amenities = []
    amenities += [i.strip() for i in response.css(".AmenitiesBlock .Text::text").extract()]
    amenities += [i.strip() for i in response.css(".AmenitiesBlock-item::text").extract() if i.strip()]
    item['amenities'] = amenities
    return item


def upload_item(item):
    headers = {
        'authority': 'streeteasy.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    try:
        for index, image_url in enumerate(item.get('image_urls', []).split(','), start=1):
            img_data = requests.get(url=image_url)
            if img_data.status_code == 200:
                if not os.path.exists(f"images/{item['complete_title']}"):
                    os.makedirs(f"images/{item['complete_title']}")
                with open(f"images/{item['complete_title']}/{index}.jpg", 'wb') as handler:
                    handler.write(img_data.content)
            else:
                print('Unable to get Response')
    except Exception as e:
        return e
    # try:
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=C:\Profile")
    options.add_argument("--start-maximized")
    LOGGER.setLevel(logging.WARNING)
    options.add_argument("--enable-password-saving")
    driver = webdriver.Chrome(executable_path='chromedriver.exe', options=options)
    driver.get("http://roslisting.com/admin2/login.cfm")
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, "email"))).send_keys('vishal')
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, "password"))).send_keys('12345')
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))).click()
    menu_frame = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "menuFrame")))
    driver.switch_to.frame(menu_frame)
    time.sleep(2)
    listing_url = driver.find_element(By.CSS_SELECTOR, '.listingsBorder [target="mainFrame"]').get_attribute("href")
    driver.get(listing_url)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "inputAddress"))).send_keys(item['title'])
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()
    real_name = item['title'].lower()
    response = Selector(text=driver.page_source)
    for index, iterate in enumerate(response.css(".table tr~tr"), start=1):
        name_on_website = iterate.css("td a strong::text").get().lower()
        if real_name.strip() in name_on_website.strip():
            if "Apartment" in iterate.css("td+td strong::text").get(''):
                driver.find_element(By.CSS_SELECTOR, f".table tbody tr:nth-child({index + 1}) a").click()
                break
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, "Apt"))).send_keys(item['unit'])
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="Status"] [value="2"]'))).click()
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, 'beds'))).send_keys(item['beds'])
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, 'bath'))).clear()
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.NAME, 'bath'))).send_keys(item['baths'])
    if item.get('convertible'):
        count = item.get('convertible').replace("+", '')
        count = int(count)
        if count in [1, 2]:
            driver.find_element(By.CSS_SELECTOR, f'#convertible [value="{count}"]').click()
            time.sleep(2)
    if item.get("net effective"):
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'NER'))).click()
        time.sleep(2)
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, 'Price'))).send_keys(
        str(item['price']))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, 'showAddressAs'))).send_keys(
        'property_for_rent')
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'Ad'))).click()
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'selectMaketALL'))).click()
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[valign="top"] [name="Features1"]'))).send_keys(
        item['description'])
    if 'Balcony' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Balcony'))).click()
    if 'Duplex' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Duplex'))).click()
    if 'Free Rent' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'FreeRent'))).click()
    if 'Granite Kitchen' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'GraniteKitchen'))).click()
    if 'Laundry In Unit' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'LaundryInUnit'))).click()
    if 'Loft' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Loft'))).click()
    if 'Multi Level' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'MultiLevel'))).click()
    if 'Original Details' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'OriginalDetails'))).click()
    if 'Penthouse' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Penthouse'))).click()
    if 'Room For Rent' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'RoomForRent'))).click()
    if 'Triplex' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Triplex'))).click()
    if 'Wall to Wall Carpeting' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'WalltoWallCarpeting'))).click()
    if 'Wine Cooler' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'WineCooler'))).click()
    if 'Dining Room' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'DiningRoom'))).click()
    if 'Eat In Kitchen' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'EatInKitchen'))).click()
    if 'Furnished' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Furnished'))).click()
    if 'Hardwood' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Hardwood'))).click()
    if 'Light' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Light'))).click()
    if 'Marble Bath' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'MarbleBath'))).click()
    if 'NO FEE' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'NOFEE'))).click()
    if 'Outdoor Space' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'OutdoorSpace'))).click()
    if 'Private Deck' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'PrivateDeck'))).click()
    if 'Stainless Steel Appliances' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'StainlessSteelAppliances'))).click()
    if 'Vacation Rental' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'VacationRental'))).click()
    if 'WallsOK' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'WallsOK'))).click()
    if 'Dishwasher' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Dishwasher'))).click()
    if 'Fireplace' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Fireplace'))).click()
    if 'Garden' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Garden'))).click()
    if 'High Ceilings' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'High Ceilings'))).click()
    if 'Live Work' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'LiveWork'))).click()
    if 'Microwave' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Microwave'))).click()
    if 'Open Kitchen' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'OpenKitchen'))).click()
    if 'Patio' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Patio'))).click()
    if 'Renovated' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Renovated'))).click()
    if 'Terrace' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Terrace'))).click()
    if 'Walk In Closet' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'WalkInCloset'))).click()
    if 'Washer' in item['amenities']:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Washer'))).click()
    # VIEWS
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'CityView'))).click()
    # EXPOSURE
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'exposureEast'))).click()
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="condition"] [value="1"]'))).click()
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="pets"] [value="3"]'))).click()
    # parking
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="cooling"] [value="1"]'))).click()
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="parking"] [value="5"]'))).click()
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="heating"] [value="4"]'))).click()
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[name="cooling"] [value="1"]'))).click()
    # UTILITIES
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Gas'))).click()
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'water'))).click()
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'AC'))).click()
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Heat'))).click()
    time.sleep(2)
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'photoButton'))).click()
    cwd = os.getcwd()
    folder_path = os.path.join(cwd, 'images\{}'.format(item['complete_title']))
    images = os.listdir(folder_path)
    sorted_images = sorted(images, key=lambda x: int(x.split('.')[0]))
    time.sleep(3)
    drag_and_drop_box = driver.find_element(By.XPATH, "//div[@id='uploader_buttons']/div/input")
    for image in sorted_images:
        time.sleep(0.5)
        image_path = os.path.join(folder_path, image)
        image_path = optimize_image(image_path)
        drag_and_drop_box.send_keys(image_path)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'uploader_start'))).click()
    while True:
        status = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//td[@class='plupload_file_status']/span")))
        if status.text == '100%':
            break
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'floatingSubmitBtn'))).click()
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'confirm'))).click()
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//h1[@class='listings printh1']")))
    page_source = driver.page_source
    print("page",page_source)
    return 'uploaded'
    # except Exception as e:
    #     return e


def optimize_image(image_path):
    image = Image.open(image_path)
    if image.info.get("icc_profile"):
        del image.info["icc_profile"]
    image.save(image_path)
    return image_path


if __name__ == "__main__":
    item = scrape_unit('https://streeteasy.com/building/70-pine-street-new_york/ph5902')
    upload_item(item)
