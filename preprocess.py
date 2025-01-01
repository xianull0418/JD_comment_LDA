import json
import jieba
import re
import pandas as pd
from collections import defaultdict
import os

class CommentPreprocessor:
    def __init__(self):
        self.stopwords = self.load_stopwords()
    
    def load_stopwords(self):
        with open('stopwords.txt', 'r', encoding='utf-8') as f:
            return set([line.strip() for line in f])
    
    def clean_text(self, text):
        # 去除特殊字符和表情
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
        return text
    
    def segment(self, text):
        words = jieba.cut(text)
        return [w for w in words if w not in self.stopwords and len(w) > 1]
    
    def process_comments(self, file_path=None):
        if file_path and file_path.endswith('.csv'):
            # 从CSV文件读取
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                comments = df.to_dict('records')
            except pd.errors.EmptyDataError:
                print(f"CSV文件 {file_path} 为空")
                return defaultdict(list), defaultdict(list)
        else:
            # 从JSON文件读取
            json_path = os.path.join('comments', 'comments.json')
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    comments = json.load(f)
            except FileNotFoundError:
                print(f"找不到文件: {json_path}")
                return defaultdict(list), defaultdict(list)
        
        processed_comments = defaultdict(list)
        comment_details = defaultdict(list)  # 存储详细信息
        
        for comment in comments:
            cleaned_text = self.clean_text(comment['content'])
            if not cleaned_text:
                continue
                
            words = self.segment(cleaned_text)
            if words:
                if comment['score'] >= 4:  # 4分以上为好评
                    processed_comments['positive'].append(words)
                    comment_details['positive'].append({
                        'content': comment['content'],
                        'score': comment['score'],
                        'time': comment['time']
                    })
                elif comment['score'] <= 2:  # 2分以下为差评
                    processed_comments['negative'].append(words)
                    comment_details['negative'].append({
                        'content': comment['content'],
                        'score': comment['score'],
                        'time': comment['time']
                    })
        
        return processed_comments, comment_details 