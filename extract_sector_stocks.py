import csv
import os
from bs4 import BeautifulSoup

rows = []
folder = 'stock_sector'
for filename in os.listdir(folder):
    if filename.endswith('.html'):
        filepath = os.path.join(folder, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        current_sector = ''
        for elem in soup.body.descendants:
            if not hasattr(elem, 'name') or elem.name is None:
                continue  # Skip non-tag elements
            if elem.name == 'h1' and 'main_heading' in elem.get('class', []):
                sector_text = elem.get_text(strip=True)
                # Remove ' stocks' (case-insensitive, trailing) from sector name
                if sector_text.lower().endswith(' stocks'):
                    sector_text = sector_text[:-7].rstrip()
                current_sector = sector_text
            elif elem.name == 'a' and elem.has_attr('href') and elem.find('div', class_='left'):
                href = elem['href']
                # Extract exchange and symbol from Zerodha URL if pattern matches
                exchange = ''
                symbol = ''
                if 'stocks/' in href:
                    try:
                        after_stocks = href.split('stocks/', 1)[1]
                        exchange = after_stocks.split('/', 1)[0].strip('/')
                        # Find symbol after 'NSE/' or 'BSE/'
                        symbol = ''
                        for ex in ['NSE/', 'BSE/']:
                            if ex in after_stocks:
                                symbol = after_stocks.split(ex, 1)[1].split('/')[0].strip('/')
                                break
                    except Exception:
                        pass
                left_div = elem.find('div', class_='left')
                stock_name = ''
                if left_div:
                    inner_div = left_div.find('div')
                    if inner_div:
                        stock_name = inner_div.get_text(strip=True)
                    else:
                        stock_name = left_div.get_text(strip=True)
                market_cap = ''
                pe = ''
                right_div = elem.find('div', class_='right')
                if right_div:
                    market_cap_div = right_div.find('div', class_='market_cap')
                    pe_div = right_div.find('div', class_='pe')
                    if market_cap_div:
                        market_cap = market_cap_div.get_text(strip=True)
                    if pe_div:
                        pe = pe_div.get_text(strip=True)
                rows.append({
                    'Sector': current_sector,
                    'Stock URL': href,
                    'Exchange': exchange,
                    'Symbol': symbol,
                    'Stock Name': stock_name,
                    'Market Cap': market_cap,
                    'PE': pe
                })

with open('sector_stocks_extracted.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Sector', 'Stock URL', 'Exchange', 'Symbol', 'Stock Name', 'Market Cap', 'PE'])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. {len(rows)} stocks saved to sector_sample_extracted.csv with sector info from all HTML files in {folder}.")
