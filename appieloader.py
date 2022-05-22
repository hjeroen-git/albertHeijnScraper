import requests
import json

api_url = r"https://www.ah.nl/zoeken/api/products/search"

def search_pricerange(minprice, maxprice):
    print(f'loading pricerange: ({minprice},{maxprice})')
    products = []
    for page in range(20):
        print(f'loading page {page}')
        params = {"minPrice":minprice,"maxPrice":maxprice,"size":500,"page":page}
        r = requests.get(api_url, params = params).json()

        products = products + r['cards']
        if r['page']['totalElements'] > 2500:
            print("WARNING")
        if page == int(r['page']['totalElements']/500):
            break
    print(f'added={len(products)}')
    return products

ranges = [0.001,0.5,1,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2,2.1,2.2,2.3,2.4,2.5,2.6,2.7,2.8,2.9,3.5,4.1,5,6,8,10,15,20,30,50,1000]

products = []
for idx, maxprice in enumerate(ranges[1:]):
    minprice = ranges[idx]
    products = products + search_pricerange(minprice, maxprice)
    print(f'Total = {len(products)}')

with open('allproducts_summary.json', 'w') as f:
    allcards = json.dump(products, f)
