import json
import re

def parse_jsonld(response):
    """解析详情页 application/ld+json。"""
    data = {}
    for sel in response.xpath('//script[@type="application/ld+json"]/text()'):
        try:
            j = json.loads(sel.get().strip())
        except Exception:
            continue
        # 有的页面是对象，有的是数组；只取包含价格/户型的
        if isinstance(j, dict):
            if j.get("@type") and "offers" in j:
                offers = j.get("offers", {})
                data["jsonld_price_text"] = offers.get("price")  # 如“498万”
            if "floorSize" in j:
                data["jsonld_area"] = j.get("floorSize")
            if "numberOfRooms" in j:
                data["jsonld_rooms"] = j.get("numberOfRooms")
        # 非标准结构时继续尝试
    return data

_DETAIL_INIT_RE = re.compile(r"detailV3\]\s*,\s*function\(init\)\s*{\s*init\((\{.*?\})\)", re.S)
_KV_RE = re.compile(r'(\w+)\s*:\s*([\'"]?[^,}]+[\'"]?)')

def parse_detail_init_block(response_text):
    """
    从 require(['ershoufang/sellDetail/detailV3'], function(init){ init({...}) })
    中抽取 totalPrice, price, area 等（数值更规整，便于统计）。
    """
    m = _DETAIL_INIT_RE.search(response_text)
    if not m:
        # 容错：直接找 totalPrice:'498' 等键值
        block = re.search(r"init\(\{.*?\}\)", response_text, re.S)
        if not block:
            return {}
        text = block.group(0)
    else:
        text = m.group(1)

    result = {}
    for k, v in _KV_RE.findall(text):
        v_clean = v.strip().strip('\'"')
        result[k] = v_clean
    keep = {k: result.get(k) for k in ("totalPrice","price","area","houseId","resblockName")}
    return {k:v for k,v in keep.items() if v}
