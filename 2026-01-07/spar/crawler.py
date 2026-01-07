import hrequests
import json

headers = {
    'accept': 'application/json',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'origin': 'https://www.spar.at',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.spar.at/',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}


page = 1
with open("spar_products.jl", "a", encoding="utf-8") as f:
    while True:
        
        response = hrequests.get(
    f'https://api-scp.spar-ics.com/ecom/pw/v1/search/v1/navigation?query=*&sort=Relevancy:asc&page={page}&marketId=NATIONAL&showPermutedSearchParams=false&filter=pwCategoryPathIDs%3Alebensmittel&hitsPerPage=32',
        headers=headers,
        )
        data = response.json()

        products = data.get("hits", [])
        if not products:
            break

        for product in products:
            master = product.get("masterValues", {})
            master = product.get("masterValues", {})

            item = {
                "url": f"https://www.spar.at/produktwelt/{master.get('slug')}",
                "brand": master.get("name1"),
                "product_title": master.get("name2"),
                "size": master.get("name3"),
                "article_number": master.get("productId")
            }
            
            # write ONE product per line
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # save / process data here

        total_pages = data.get("paging", {}).get("pageCount", 1)

        if page >= total_pages:
            break

        page += 1
# import hrequests
# from parsel import Selector
# response = hrequests.get("https://www.spar.at/produktwelt/lebensmittel?page=1")
# # print(response.status_code)
# # print(response.text)

# sel=Selector(response.text)

# products=sel.xpath("//a[@class='link product-tile__link']/@href").getall()
# print(products)