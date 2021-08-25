# Add your headers or info cases handling functions here


def regular_case(cell):
    return cell.text.strip().replace('\n', ' ')


def url_case(cell):
    try:
        return 'https://' + cell.find_element_by_xpath(
            './/span[starts-with(@class, "url-fragment url-fragment__l3")]').text
    except AttributeError:
        return regular_case(cell)