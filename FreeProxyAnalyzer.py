from queue import PriorityQueue


class SifterFreeProxy:
    def __init__(self, proxy_type: str, file_txt: str):
        self.proxies_type = proxy_type
        self.file_proxies = file_txt
        self.proxy_queue = PriorityQueue()

    def proxy_empty(self):
        return self.proxy_queue.empty()

    @staticmethod
    def _add_fail(proxies):
        fail_count = proxies[0]
        if fail_count < 0:
            fail_count = 0
        fail_count += 1
        return fail_count, proxies[1]

    @staticmethod
    def _add_working(proxies):
        fail_count = proxies[0]
        if fail_count == -2:
            pass
        elif fail_count >= 0:
            fail_count -= 1
        return fail_count, proxies[1]

    @staticmethod
    def _proxy_is_bad(proxies):
        fail_count = proxies[0]
        if fail_count == 3:
            return True
        return False

    def get_proxy(self):
        if not self.proxy_empty():
            return self.proxy_queue.get()
        raise ValueError('Proxy queue is empty')

    def set_queue_from_file(self):
        if self.file_proxies:
            with open(self.file_proxies, 'r') as rd_file:
                for proxies in rd_file.readlines():
                    if proxies:
                        self.proxy_queue.put((0, f'{self.proxies_type}://{proxies.strip()}'))
        else:
            raise FileExistsError(f'File <{self.file_proxies}> not found')

    def put_back(self, proxies: tuple, bad_response=False):
        if bad_response:
            proxies = self._add_fail(proxies)
        else:
            proxies = self._add_working(proxies)
        if not self._proxy_is_bad(proxies):
            self.proxy_queue.put(proxies)

    def get_size(self):
        return self.proxy_queue.qsize()


if __name__ == '__main__':
    proxy = SifterFreeProxy('socks5', 'some_garbage/proxy.txt')
    proxy.set_queue_from_file()
    some_proxy = proxy.get_proxy()
    proxy.put_back(some_proxy)
    new_proxy = proxy.get_proxy()
    print('ok')
