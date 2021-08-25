import os
import sys
import time
from csv import DictWriter
from random import randint

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from cases import *
from utils import *


# Список кортежей ключ-значение функций-обработчиков иной обработки данных в столбцах таблицы
HEADERS_CASES = [(lambda header, cell: 'url' in header.lower(), url_case),
                 ('DTOXRISK', lambda cell: regular_case(cell).split(' ')[0]),
                 ('Page BL', lambda cell: regular_case(cell).replace(',', ''))]


def authorize(url, driver: Chrome, username, password, function_call=False):
    driver.get(url)
    fields = [{'name': 'username', 'id': 'username', 'val': username},
              {'name': 'password', 'id': 'password', 'val': password}]
    for i in range(len(fields)):
        try:
            field = driver.find_element_by_id(fields[i]['id'])
        except NoSuchElementException:
            return f'Failed to find {fields[i]["name"]} on {url}'
        for s in eval(fields[i]['name']):
            field.send_keys(s)
            time.sleep(float(f'0.{randint(2, 4)}'))
    driver.execute_script('document.getElementsByClassName("login__submit")[0].click();')
    if not function_call and driver.current_url == url:  # Небольшой костыль, ибо после
        authorize(url, driver, username, password, function_call=True)


def parse_page(driver: Chrome, headers, page_count, total_count):
    left_rows = driver.find_elements_by_xpath(
        '//*[@class="data-table__fixed-data data-table__fixed-data--left"]'
        '//div[starts-with(@class, "data-table__data-row-group")]'
    )  # Получение фиксированных рядов левой части
    middle_rows = driver.find_elements_by_xpath(
        '//*[@class="data-table__scrollable-data"]'
        '//div[starts-with(@class, "data-table__data-row-group")]'
    )  # Получение прокручиваемых рядов из центральной части
    data = []
    count = (page_count - 1) * 100  # hard-code alert!!!!!
    for left_row, middle_row in zip(left_rows, middle_rows):
        count += 1
        # Получение колонок из левой части
        left_cells = left_row.find_elements_by_xpath('.//div[starts-with(@class, "data-table__data-cell")]')
        # Отсечение чекбоксов
        left_cells = [cell for cell in left_cells if 'selectable' not in cell.get_attribute('class')]
        # Получение колонок из центра
        middle_cells = middle_row.find_elements_by_xpath('.//div[starts-with(@class, "data-table__data-cell")]')
        # Слияние списков для работы через индексы получаемых заголовков
        cells = left_cells + middle_cells
        item = {}
        for i, cell in enumerate(cells):
            if i in headers:
                header = headers[i]
                processed = False
                for key, process in HEADERS_CASES:  # Обработка необычных случаев
                    if (callable(key) and key(header, cell)) or key == header:
                        item[header] = process(cell)
                        processed = True
                        break
                if not processed:
                    item[header] = regular_case(cell)
        data.append(item)
        print(f'Parsed {count}/{total_count}', flush=True, end='\r')
    return data


def parse_pages(driver: Chrome, url, headers):
    driver.get(url)
    # Ожидание, пока не загрузится таблица
    WebDriverWait(driver, 60).until(
        ec.presence_of_element_located((By.CLASS_NAME, 'data-table__data-body')))
    page_headers = parse_headers(driver)
    page_headers_lowered = [header.lower() for header in page_headers]
    # Фильтрация получаемых заголовков на предмет их наличия в таблице на сайте
    headers = {page_headers_lowered.index(header.lower()): header for header in headers
               if header.lower() in page_headers_lowered}
    next_btn = get_next_btn(driver)
    if not next_btn:
        print('Failed to get next button')
        sys.exit(-1)
    total_count = get_total_count(driver)
    total_pages_count = get_pages_count(driver)
    page_count = 1
    yield parse_page(driver, headers, page_count, total_count)
    while page_count < total_pages_count:
        next_btn.click()
        # Ожидание, пока не разморозится таблица после перехода на новую страницу
        WebDriverWait(driver, 60).until_not(
            ec.presence_of_element_located((
                By.XPATH,
                '//*[starts-with(@class, "data-table__loading")]')))
        page_count += 1
        yield parse_page(driver, headers, page_count, total_count)
        next_btn = get_next_btn(driver)


def main(info_filename='info.txt', output_filename='output.csv'):
    driver = get_driver(os.path.join('binary', 'chromedriver.exe'))
    with open(info_filename, encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
        if not lines or len(lines) != 4:
            return f'Invalid input data in {info_filename}'
        # Четвёртой строкой в информационном файле должны идти заголовки конечного csv файла через ";"
        login_url, login_data, url, headers = lines
        try:
            username, password = login_data.split(':')
        except ValueError:
            return 'Invalid format of login data (username & password)'
        headers = headers.split(';')
    authorized = authorize(login_url, driver, username, password)
    if isinstance(authorized, str):
        return authorized
    with open(output_filename, 'w', newline='', encoding='utf-8') as f:
        writer = DictWriter(f, headers, delimiter=';')
        writer.writeheader()
    for data in parse_pages(driver, url, headers):
        with open(output_filename, 'a', newline='', encoding='utf-8') as f:
            writer = DictWriter(f, headers, delimiter=';')
            writer.writerows(data)


if __name__ == '__main__':
    start_time = time.time()
    callback = main()
    if callback:
        print(f'\n{callback}')
    else:
        print(f'\nCompleted in: {time.time() - start_time:.2f} seconds')
