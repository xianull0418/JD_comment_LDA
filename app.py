import streamlit as st
import json
import pandas as pd
from jd_crawler import JDCommentCrawler
from preprocess import CommentPreprocessor
from analysis import CommentAnalyzer
import pyLDAvis
import tempfile
import os

class StreamlitApp:
    def __init__(self):
        st.set_page_config(page_title="京东评论分析", layout="wide")
        self.temp_dir = tempfile.mkdtemp()
    
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
        csv_files = [f for f in os.listdir('comments') if f.startswith('comments_') and f.endswith('.csv')]
        if csv_files:
            selected_file = st.selectbox("选择要分析的评论文件", csv_files)
            selected_file = os.path.join('comments', selected_file)
        
        # 主界面
        if csv_files:
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
                with st.spinner("正在进行主题分析..."):
                    # 根据选择进行分析
                    texts = processed_comments['positive'] if analysis_type == "正面评论" else processed_comments['negative']
                    lda_model, vis_data = analyzer.run_lda(texts, num_topics=num_topics)
                    
                    # 保存可视化结果
                    temp_html = os.path.join(self.temp_dir, 'topics.html')
                    pyLDAvis.save_html(vis_data, temp_html)
                    
                    # 显示主题词
                    st.subheader("主题词分布")
                    for idx, topic in lda_model.print_topics():
                        st.write(f'主题 {idx + 1}:')
                        st.write(topic)
                    
                    # 显示交互式可视化
                    st.subheader("主题可视化")
                    with open(temp_html, 'r', encoding='utf-8') as f:
                        html_string = f.read()
                        st.components.v1.html(html_string, height=800)
                    
                    # 显示评论数量统计和示例
                    st.subheader("评论统计")
                    details = comment_details['positive'] if analysis_type == "正面评论" else comment_details['negative']
                    df = pd.DataFrame(details)
                    
                    st.write(f"正面评论数量: {len(processed_comments['positive'])}")
                    st.write(f"负面评论数量: {len(processed_comments['negative'])}")
                    
                    # 显示评论示例
                    st.subheader("评论示例")
                    st.dataframe(df[['content', 'score', 'time']].head())
        else:
            st.info("请先爬取评论数据")

if __name__ == "__main__":
    app = StreamlitApp()
    app.run() 