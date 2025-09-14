import os

BOT_NAME = "lianjia"
SPIDER_MODULES = ["lianjia.spiders"]
NEWSPIDER_MODULE = "lianjia.spiders"

ROBOTSTXT_OBEY = False    # 仅用于工程演示。生产务必遵循网站协议与法律合规。
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.8
RANDOMIZE_DOWNLOAD_DELAY = True
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [403, 404, 412, 418, 429, 500, 502, 503, 504]

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

DOWNLOADER_MIDDLEWARES = {
    "lianjia.middlewares.AntiBanMiddleware": 543,
}

ITEM_PIPELINES = {
    "lianjia.pipelines.SaveToCSV": 300,
}

# 输出目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 从 .env 读取起始配置
from dotenv import load_dotenv
load_dotenv()
START_URL = os.getenv("START_URL", "https://xm.lianjia.com/ershoufang/")
DISTRICTS = [x.strip() for x in os.getenv("DISTRICTS", "思明,湖里,集美,翔安,同安,海沧").split(",") if x.strip()]
