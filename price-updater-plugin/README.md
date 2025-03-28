# Hotel Price Aggregator

This program aggregates hotel prices from four different websites by retrieving the lowest price from each source and then calculating a "best price" (the minimum price found minus 1). It combines these prices with corresponding hotel logos and automatically uploads the information to a specified website.

## Features

- **Price Retrieval:**  
  Fetches hotel prices from four sources:
  1. [Etstur - Bodrum Hotels](https://www.etstur.com/Bodrum-Otelleri?check_in=26.03.2025&check_out=27.03.2025&adult_1=7&filters=&sortType=price&sortDirection=asc)
  2. [Trivago - Bodrum Hotels](https://www.trivago.com.tr/tr/lm/otel-bodrum-t%C3%BCrkiye?search=200-15260;dr-20250327-20250328-s;rc-1-7;so-1)
  3. [Tatilbudur - Bodrum Hotels](https://www.tatilbudur.com/yurtici-oteller/mugla/bodrum-otelleri?checkInDate=27.03.2025&checkOutDate=31.03.2025&latStart=0&latEnd=0&lonStart=0&lonEnd=0&min=&max=&sort=price&sort-type=asc&searchType=hotel&hotelCategory=yurtici-oteller%2Fmugla%2Fbodrum-otelleri&key=Bodrum+Otelleri&checkInDate=27.03.2025&checkOutDate=31.03.2025&adult=7&child=0&personCount=7+Yeti%C5%9Fkin+&type=region&id=30344&regionType=place&item_list_id=search&item_list_name=Bodrum+Otelleri&cd_item_list_location=search&price-range=false&searchType=hotel)
  4. **Otelz:** Uses Selenium to interact with the website by automatically typing the city (e.g., Bodrum) and the number of guests before retrieving the price.
- **Best Price Calculation:**  
  Compares the retrieved prices and calculates the best price as the lowest value minus 1.
- **Logo Integration:**  
  Associates and displays hotel logos (provided as PNG files) alongside the price details.
- **Automatic Upload:**  
  Uploads the aggregated pricing information and logos to a specified website.

## Configuration Files

- **`env.txt`:**  
  This file holds the configuration for the target website where the data will be uploaded. An example `env.txt`:
  https://wawday.com/ # Website domain
  https://wawday.com/test-page/ # Page for uploading prices
  yasem # Username for the website
  N6bS XIcl HSR7 x69O QwUm Ya5p # Password for the website
- **Logos:**  
Place your logo PNG files in the designated directory (e.g., `logos/`).

## Parameters

- **City:** The target city for the price search (e.g., Bodrum).
- **Number of Guests:** The number of guests (e.g., 7).
