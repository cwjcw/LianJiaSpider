import scrapy

class HouseItem(scrapy.Item):
    house_id = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    district = scrapy.Field()     # 区：思明/湖里/...
    bizcircle = scrapy.Field()    # 片区：白鹭洲/滨东/...
    community_name = scrapy.Field()
    community_url = scrapy.Field()
    total_price_wan = scrapy.Field()  # 万
    unit_price = scrapy.Field()       # 元/平
    area_sqm = scrapy.Field()
    rooms = scrapy.Field()            # 3室2厅 等
    orientation = scrapy.Field()
    floor_info = scrapy.Field()
    year = scrapy.Field()
    building_type = scrapy.Field()
    listed_desc = scrapy.Field()      # 页面上类似“满五”等标签或描述
    crawl_time = scrapy.Field()
