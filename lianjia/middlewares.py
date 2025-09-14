import random
import time
from scrapy import signals
from w3lib.http import basic_auth_header
from .utils.proxies import kdl_proxy_url

UA_POOL = [
    # 若被封可补充更多真实常见 UA
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
]

class AntiBanMiddleware:
    def process_request(self, request, spider):
        # 随机 UA + Referer + 小随机延迟
        request.headers.setdefault(b"User-Agent", random.choice(UA_POOL).encode())
        request.headers.setdefault(b"Accept-Language", b"zh-CN,zh;q=0.9,en;q=0.8")
        if b"Referer" not in request.headers:
            request.headers[b"Referer"] = b"https://xm.lianjia.com/ershoufang/"

        # 加点随机抖动，避开固定节奏
        if random.random() < 0.4:
            time.sleep(random.uniform(0.5, 1.4))

        # 代理
        proxy = kdl_proxy_url()
        if proxy:
            request.meta["proxy"] = proxy
        return None

    def process_response(self, request, response, spider):
        # 遇到 403/412/418 等，切换 UA/代理并重试
        if response.status in (403, 404, 412, 418, 429, 503):
            request.headers[b"User-Agent"] = random.choice(UA_POOL).encode()
            request.dont_filter = True
            return request
        return response

class LianjiaDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        return s
