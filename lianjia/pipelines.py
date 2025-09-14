import csv, os, time
from scrapy.exceptions import DropItem
from .settings import DATA_DIR

class SaveToCSV:
    def open_spider(self, spider):
        ts = time.strftime("%Y%m%d")
        self.fp = open(os.path.join(DATA_DIR, f"xiamen_ershou_{ts}.csv"), "a", newline="", encoding="utf-8-sig")
        self.writer = csv.writer(self.fp)
        if self.fp.tell() == 0:
            self.writer.writerow([
                "house_id","title","url","district","bizcircle",
                "community_name","community_url","total_price_wan","unit_price",
                "area_sqm","rooms","orientation","floor_info","year","building_type",
                "listed_desc","crawl_time"
            ])

    def process_item(self, item, spider):
        if not item.get("url"):
            raise DropItem("no url")
        self.writer.writerow([
            item.get("house_id",""), item.get("title",""), item.get("url",""),
            item.get("district",""), item.get("bizcircle",""),
            item.get("community_name",""), item.get("community_url",""),
            item.get("total_price_wan",""), item.get("unit_price",""),
            item.get("area_sqm",""), item.get("rooms",""),
            item.get("orientation",""), item.get("floor_info",""),
            item.get("year",""), item.get("building_type",""),
            item.get("listed_desc",""), item.get("crawl_time","")
        ])
        return item

    def close_spider(self, spider):
        self.fp.close()
