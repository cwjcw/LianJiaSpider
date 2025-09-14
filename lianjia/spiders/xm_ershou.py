import os, time, re
import scrapy
from urllib.parse import urljoin
from lianjia.items import HouseItem
from lianjia.utils.parsers import parse_jsonld, parse_detail_init_block
from lianjia import settings as S

def now_str():
    return time.strftime("%Y-%m-%d %H:%M:%S")

class XmErshouSpider(scrapy.Spider):
    name = "xm_ershou"
    allowed_domains = ["xm.lianjia.com", "lianjia.com", "s1.ljcdn.com"]
    custom_settings = {
        "DOWNLOAD_DELAY": 0.8,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 8,
    }

    def start_requests(self):
        start = S.START_URL
        # 入口：城市二手房首页
        yield scrapy.Request(start, callback=self.parse_home, dont_filter=True)

    def parse_home(self, response):
        # 在“区域”里挑你指定的区（思明、湖里、...）
        # 链家区域链接通常形如 https://xm.lianjia.com/ershoufang/siming/
        for d in S.DISTRICTS:
            # 先尝试直接拼音路由（常见）：/ershoufang/{pinyin}/
            # 如果你需要精准从页面 DOM 提取，也可以用 xpath 查找包含区名的 a 标签再取 href。
            href_guess = urljoin(response.url, f"./{self.cn2py(d)}/")
            yield scrapy.Request(href_guess, callback=self.parse_district, meta={"district": d}, dont_filter=True)

    # 简易中文→拼音兜底（只覆盖本项目 6 个区名）
    def cn2py(self, name):
        mapping = {"思明":"siming","湖里":"huli","集美":"jimei","翔安":"xiangan","同安":"tongan","海沧":"haicang"}
        return mapping.get(name, name)

    def parse_district(self, response):
        district = response.meta["district"]
        # 片区/商圈列表的链接，一般在筛选区块里，url 类似 /ershoufang/bailuzhou/
        # 用包含区名或“商圈”节点下的 a 收集：
        sub_links = set()

        # 1) 直接在页面上收集形如 /ershoufang/{bizcircle}/ 的链接
        for a in response.xpath('//a[contains(@href, "/ershoufang/")]/@href').getall():
            if re.search(r"/ershoufang/[^/]+/?$", a):
                sub_links.add(urljoin(response.url, a))

        # 2) 去重并下发（真实线上会有不少“特色/地铁”等，也一起下发没关系，后续 parse_list 过滤）
        for href in sorted(sub_links):
            yield scrapy.Request(href, callback=self.parse_list, meta={"district": district, "bizcircle_url": href})

    def parse_list(self, response):
        district = response.meta.get("district")
        bizcircle = self.guess_bizcircle_from_url(response.url)
        # 列表页每条房源卡片：提取详情链接 + 页面上能拿到的结构化信息
        # 常见详情链接：/ershoufang/105118866089.html
        detail_links = response.xpath('//a[contains(@href,"/ershoufang/") and contains(@href,".html")]/@href').getall()
        for href in detail_links:
            url = urljoin(response.url, href)
            yield scrapy.Request(url, callback=self.parse_detail, meta={
                "district": district,
                "bizcircle": bizcircle
            })

        # 翻页：查 “下一页” 或 ?pg2 之类
        next_href = response.xpath('//a[contains(@class,"next") or contains(text(),"下一页")]/@href').get()
        if next_href:
            yield scrapy.Request(urljoin(response.url, next_href), callback=self.parse_list, meta=response.meta)

    def guess_bizcircle_from_url(self, url):
        # 片区路由通常是 /ershoufang/bailuzhou/ 这种
        m = re.search(r"/ershoufang/([^/]+)/?$", url)
        return m.group(1) if m else ""

    def parse_detail(self, response):
        item = HouseItem()
        item["url"] = response.url
        item["district"] = response.meta.get("district")
        item["bizcircle"] = response.meta.get("bizcircle")

        # 标题
        title = response.xpath("//title/text()").get() or ""
        item["title"] = title.strip()

        # JSON-LD（含价格、面积、户型等，见你给的详情页源码）：
        # application/ld+json 内含 offers.price/ floorSize/ numberOfRooms 等
        jd = parse_jsonld(response)
        # 兜底：detailV3.init({...})（见源码中的 init 字段 totalPrice/price/area 等）
        initk = parse_detail_init_block(response.text)

        # house_id
        m = re.search(r"/ershoufang/(\d+)\.html", response.url)
        item["house_id"] = m.group(1) if m else initk.get("houseId")

        # 价格
        # 优先 detailV3 数值，其次 JSON-LD 文本（如“498万”）
        item["total_price_wan"] = initk.get("totalPrice") or (jd.get("jsonld_price_text") or "").replace("万","").strip()
        item["unit_price"] = initk.get("price")

        # 面积/户型
        item["area_sqm"] = initk.get("area") or jd.get("jsonld_area")
        item["rooms"] = jd.get("jsonld_rooms")

        # 从“房屋基本信息”一行抓更多文本（示例在列表页 DOM 也有 “3室2厅 | 131.52平米 | 朝向 | 楼层 | 年份 | 结构”）
        info_text = response.xpath('string(//div[contains(@class,"houseInfo")])').get()
        if info_text:
            t = " ".join(info_text.split())
            item["orientation"] = self.pick_orient(t)
            item["floor_info"] = self.pick_floor(t)
            item["year"] = self.pick_year(t)
            item["building_type"] = self.pick_building(t)
            if not item.get("rooms"):
                item["rooms"] = self.pick_rooms(t)
            if not item.get("area_sqm"):
                item["area_sqm"] = self.pick_area(t)

        # 小区名与链接（在面包屑/位置模块能找到，示例片段显示小区链接 + 片区“白鹭洲”）：
        # <div class="positionInfo"> <a href=".../xiaoqu/xxx/">国贸花园</a> - <a href=".../ershoufang/bailuzhou/">白鹭洲</a>
        comm_a = response.xpath('//div[contains(@class,"positionInfo")]//a[contains(@href,"/xiaoqu/")][1]')
        item["community_name"] = (comm_a.xpath("text()").get() or "").strip()
        item["community_url"] = comm_a.xpath("@href").get()

        # 描述/标签（若有）
        item["listed_desc"] = " | ".join(x.strip() for x in response.xpath('//div[contains(@class,"keyDetail") or contains(@class,"tag")]/text()').getall() if x.strip())
        item["crawl_time"] = now_str()
        yield item

    # ——若页面不同形态，下面这些提取器做兜底——
    def pick_rooms(self, text):
        m = re.search(r"(\d室\d厅)", text)
        return m.group(1) if m else ""

    def pick_area(self, text):
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*平米", text)
        return m.group(1) if m else ""

    def pick_orient(self, text):
        m = re.search(r"(东南|东北|西南|西北|南北|朝[东南西北中]|[东南西北]{1,2})", text)
        return m.group(1) if m else ""

    def pick_floor(self, text):
        m = re.search(r"(低楼层|中楼层|高楼层|共\d+层|\d+层)", text)
        return m.group(1) if m else ""

    def pick_year(self, text):
        m = re.search(r"(\d{4})年", text)
        return m.group(1) if m else ""

    def pick_building(self, text):
        m = re.search(r"(板楼|塔楼|板塔结合|其他)", text)
        return m.group(1) if m else ""
