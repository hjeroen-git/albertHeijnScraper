import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

def AH_get_categories():
    '''
    Gets categories used in the Albert Heijn website
    '''
    products_url = 'https://www.ah.nl/producten'
    req = requests.get(products_url)
    soup = BeautifulSoup(req.text,features="html.parser")
    
    category_tags = soup.find_all('a',class_="taxonomy-card_imageLink__13VS1")
    
    category_names = [category['title'] for category in category_tags]
    category_links = ['http://www.ah.nl' + category['href'] for category in category_tags]
    
    return [{'name':i[0], 'link':i[1]} for i in zip(category_names,category_links)]



def get_products_from_pageset(url_base, label=''):
    
    # inits
    search_price = 0
    products_dict_list = []
    
    # check if query
    if not '?' in url_base:
        url_base = url_base + '?'
    else:
        url_base = url_base + '&'

    # loop
    for i in range(30):
        
        # make new query with new starting price and page number
        url = (url_base + 
               'sortBy=price' + 
               '&minPrice=' + str(search_price) + 
               '&maxPrice=120&page=' + str(55+i))
        
        print('Searching through ' + url + ' ...')
        
        # get products from a single page and append to existing list
        products_on_page = get_products_from_page(url, label)
        products_dict_list = products_dict_list + products_on_page
        
        # get the price of the most expensive item to know where to start the next loop. Note: this might produce duplicate entries
        search_price = np.nanmax([product['price'] for product in products_dict_list])
        
        # if the number of items was less than 1000, this was the last page. Note: If the number of items is exactly 1000, this will cause issues
        if len(products_on_page) < 1000:
            break
            
    return products_dict_list

def get_products_from_page(url, label=''):
    ''' 
    Gets all products from a single page with multiple items.
    Keyword arguments:
    url: the url of the page
    label: a label can be added to all items in the returnlist. If blank or not specified, the dicts will not contain this key 
    Returns: list of dicts of products
    '''
    
    # init
    products_dict_list = []
    
    # open connection to webpage
    req = requests.get(url)
    soup = BeautifulSoup(req.text,features="html.parser")
    product_tags = soup.find_all(attrs = {'data-testhook':'product-card'})
    print(str(len(product_tags)) + ' items found')
    
    for product_tag in product_tags:

        product_dict = dict()

        # Product name
        try:
            product_dict['name'] = str(product_tag.find_all(class_="line-clamp line-clamp--active title_lineclamp__10wki")[0].contents[0])
        except:
            product_dict['name'] = ''

        # URL
        try:
            product_dict['link'] = str('https://www.ah.nl' + product_tag.find_all('a', class_="link_root__fmxIo")[0]['href'])
        except:
            product_dict['link'] = ''

        # Quantity (e.g. 100g)
        try:
            product_dict['quantity'] = str(product_tag.find(attrs={'data-testhook':"product-unit-size"}).contents[0])
        except:
            product_dict['quantity'] = ''

        # Promo
        try:
            product_dict['promotion'] = str(''.join([promo.contents[0] + '. ' for promo in  product_tag.find_all(attrs={'data-testhook':"product-shield"})[0].find_all('span')])[:-2])
        except:
            product_dict['promotion'] = ''

        # Price and discounted price
        price_tags = product_tag.find_all(attrs = {'data-testhook':"price-amount"})
        if len(price_tags) !=0:
            product_dict['price'] = float(price_tags[0].contents[0].contents[0] + price_tags[0].contents[1].contents[0] + price_tags[0].contents[2].contents[0])
            if len(price_tags) == 2:
                product_dict['price_discounted'] = float(price_tags[1].contents[0].contents[0] + price_tags[1].contents[1].contents[0] + price_tags[1].contents[2].contents[0])
            else:
                product_dict['price_discounted'] = np.nan
        else:
            product_dict['price'] = np.nan
            product_dict['price_discounted'] = np.nan

        # Product category
        if label != '':
            product_dict['label'] = label


        products_dict_list.append(product_dict)
    return products_dict_list 


def AH_get_products_from_categories(categories):
    products_dict_list = []
    for category in categories:
        products_dict_list.append(products_from_page(category['link'] + '?', category['name']))
    return products_dict_list

def product_dict_to_df(products_dict_list):
    products_dict_list = [val for sublist in products_dict_list for val in sublist]
    products_df = pd.DataFrame(products_dict_list).drop_duplicates().reset_index(drop = True)
    products_df['discount_percentage'] = (products_df['price'] - products_df['price_discounted'])/products_df['price']*100
    products_df['discount'] = (products_df['price'] - products_df['price_discounted'])
    products_df['discount_relative'] = products_df['discount']/10 + products_df['discount_percentage']/50
    products_df.sort_values(by='discount_relative', axis=0, ascending = False).dropna()[:55]
    products_df = products_df.sort_values(by='discount_relative', axis=0, ascending = False)
    return products_df


def AH_saveproducts_to_html(products_df):
    products_df['link'] = products_df['link'].apply(lambda x: '<a href="{0}">link</a>'.format(x))
    f = open('AH_prod.html','w')
    f.write(products_df.to_html(escape=False))
    f.close()
    
