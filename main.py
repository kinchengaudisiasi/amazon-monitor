import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# 配置区
API_KEY = os.getenv('SCRAPERAPI_KEY')
KEYWORDS = ["resound hearing aid domes", "phonak hearing aid domes", "resound hearing aid accessories", "phonak hearing aid accessories"]
ZIP_CODES = ["90001", "10001", "33101"]

def parse_amazon_page(html_content, zip_code, keyword):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # 查找所有的产品搜索结果容器
    items = soup.select('div[data-component-type="s-search-result"]')
    
    for rank, item in enumerate(items, 1):
        try:
            # 1. 识别 ASIN
            asin = item.get('data-asin')
            
            # 2. 识别位置类型 (广告位通常有这个特定的类名)
            is_sponsored = "Sponsored" if item.select('.s-sponsored-label-info-icon') else "Organic"
            
            # 3. 价格
            price_whole = item.select_one('.a-price-whole')
            price_fraction = item.select_one('.a-price-fraction')
            price = f"{price_whole.text}{price_fraction.text}" if price_whole else "N/A"
            
            # 4. 评价数与评分
            rating_element = item.select_one('i.a-icon-star-small span')
            rating = rating_element.text if rating_element else "N/A"
            
            review_count_element = item.select_one('span.a-size-base.s-light-weight-text')
            review_count = review_count_element.text if review_count_element else "0"

            results.append({
                "ZipCode": zip_code,
                "Type": is_sponsored,
                "Rank": rank,
                "ASIN": asin,
                "Price": price,
                "Reviews": review_count,
                "Rating": rating,
                "Keyword": keyword,
                "FetchTime": datetime.now().strftime('%Y-%m-%d %H:%M')
            })
        except Exception as e:
            continue
            
    return results

def main():
    if not API_KEY:
        print("错误: 未找到 API Key，请检查 GitHub Secrets 设置")
        return

    all_data = []
    for zip_code in ZIP_CODES:
        for kw in KEYWORDS:
            for page in [1, 2]:
                print(f"正在抓取: {zip_code} | {kw} | 第 {page} 页")
                url = f"https://www.amazon.com/s?k={kw.replace(' ', '+')}&page={page}"
                
                payload = {'api_key': API_KEY, 'url': url, 'zip_code': zip_code, 'render': 'true'}
                try:
                    r = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
                    if r.status_code == 200:
                        page_data = parse_amazon_page(r.text, zip_code, kw)
                        all_data.extend(page_data)
                except Exception as e:
                    print(f"请求失败: {e}")

    # 保存数据
    if all_data:
        df = pd.DataFrame(all_data)
        file_path = 'data.csv'
        # 如果文件已存在则追加，不存在则新建
        header = not os.path.exists(file_path) or os.stat(file_path).st_size == 0
        df.to_csv(file_path, mode='a', index=False, header=header, encoding='utf-8-sig')
        print(f"成功保存 {len(all_data)} 条数据到 data.csv")
    else:
        print("警告: 本次运行未抓取到任何数据")

if __name__ == "__main__":
    main()
