import json
import requests
from parsel import Selector
from html import unescape

INPUT_FILE = "/home/shahana/datahut-training/hw-training/myntra_multiple_categories.jl"
OUTPUT_FILE = "/home/shahana/datahut-training/hw-training/myntra_complete_products.json"
headers = {
    'accept': 'application/json',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'app': 'web',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    # 'cookie': 'at=ZXlKaGJHY2lPaUpJVXpJMU5pSXNJbXRwWkNJNklqRWlMQ0owZVhBaU9pSktWMVFpZlEuZXlKdWFXUjRJam9pWWpNMU1HSXlabVV0WlRsbU15MHhNV1l3TFRnM01XWXRPRFptWkRNMVpHTXpaR00zSWl3aVkybGtlQ0k2SW0xNWJuUnlZUzB3TW1RM1pHVmpOUzA0WVRBd0xUUmpOelF0T1dObU55MDVaRFl5WkdKbFlUVmxOakVpTENKaGNIQk9ZVzFsSWpvaWJYbHVkSEpoSWl3aWMzUnZjbVZKWkNJNklqSXlPVGNpTENKbGVIQWlPakUzT0RNeE5ERXpNelFzSW1semN5STZJa2xFUlVFaWZRLkhCV0d3MzlEV1VkWm80VHM2MjdYVzFEckpBLXJxMjNhODZpN21iakpEVnc=; lt_timeout=1; _d_id=eeccbf30-4d84-41a3-9e95-cf60d3d3b02f; mynt-eupv=1; _ma_session=%7B%22id%22%3A%22dc8fd597-c235-4b10-9c15-ca196b7cd3ca-eeccbf30-4d84-41a3-9e95-cf60d3d3b02f%22%2C%22referrer_url%22%3A%22%22%2C%22utm_medium%22%3A%22%22%2C%22utm_source%22%3A%22%22%2C%22utm_channel%22%3A%22direct%22%7D; microsessid=728; mynt-ulc-api=pincode%3A695001; x-mynt-pca=3Hj-tIEQ_eyG5seXLAsSHHGed79dnCikagiLU5v3dLXSOxAqJtdCDmo2yDNi1bKEY0NoRseumVrqcV4xzN2DWB8a2csR-d4wq0K8--jM44xMbz6aR22sA0RwlA2PsQi4VezJZGXePemqZm5gFTxdyEL1IbUP7NEBXrTCKJuG8XGXrWWUCsqi0tpV; ak_bmsc=571321BB917968F83C019CD0EEC4ABC6~000000000000000000000000000000~YAAQdo3vdTC4uoKbAQAAXdSIjB5ipClxnx9EpHwEDdU+ZztcdYQDgEvSQbwcNuc8NmXbUEmim3bpkLG8cbf0ehgy52PaQKMW8Yp2AmiHxmjvjllpl70zgPWO6l95T39adCqGk171zVCeVK4Vzcne1kl/2GB4TvxkYWpwg4i8UHJsSLcsq9WxeNzXBId7Rigmw2UByBkyUXnkcnu0gVmt/FnC2WpxOLJn1+6N48Qt+vIRGH7xWIZg5MrFoHI76MdF5ZTG0FW4mbPQXPMS2hSNsFC9Ov9yoe/5aCfIQ5FmTGtGRq7ysOnoOCYhzpG73ZOt2lQv5rfYa9FOZKxrxDfGpyQvSmGgE+hFC1evwR1lGM4IpLVLlX5ugxjGadOIWCPaRQRZqGvnZzNxLZkBs2AqEYEcnkDoI9unQ8uJA5g1UxieXhuOnER2CwpjUWFpJ0D8qw8TUotC20xMUMXoIPPEa5VRIBC/02VbD0VEJajNJXmvAyO+Y4McSg==; _gcl_au=1.1.3720374.1767589336; tvc_VID=1; _fbp=fb.1.1767589337071.998589818621442082; _cs_ex=1; _cs_c=1; _scid=DcnOx6-UxkYoJEHmTdLztOXeiko4WuEI; _ScCbts=%5B%22572%3Bchrome.2%3A2%3A5%22%5D; _sctr=1%7C1767551400000; mynt-loc-src=expiry%3A1767592226431%7Csource%3AIP; _mxab_=config.bucket%3Dregular%3Bcoupon.cart.channelAware%3DchannelAware_Enabled%3Bcart.cartfiller.personalised%3Denabled; lt_session=1; _xsrf=LC67E08iZupOSWfFUDJ8idoXBoc3TPcB; _pv=default; dp=d; user_session=rAk5r27mJVW_rQexjqev0Q.vjighbv1yeS3H4kOeWXkfzuLezOsXuka0HxjVCBd-nzjSi_Xsr1z53ORk6znBr75L_MaOHcDGKKodCYnjW-ctsYjZSCP3NL2jGCVdLdHhYZeIseC3en9yEgsrTcs0F2A8UQFTgU-Rux1gx1H6pintA.1767591242868.86400000.CRHuQN5yraQz_1Rx6Vc6xW_6yu7NGGsIHLtZKrfnqtM; bm_sz=D6B16EB9D39051726489A23E55BA9059~YAAQbY3vdbOplSWbAQAAlLWujB7UnXp4qgFP3W69lR1yfa3UlVo3vcJm/GLfkVs6B/AqgYmMUNCBieKGyGYHuOv7nMLN3ttIkqCNLaxHMY4laJPz8itOQXMASRFlWr0ak7tCjrS2F0xs5cIx1K27P6FplcwZvkfknMG0mWnepfzKapiuPgphRBW9VfLcvRmrLwO1XQqNcuOvZeLkGpiJ3ZV77eI9eCrFyn0QAW2a5zZxw1ieC9ir7O5V7CLEiM/6yv82KiefiFo5TziqnXNPvmc3F0vDFVQeuKpG+tYsgtHCU+plrFjIw1Mu0idV4K7d8GEUk74Awd9VmlDbkUHoXkRiGzK4UryLxyfeZA39LGYk9ZSnX9DJbs7NH4IDzCpJxeexs61Ri7/TkX0mS9c/JggE/EQ4o+EU8ZMPTqkosUwo9HJkiDN0mv79aD17ioyGW6mAjE7J0hhRYGr3ctYuZSGLjlkk+dONMUHe5TzdshSOKTuZFCTw3mbI55SJe0CNfE8ol4jSOB41fO/ueQxElAVNjNlNMb/ihdphymoptd6+bf6l84mFgEsvMPkPyU79/BF1KBaBeBUDLsiD~3618358~4473906; _abck=1D34682B4B780376CE3D7A404A3F1DC3~0~YAAQbY3vdbiplSWbAQAA9raujA/qigdFmo2tJ6iaSD2ZB7x4YmENF+5Nam+4dUpbkzoJnnaqwaMm/+IoHrnpVGJjJARKs/427zSOR5Zb7xio8MDY23DcfG9cI0bOpracpd7cZ7Zr5gk6XDefeLjN4X/Dxdx9gMTRtfwGpGVFrzx6uHdOHVoFWW7NFWVaz4RISV1QFqdxkfdHUoM7cIOs6Z6cmk8g4+6BkRDMK1ygFbxr6gXZYkwZzaIXdUrnj5JYSYh+1MsG2HbaP2rlJUCPwir0R6CxbZSLaT9VvtgO08AAxuTIptfLDxDs5wAqjgyBdtinQ1I/SBzE0arDn0usS9N8aYxRQiLghbr8MPflQLJxWOn/ZhI1hwbv4brs3H9+U5eTdLD72nfDztPLQV0PaQfrxBzcrz32AWKj/6zG86wQlaa39NRHKgTh3jH39YC1AqXsXsScwc28ZABWYBjlG9uge3MLDXbT0CgQfIHdFVqiJLgWs3uC11AH1syNK5jTDW2LCMLENPZoB8Y8mJTwyF20AamO3nWkdBFqbHrSQ7HlKDoKKzcDs73mNUNnsKU6/cvjWgTZ1M3vcxbfYSdjC1z/hxdHlv0L6yOL8LMmAeBTXerPTGXL2xbbaqd43muZgWUOZI1nyryaPBHaSYR/IgWaHSpvj6jzg5/c79hJwjq9WmHO1Z3+3UVeONuWuYvcJx9AI6A=~-1~-1~-1~AAQAAAAE%2f%2f%2f%2f%2fysfM8Wdx7yunXU4GQXpjh4E1q5kRECtP%2fqTIG+WmyWOUzrGbnXXWi70OtDtQYlpLXk8+OshPOOfCAcUupvjhNO64oyV9LnuPspALCGACSHyMPWjgvjOSDtJPARswgUMFvfeSQS+PUHkW2SORn3TBccZXEM4l2RV7Q5jU4CDlw%3d%3d~-1; ak_RT="z=1&dm=myntra.com&si=c0af5185-6ad9-4290-b5f8-0049729ccdff&ss=mk0p1v0y&sl=n&tt=18xf&obo=5&rl=1"; utrid=ek9veFx5UmtzcgpnCH9AMCMyMjYwMzczOTg5JDI%3D.9653da75c835ea7f0f7e73763f1eb95b; bm_sv=702903390175272E1EB518FEA229C0E9~YAAQbY3vddmplSWbAQAA/buujB5pNROu2rc3Hyh5vQ90fglRpluyEhPQBjnOnpdzvk6a/C1CephYmjFARLM+XpArPR/jSlkdssJpz/c9YnQ/GrqSZArthBvbwXAxBTqwErAUrqXNRcFIcp4Naj94Ougkdvu2HcmxOleLe0HNvIiN0LKpDHpMX+OrrTpgKMm7b4z8CmBZvXHXoW4ySh/g+T/CnL+nNrSMpCRkax5eETy2woE28hvchce19+t7HQxAB48=~1; _scid_r=HUnOx6-UxkYoJEHmTdLztOXeiko4WuEICMoACQ',
    'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjMwNjIwNzEiLCJhcCI6IjcxODQwNzY0MyIsImlkIjoiNzc5MDZiMzRhYWI2YWI2NCIsInRyIjoiYWFmZTA3NzZjN2RiNjA5MGE1MTNmNzllZDYxNzk5YWEiLCJ0aSI6MTc2NzU5MjA1MjA3OSwidGsiOiI2Mjk1Mjg2In19',
    'pagination-context': '{"productRack":{"dsCnsdrd":0,"tp":"nonDS","cntCnsdrd":0,"slrCnsdrd":0},"scImgVideoOffset":"0_0","v":1.0,"productsRowsShown":25,"paginationCacheKey":"a2e73d61-f36e-4079-b151-d2608635908f","inorganicRowsShown":2,"plaContext":"eyJvcmdhbmljQ3Vyc29yTWFyayI6IkFvZ0lRRUFBQUVGWDYvVXdXcEVLVllNV2NJREtxYTJQQTFhMG1sd3dNRjl6ZEhsc1pWOHlOREUzTVRNek5BXHUwMDNkXHUwMDNkIiwicGxhT2Zmc2V0IjowLCJvcmdhbmljT2Zmc2V0IjoyOSwiZXhwbG9yZU9mZnNldCI6MywiZmNjUGxhT2Zmc2V0IjoyMiwic2VhcmNoUGlhbm9QbGFPZmZzZXQiOjE5LCJpbmZpbml0ZVNjcm9sbFBpYW5vUGxhT2Zmc2V0IjowLCJ0b3NQaWFub1BsYU9mZnNldCI6Mywib3JnYW5pY0NvbnN1bWVkQ291bnQiOjI5LCJhZHNDb25zdW1lZENvdW50IjoxOCwiZXhwbG9yZUNvbnN1bWVkQ291bnQiOjMsImN1cnNvciI6eyJTRUFSQ0giOiJzcmM6TVlOVFJBX1BMQXxpZHg6MjB8ZmVhOnJvc35mZWE6a3d0fGlkeDowfHNyYzpGQ0N+ZmVhOm5rd3R8aWR4OjB8c3JjOkZDQyIsIlRPUF9PRl9TRUFSQ0giOiJzcmM6TVlOVFJBX1BMQXxpZHg6NHxmZWE6dG9zfmZlYTprd3R8aWR4OjB8c3JjOkZDQ35mZWE6bmt3dHxpZHg6MHxzcmM6RkNDIn0sInBsYXNDb25zdW1lZCI6W10sImFkc0NvbnN1bWVkIjpbXSwib3JnYW5pY0NvbnN1bWVkIjpbXSwiZXhwbG9yZUNvbnN1bWVkIjpbXX0\\u003d","refresh":false,"inorganicWidgetsOffset":{"bannerAdsOffset":0,"missionsOffset":0,"inlineFiltersGroupOffset":2,"relatedSearchesOffset":0,"productRacksOffset":0,"recSearchOffset":0},"scOffset":0,"reqId":"a2e73d61-f36e-4079-b151-d2608635908f"}',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.myntra.com/boy-tshirts',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'traceparent': '00-aafe0776c7db6090a513f79ed61799aa-77906b34aab6ab64-01',
    'tracestate': '6295286@nr=0-1-3062071-718407643-77906b34aab6ab64----1767592052079',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'x-location-context': 'pincode=695001;source=IP',
    'x-meta-app': 'channel=web',
    'x-myntra-app': 'deviceID=eeccbf30-4d84-41a3-9e95-cf60d3d3b02f;customerID=;reqChannel=web;appFamily=MyntraRetailWeb;',
    'x-myntraweb': 'Yes',
    'x-requested-with': 'browser',
}


all_products = []

with open(INPUT_FILE, "r", encoding="utf-8") as f, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as out:

    for line in f:
        prod = json.loads(line)
        url = prod.get("product_url")

        response = requests.get(url, headers=headers, timeout=30)
        sel = Selector(response.text)

        # ---------------- Breadcrumbs ----------------
        breadcrumbs = ""
        breadcrumb_script = sel.xpath(
            "//script[@type='application/ld+json' and contains(., 'BreadcrumbList')]/text()"
        ).get()

        if breadcrumb_script:
            data = json.loads(breadcrumb_script)
            breadcrumbs_list = [
                item["item"]["name"]
                for item in data.get("itemListElement", [])
                if item.get("item")
            ]
            breadcrumbs = " > ".join(breadcrumbs_list)

        # ---------------- PDP Data ----------------
        product_details_str = ""
        specifications = None

        for script in sel.xpath("//script/text()").getall():
            script = script.strip()

            if script.startswith('window.__myx = {"pdpData"'):
                json_text = script.replace("window.__myx = ", "").rstrip(";")
                myx_data = json.loads(json_text)
                pdp_data = myx_data.get("pdpData", {})

                # Product Details
                details_kv = []
                for item in pdp_data.get("productDetails", []):
                    title = item.get("title")
                    description = item.get("description")
                    if title and description:
                        clean_desc = Selector(text=description).xpath("string()").get()
                        clean_desc = unescape(clean_desc).strip()
                        details_kv.append(f"{title}: {clean_desc}")

                product_details_str = " , ".join(details_kv)
                specifications = pdp_data.get("articleAttributes")
                break
        discount_=prod.get("discount_label")
        discount=discount_.replace('% OFF)"','').replace('"(','').strip()

        images=prod.get("images")
        images_str = ",".join(img for img in images if img.strip())
        # ---------------- Final Product ----------------
        product = {
            "product_id": prod.get("product_id"),
            "product_url": url,
            "title": prod.get("title"),
            "brand": prod.get("brand"),
            "breadcrumbs": breadcrumbs,
            "category": prod.get("category"),
            "gender": prod.get("gender"),
            "regular_price": prod.get("mrp"),
            "selling_price": prod.get("price"),
            "discount": discount.replace('% OFF)"', '').replace('"(', '').strip(),
            "promotion_description": prod.get("discount_label"),
            "color": prod.get("color"),
            "sizes": prod.get("sizes"),
            "images": images_str,
            "rating": prod.get("rating"),
            "reviews": prod.get("reviews"),
            "product_details": product_details_str,
            "specifications": specifications
        }


        # JSON Lines write
        out.write(json.dumps(product, ensure_ascii=False) + "\n")
