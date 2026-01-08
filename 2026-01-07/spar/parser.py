import hrequests
import json
import os

INPUT_FILE = "/home/shahana/datahut-training/hw-training/spar_products.jl"
OUTPUT_FILE = "/home/shahana/datahut-training/hw-training/spar_products_details.json"

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

MAX_ITEMS = 100
count = 0

with open(INPUT_FILE, "r", encoding="utf-8") as fin:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("[\n")  # start JSON array

        for line in fin:
            if count >= MAX_ITEMS:
                break

            product = json.loads(line)

            article_number = product.get("article_number")
            if not article_number:
                continue
            def fetch_price_details(article_number,headers):
                """
                Fetch price details for a given article number from SPAR price API.

                :param article_no: str or int (article ID)
                :param headers: dict (optional request headers)
                :param timeout: int (request timeout)
                :return: dict (extracted price details)
                """

                url = "https://api-scp.spar-ics.com/ecom/pw/v1/price/v1/store/at"
                params = {
                    "articleIds": str(article_number),
                    "salesChannel": "NATIONAL"
                }

                response = hrequests.get(url, headers=headers, params=params)

                data = response.json()
                article_data = data.get("storePrices", [])[0]

                regular_price=article_data.get("basePrice")
                selling_price=article_data.get("calculatedPrice")
                price_per_unit=article_data.get("comparisonPrice")
                promotion_description=article_data.get("aktionsKennzeichen").get("promotionBadgeText")

            
                return regular_price,selling_price,price_per_unit,promotion_description
            
            
            regular_price,selling_price,price_per_unit,promotion_description=fetch_price_details(article_number,headers)
            if price_per_unit:
                priceperunit=", ".join(
                    f"{k}: {v}" for k, v in price_per_unit.items()
                )


            url = (
                f"https://api-scp.spar-ics.com/ecom/pw/v1/product/v2/at/"
                f"{article_number}?audience=basic"
            )

            response = hrequests.get(url, headers=headers)

            if response.status_code != 200:
                print(f"Failed for {article_number}")
                continue

            data = response.json()
            product_description_list = (
                data.get("productClassificationStore", {})
                    .get("tradeItemMarketingMessage", {})
                    .get("values", [])
            )
            product_description = (
                ", ".join(v.get("valueString") for v in product_description_list)
                if product_description_list else ""
            )

            regulated_productname_list = (
                data.get("productClassificationStore", {})
                    .get("regulatedProductName", {})
                    .get("values", [])
            )
            regulated_productname = (
                ", ".join(v.get("valueString") for v in regulated_productname_list)
                if regulated_productname_list else ""
            )

            additional_info_list = (
                data.get("productClassificationStore", {})
                    .get("additionalTradeItemDescription", {})
                    .get("values", [])
            )
            additional_information = (
                ", ".join(add.get("valueString") for add in additional_info_list)
                if additional_info_list else ""
            )

            ingredients_list = (
                data.get("allergeneInfo", {})
                    .get("ingredientStatement", {})
                    .get("values", [])
            )
            ingredients = (
                ", ".join(ing.get("valueString") for ing in ingredients_list)
                if ingredients_list else ""
            )

            allergens_list = (
                data.get("allergeneInfo", {})
                    .get("allergenes", {})
                    .get("values", [])
            )
            allergens = (
                ", ".join(allg.get("valueString") for allg in allergens_list)
                if allergens_list else ""
            )

            nutrition_table = (
                data.get("nutrition", {})
                    .get("nutritionTable", {})
                    .get("201", {})
            )

            nutrition_data = {}

            for _, nutrient in nutrition_table.items():
                if not isinstance(nutrient, dict):
                    continue

                fe_name = nutrient.get("feName")
                values = nutrient.get("values", [])

                if not fe_name or not values:
                    continue

                value_string = values[0].get("valueString")
                if value_string:
                    nutrition_data[fe_name] = value_string

            nutrition_info = ", ".join(
                f"{k}: {v}" for k, v in nutrition_data.items()
            )

            preperation_instructions_list = (
                data.get("nutrition", {})
                    .get("preparationInstructions", {})
                    .get("values", [])
            )
            preperation_instructions = (
                ", ".join(pre.get("valueString") for pre in preperation_instructions_list)
                if preperation_instructions_list else ""
            )

            preperation_methods_list = (
                data.get("nutrition", {})
                    .get("preparationType", {})
                    .get("values", [])
            )
            preperation_methods = (
                ", ".join(pre.get("valueString") for pre in preperation_methods_list)
                if preperation_methods_list else ""
            )

            identification_marking_list = (
                data.get("productClassificationStore", {})
                    .get("regulatoryPermitIdentification", {})
                    .get("values", [])
            )
            identification_marking = (
                ", ".join(ide.get("valueString") for ide in identification_marking_list)
                if identification_marking_list else ""
            )

            countryoforigin_list = (
                data.get("productClassificationStore", {})
                    .get("provenanceStatement", {})
                    .get("values", [])
            )
            country_of_origin = (
                ", ".join(cou.get("valueString") for cou in countryoforigin_list)
                if countryoforigin_list else ""
            )

            storage_instructions_list = (
                data.get("productClassificationStore", {})
                    .get("consumerStorageInstructions", {})
                    .get("values", [])
            )
            storage_instructions = (
                ", ".join(sto.get("valueString") for sto in storage_instructions_list)
                if storage_instructions_list else ""
            )

            instructionsforuse_list = (
                data.get("productClassificationStore", {})
                    .get("consumerUsageInstructions", {})
                    .get("values", [])
            )
            instructions_for_use = (
                ", ".join(ins.get("valueString") for ins in instructionsforuse_list)
                if instructionsforuse_list else ""
            )

            
            scientific_name_list = (
                data.get("productClassificationStore", {})
                    .get("speciesForFisheryStatisticsPurposesName", {})
                    .get("values", [])
            )
            scientific_name = (
                ", ".join(aci.get("valueString") for aci in scientific_name_list)
                if scientific_name_list else ""
            )

            production_method_list = (
                data.get("productClassificationStore", {})
                    .get("productionMethodForFishAndSeafood", {})
                    .get("values", [])
            )
            production_method = (
                ", ".join(pro.get("valueString") for pro in production_method_list)
                if production_method_list else ""
            )

            variant_list = (
                data.get("productClassificationStore", {})
                    .get("variant", {})
                    .get("values", [])
            )
            variant = (
                ", ".join(var.get("valueString") for var in variant_list)
                if variant_list else ""
            )

            country_list = (
                data.get("productClassificationStore", {})
                    .get("classificationCountry", {})
                    .get("values", [])
            )
            country = (
                ", ".join(cou.get("valueString") for cou in country_list)
                if country_list else ""
            )

            item={
                "pdp_url":product.get("url"),
                "article_number":product.get("article_number"),
                "brand":product.get("brand"),
                "product_name":product.get("product_title"),
                "size":product.get("size"),
                "regular_price":regular_price,
                "selling_price":selling_price,
                "price_per_unit":priceperunit if priceperunit else "",
                "promotion_description":promotion_description,
                "product_description":product_description,
                #"regulated_product_name": regulated_productname,
                "additional_information": additional_information,

                "ingredients": ingredients,
                "allergens": allergens,

                "nutrition_info": nutrition_info,

                "preparation_instructions": preperation_instructions,
                "preparation_methods": preperation_methods,

                "identification_marking": identification_marking,
                "country_of_origin": country_of_origin,

                "storage_instructions": storage_instructions,
                "instructions_for_use": instructions_for_use,

                #"scientific_name": scientific_name,
                #"production_method": production_method,

                "variant": variant,
                "country": country


            }
        # save all products into ONE json file
            print(f"saving url : {item.get('pdp_url')}")

            if count > 0:
                f.write(",\n")  # comma between items

            json.dump(item, f, ensure_ascii=False, indent=2)
            count += 1

        f.write("\n]")  # end JSON array
