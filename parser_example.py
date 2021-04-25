import requests
from bs4 import BeautifulSoup
from queue import Queue
from FreeProxyAnalyzer import SifterFreeProxy
import csv
from time import sleep
import threading


class DataScrap:
    def __init__(self, organization_name=None, director=None, address=None, inn=None, create_date=None):
        self.organization_name = organization_name
        self.director = director
        self.address = address
        self.inn = inn
        self.create_date = create_date

    def get_values(self):
        return self.__dict__


class RusProfileParser:
    HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'}
    check_writable = True

    def __init__(self):
        self.main_url = 'https://www.rusprofile.ru/codes/310000'
        self.max_page = 20  # 353
        self.template_data = Queue()
        self.proxy = SifterFreeProxy('socks5', 'some_garbage/proxy.txt')
        self.proxy.set_queue_from_file()
        self.all_pages = Queue()
        self.checker_data = Queue()

    def write_values(self):
        while self.check_writable:
            if not self.template_data.empty():
                with open('some_garbage/RESULTAT.csv', 'a', newline='') as wrt_csv:
                    fields = ['organization_name', 'director', 'inn', 'create_date', 'address']
                    csv_write = csv.DictWriter(wrt_csv, fieldnames=fields, delimiter=';')
                    while not self.template_data.empty():
                        write_row = self.template_data.get()
                        csv_write.writerow(write_row.get_values())
                        self.template_data.task_done()
            else:
                sleep(0.2)

    def prepare_all_pages(self):
        for num in range(1, self.max_page + 1):
            self.all_pages.put(f'{self.main_url}/{num}')

    def get_page(self, url):
        proxy = self.proxy.get_proxy()
        proxies = {
            'http': {proxy[1]},
            'https': {proxy[1]},
        }
        try:
            page = requests.get(url, headers=self.HEADER, proxies=proxies, timeout=10)
        except:
            self.proxy.put_back(proxy, bad_response=True)
            return False
        else:
            if page.status_code == 200:
                # print(proxy)
                self.proxy.put_back(proxy)
                return page.text
            self.proxy.put_back(proxy, bad_response=True)
            return False

    def find_values_in_html(self, page):
        soup = BeautifulSoup(page, 'lxml')
        all_organizations = soup.find_all('div', attrs={'class': 'company-item'})
        captcha_find = soup.find('div', attrs={'class': 'captcha-section'})
        if captcha_find:
            # print('CAPTCHA FIND')
            return False
        if all_organizations:
            for organization in all_organizations:
                organization_name = organization.find('div', attrs={'class': 'company-item__title'})
                address = organization.find('address', attrs={'class': 'company-item__text'})
                raw_other = organization.find_all('dd', attrs={'class': None})
                if raw_other and len(raw_other) >= 5:
                    director = raw_other[0].text.strip()
                    inn = raw_other[1].text.strip()
                    create_date = raw_other[3].text.strip()
                    if all([organization_name, address, director, inn, create_date]):
                        self.template_data.put(DataScrap(organization_name=organization_name.text.strip(),
                                                         director=director,
                                                         address=address.text.strip(),
                                                         inn=inn,
                                                         create_date=create_date))
                    else:
                        return False
                else:
                    return False
            return True
        return False

    def parser(self):
        while not self.all_pages.empty():
            url = self.all_pages.get()
            page = self.get_page(url)
            if page:
                checker_values = self.find_values_in_html(page)
                if all((page, checker_values)):
                    print(f'Незавершенных заданий: {self.all_pages.unfinished_tasks} из {self.max_page}')
                else:
                    self.all_pages.put(url)
            else:
                self.all_pages.put(url)
            self.all_pages.task_done()


if __name__ == '__main__':
    experiment = RusProfileParser()
    experiment.prepare_all_pages()
    write_threading = threading.Thread(target=experiment.write_values, daemon=True)
    write_threading.start()
    for _ in range(10):
        _ = threading.Thread(target=experiment.parser, daemon=True)
        _.start()
    experiment.all_pages.join()
    experiment.template_data.join()
    experiment.check_writable = False
    
