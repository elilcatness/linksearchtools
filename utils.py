from selenium.webdriver import Chrome, ChromeOptions


def get_driver(path='chromedriver'):
    options = ChromeOptions()
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.124 Safari/537.36')
    # options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    # options.add_argument('--no-sandbox')
    return Chrome(path, options=options)


def parse_headers(driver: Chrome):
    labels = driver.find_elements_by_xpath('//*[@class="data-table__header-label"]/span')
    return [label.get_property('innerHTML').replace('<br>', ' ').strip() for label in labels]


def get_pages_count(driver: Chrome):
    pagination_block = driver.find_element_by_xpath('//ul[@class="pagination"]')
    buttons = pagination_block.find_elements_by_xpath('.//button[@class="page-link"]')
    try:
        return int(''.join(buttons[-2].text.split(',')))
    except (IndexError, ValueError):
        return None


def get_next_btn(driver: Chrome):
    return driver.find_element_by_xpath('//li[@title="Next"]/button[@class="page-link"]')


def get_total_count(driver: Chrome):
    try:
        return int(driver.find_element_by_class_name(
            'display-summary__short-summary').text.split()[0].replace(',', ''))
    except (IndexError, ValueError):
        return 0