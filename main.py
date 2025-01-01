from jd_crawler import JDCommentCrawler
from preprocess import CommentPreprocessor
from analysis import CommentAnalyzer

def main():
    # 爬取评论
    crawler = JDCommentCrawler()
    product_id = '你的产品ID'  # 需要替换为实际的美的电热水器产品ID
    crawler.save_comments(product_id)
    
    # 预处理评论
    preprocessor = CommentPreprocessor()
    processed_comments = preprocessor.process_comments()
    
    # 分析评论
    analyzer = CommentAnalyzer(processed_comments)
    analyzer.analyze()

if __name__ == '__main__':
    main() 