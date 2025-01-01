from sklearn.feature_extraction.text import CountVectorizer
from gensim import corpora, models
import pyLDAvis.gensim_models
import pyLDAvis
import pandas as pd
from datetime import datetime

class CommentAnalyzer:
    def __init__(self, processed_comments, comment_details):
        self.positive = processed_comments['positive']
        self.negative = processed_comments['negative']
        self.comment_details = comment_details
    
    def run_lda(self, texts, num_topics=5):
        # 创建词典
        dictionary = corpora.Dictionary(texts)
        
        # 创建文档-词频矩阵
        corpus = [dictionary.doc2bow(text) for text in texts]
        
        # 训练LDA模型
        lda_model = models.LdaModel(
            corpus=corpus,
            num_topics=num_topics,
            id2word=dictionary,
            passes=20
        )
        
        # 可视化
        vis_data = pyLDAvis.gensim_models.prepare(lda_model, corpus, dictionary)
        return lda_model, vis_data
    
    def save_analysis_results(self, comment_type, topics):
        """保存分析结果到CSV"""
        details = self.comment_details[comment_type]
        df = pd.DataFrame(details)
        
        # 添加主题分析结果
        topic_str = []
        for idx, topic in topics:
            topic_str.append(f"主题{idx+1}: {topic}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'analysis_{comment_type}_{timestamp}.csv'
        
        # 保存评论详情
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        # 保存主题分析结果
        with open(f'topics_{comment_type}_{timestamp}.txt', 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(topic_str))
        
        return filename
    
    def analyze(self):
        results = {}
        
        # 分析正面评论
        pos_lda, pos_vis = self.run_lda(self.positive)
        pos_topics = pos_lda.print_topics()
        results['positive'] = {
            'lda': pos_lda,
            'vis': pos_vis,
            'topics': pos_topics,
            'file': self.save_analysis_results('positive', pos_topics)
        }
        
        # 分析负面评论
        neg_lda, neg_vis = self.run_lda(self.negative)
        neg_topics = neg_lda.print_topics()
        results['negative'] = {
            'lda': neg_lda,
            'vis': neg_vis,
            'topics': neg_topics,
            'file': self.save_analysis_results('negative', neg_topics)
        }
        
        return results 