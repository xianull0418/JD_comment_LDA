import time
import random
import json
import pandas as pd
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

class JDCommentCrawler:
    def __init__(self):
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 添加更多的选项来解决WebGL错误
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-webgl')
        chrome_options.add_argument('--ignore-certificate-errors')
        
        # 添加反爬虫检测规避措施
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置一些性能相关的选项
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # 不加载图片
                'javascript': 1,  # 允许JavaScript
                'cookies': 1  # 允许Cookie
            }
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # 初始化浏览器
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # 设置等待时间
        self.wait = WebDriverWait(self.driver, 10)
    
    def get_comments(self, product_id, page=0, score=0):
        """
        获取评论
        :param product_id: 商品ID
        :param page: 页码
        :param score: 评分 (1-差评 2-中评 3-好评 0-所有评论)
        """
        try:
            # 直接访问评论API
            comment_url = f'https://club.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98&productId={product_id}&score={score}&sortType=5&page={page}&pageSize=100&isShadowSku=0&fold=1&rid=0&sku={product_id}'
            
            # 添加随机延迟
            time.sleep(random.uniform(2, 4))
            
            self.driver.get(comment_url)
            
            # 获取页面源码
            response_text = self.driver.page_source
            
            # 提取JSON数据
            if 'fetchJSON_comment98' in response_text:
                json_text = response_text.split('fetchJSON_comment98(')[1].split(');')[0]
                result = json.loads(json_text)
            else:
                print("未找到评论数据")
                return []
            
            if 'comments' not in result:
                print(f"响应数据中没有comments字段")
                print(f"可用的字段: {list(result.keys())}")
                return []
            
            comments = result['comments']
            print(f"成功获取到 {len(comments)} 条评论")
            return comments
            
        except Exception as e:
            print(f"获取评论出错: {str(e)}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"错误堆栈:\n{traceback.format_exc()}")
            return []
    
    def save_comments(self, product_id, good_count=500, bad_count=500):
        """
        保存评论
        :param product_id: 商品ID
        :param good_count: 好评数量
        :param bad_count: 差评数量
        """
        if not os.path.exists('comments'):
            os.makedirs('comments')
        
        good_comments = []
        bad_comments = []
        
        try:
            # 爬取好评
            page = 0
            while len(good_comments) < good_count:
                print(f"正在爬取好评第 {page+1} 页...")
                comments = self.get_comments(product_id, page, score=3)
                if not comments:
                    break
                
                good_comments.extend([{
                    'content': comment['content'],
                    'score': comment['score'],
                    'time': comment['creationTime'],
                    'type': 'good'
                } for comment in comments])
                
                print(f"已获取 {len(good_comments)} 条好评")
                if len(comments) < 100:  # 如果返回的评论数少于100，说明已经到最后一页
                    break
                
                page += 1
                time.sleep(random.uniform(5, 8))
            
            # 爬取差评
            page = 0
            while len(bad_comments) < bad_count:
                print(f"正在爬取差评第 {page+1} 页...")
                comments = self.get_comments(product_id, page, score=1)
                if not comments:
                    break
                
                bad_comments.extend([{
                    'content': comment['content'],
                    'score': comment['score'],
                    'time': comment['creationTime'],
                    'type': 'bad'
                } for comment in comments])
                
                print(f"已获取 {len(bad_comments)} 条差评")
                if len(comments) < 100:
                    break
                
                page += 1
                time.sleep(random.uniform(5, 8))
            
            # 限制评论数量
            good_comments = good_comments[:good_count]
            bad_comments = bad_comments[:bad_count]
            
            # 合并所有评论
            all_comments = good_comments + bad_comments
            
            if not all_comments:
                print("没有获取到任何评论数据")
                return None
            
            # 保存数据
            df = pd.DataFrame(all_comments)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f'comments_{product_id}_{timestamp}.csv'
            csv_path = os.path.join('comments', csv_filename)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            print(f"共保存 {len(good_comments)} 条好评，{len(bad_comments)} 条差评")
            return csv_filename
            
        finally:
            self.driver.quit() 