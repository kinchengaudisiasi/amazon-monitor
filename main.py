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
    
    # 调试：打印网页标题，看是否遇到了验证码或机器人检查
    title = soup.title.string if soup.title else "No Title"
    print(f"  [调试] 页面标题: {title}")

    # 尝试多种常用的亚马逊产品容器选择器（增强兼容性）
    items = soup.select('div[data-component-type="s-search-result"]')
    if not items:
        items = soup.select('.s-result-item[data-asin]') # 备用选择器
    
    print(f"  [调试] 找到产品块数量: {len(items)}")
    
    for rank, item in enumerate(items, 1):
        if not item.get('data-asin'): continue # 跳过没有 ASIN 的空块
        
        try:
            asin = item.get('data-asin')
            is_sponsored = "Sponsored" if (item.select('.s-sponsored-label-info-icon') or "AdHolder" in item.get('class', [])) else "Organic"
            
            # 价格解析增强
            price_elem = item.select_one('.a-price .a-offscreen')
            price = price_elem.text if price_elem else "N/A"
            
            # 评价与评分
            rating_elem = item.select_one('i.a-icon-star-small span, i.a-icon-star span')
            rating = rating_elem.text if rating_elem else "N/A"
            
            review_elem = item.select_one('span.a-size-base.s-light-weight-text, span.a-size-base')
            review_count = review_elem.text if review_elem else "0"

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
        except:
            continue
            
    return results

def main():
    if not API_KEY:
        print("错误: 未找到 API Key，请检查 GitHub Secrets")
        return

    all_data = []
    for zip_code in ZIP_CODES:
        for kw in KEYWORDS:
            for page in [1]: # 建议先测试第1页，稳定后再开第2页以节省额度
                print(f">>> 抓取中: {zip_code} | {kw} | Page {page}")
                url = f"https://www.amazon.com/s?k={kw.replace(' ', '+')}&page={page}"
                
                # 尝试使用 render=false (部分类目不 render 反而更容易抓到 HTML 源码)
                payload = {'api_key': API_KEY, 'url': url, 'zip_code': zip_code, 'render': 'false'}
                try:
                    r = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
                    print(f"  [状态] HTTP {r.status_code} | 网页大小: {len(r.text)} 字符")
                    
                    if r.status_code == 200:
                        page_data = parse_amazon_page(r.text, zip_code, kw)
                        all_data.extend(page_data)
                except Exception as e:
                    print(f"  [错误] 请求异常: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        file_path = 'data.csv'
        header = not os.path.exists(file_path) or os.stat(file_path).st_size == 0
        df.to_csv(file_path, mode='a', index=False, header=header, encoding='utf-8-sig')
        print(f"✅ 成功! 本次新增保存 {len(all_data)} 条记录")
    else:
        print("❌ 失败: 未能解析到任何产品数据，请查看上方调试信息")

if __name__ == "__main__":
    main()
