import streamlit as st
import json
import pandas as pd
import numpy as np
from jd_crawler import JDCommentCrawler
from preprocess import CommentPreprocessor
from analysis import CommentAnalyzer
import pyLDAvis
import tempfile
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.decomposition import PCA

class StreamlitApp:
    def __init__(self):
        st.set_page_config(page_title="京东评论分析", layout="wide")
        self.temp_dir = tempfile.mkdtemp()
    
    def perform_kmeans_analysis(self, texts, n_clusters=5):
        """
        执行K-means聚类分析
        :param texts: 评论文本列表
        :param n_clusters: 聚类数量
        :return: 聚类结果、可视化图表和降维后的数据
        """
        # 将分词后的文本转换为字符串
        text_strings = [' '.join(text) for text in texts]
        
        # TF-IDF向量化
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(text_strings)
        
        # 使用PCA降维到2维以便可视化
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X.toarray())
        
        # K-means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X)
        
        # 获取每个聚类的关键词
        cluster_keywords = []
        for i in range(n_clusters):
            center_vector = kmeans.cluster_centers_[i]
            top_indices = center_vector.argsort()[-10:][::-1]
            keywords = [vectorizer.get_feature_names_out()[idx] for idx in top_indices]
            cluster_keywords.append(keywords)
        
        return clusters, cluster_keywords, X_pca

    def plot_cluster_scatter(self, X_pca, clusters, n_clusters):
        """绘制聚类散点图"""
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        
        fig, ax = plt.subplots(figsize=(12, 8), dpi=100)
        
        # 设置更美观的颜色方案
        colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', 
                 '#99CCFF', '#FFB366', '#FF99FF', '#99FF99', '#FFB366']
        
        # 绘制散点图
        for i in range(n_clusters):
            mask = clusters == i
            ax.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                      c=colors[i], 
                      label=f'聚类 {i+1}',
                      alpha=0.7,
                      s=100,  # 增大点的大小
                      edgecolor='white',  # 添加白色边框
                      linewidth=0.5)
        
        ax.set_xlabel('主成分1', fontsize=12, fontweight='bold')
        ax.set_ylabel('主成分2', fontsize=12, fontweight='bold')
        ax.set_title(f'K-Means聚类结果 ({n_clusters}个聚类)', 
                     fontsize=14, fontweight='bold', pad=20)
        
        # 优化图例
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                 frameon=True, fancybox=True, shadow=True)
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.2, color='gray')
        
        # 设置背景色和样式
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('#ffffff')
        
        # 添加轴线
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(0.5)
        ax.spines['left'].set_linewidth(0.5)
        
        # 调整布局
        plt.tight_layout()
        
        return fig
    
    def run(self):
        st.title("京东美的电热水器评论分析")
        
        # 固定商品ID
        product_id = "100104067842"
        
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        with col1:
            good_count = st.number_input(
                "好评数量", 
                min_value=100,
                max_value=1000,
                value=500,
                step=100,
                help="设置要爬取的好评数量"
            )
        
        with col2:
            bad_count = st.number_input(
                "差评数量",
                min_value=100,
                max_value=1000,
                value=500,
                step=100,
                help="设置要爬取的差评数量"
            )
        
        if st.button("爬取评论"):
            with st.spinner("正在爬取评论..."):
                crawler = JDCommentCrawler()
                csv_file = crawler.save_comments(
                    product_id, 
                    good_count=good_count,
                    bad_count=bad_count
                )
                if csv_file:
                    st.success(f"评论爬取完成！已保存至: {csv_file}")
                    st.write(f"共爬取 {good_count + bad_count} 条评论（{good_count}条好评，{bad_count}条差评）")
                else:
                    st.error("爬取评论失败，请稍后重试")
        
        # 选择已有的CSV文件进行分析
        if not os.path.exists('comments'):
            os.makedirs('comments')
        
        csv_files = [f for f in os.listdir('comments') if f.startswith('comments_') and f.endswith('.csv')]
        
        if csv_files:
            selected_file = st.selectbox("选择要分析的评论文件", csv_files)
            selected_file = os.path.join('comments', selected_file)
            
            # 数据预处理
            preprocessor = CommentPreprocessor()
            processed_comments, comment_details = preprocessor.process_comments(selected_file)
            
            # 分析器初始化
            analyzer = CommentAnalyzer(processed_comments, comment_details)
            
            # 选择查看正面或负面评论
            analysis_type = st.radio(
                "选择查看的评论类型",
                ["正面评论", "负面评论"]
            )
            
            num_topics = st.slider("选择主题数量", min_value=2, max_value=10, value=5)
            
            if st.button("开始分析"):
                with st.spinner("正在进行分析..."):
                    # 根据选择的评论类型获取相应的数据
                    texts = processed_comments['positive'] if analysis_type == "正面评论" else processed_comments['negative']
                    details = comment_details['positive'] if analysis_type == "正面评论" else comment_details['negative']
                    
                    if not texts:
                        st.warning(f"没有找到{analysis_type}数据")
                        return
                    
                    # LDA主题分析
                    lda_model, vis_data = analyzer.run_lda(texts, num_topics=num_topics)
                    
                    # 显示LDA分析结果
                    st.subheader("LDA主题分析")
                    for idx, topic in lda_model.print_topics():
                        st.write(f'主题 {idx + 1}:')
                        st.write(topic)
                    
                    # 显示LDA可视化
                    temp_html = os.path.join(self.temp_dir, 'topics.html')
                    pyLDAvis.save_html(vis_data, temp_html)
                    with open(temp_html, 'r', encoding='utf-8') as f:
                        html_string = f.read()
                        st.components.v1.html(html_string, height=800)
                    
                    # K-means聚类分析
                    st.subheader("K-means聚类分析")
                    clusters, cluster_keywords, X_pca = self.perform_kmeans_analysis(
                        texts, n_clusters=num_topics
                    )
                    
                    # 显示聚类结果
                    col1, col2 = st.columns([1, 2])  # 调整列宽比例
                    
                    with col1:
                        st.write("聚类关键词：")
                        for i, keywords in enumerate(cluster_keywords):
                            st.write(f"聚类 {i + 1}: {', '.join(keywords[:5])}")
                    
                    with col2:
                        st.write("聚类散点图：")
                        fig = self.plot_cluster_scatter(X_pca, clusters, num_topics)
                        st.pyplot(fig)
                    
                    # 显示评论示例
                    st.subheader("评论示例")
                    df = pd.DataFrame(details)
                    df['cluster'] = clusters
                    st.dataframe(df[['content', 'score', 'time', 'cluster']].head(10))
        
        else:
            st.info("请先爬取评论数据")

if __name__ == "__main__":
    app = StreamlitApp()
    app.run() 