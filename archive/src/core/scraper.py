"""
ComBase数据爬取主控制器
"""
import logging
import time
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from retry import retry

from .browser_controller import ComBaseBrowserController
from .data_processor import DataProcessor
from .database import DatabaseManager
from config import *

class ComBaseScraper:
    def __init__(self):
        self.setup_logging()
        self.browser = None
        self.data_processor = DataProcessor()
        self.db_manager = DatabaseManager()
        self.progress_file = DATA_DIR / "scraping_progress.json"
        self.progress = self.load_progress()
        
    def setup_logging(self):
        """设置日志"""
        LOG_DIR.mkdir(exist_ok=True)
        log_file = LOG_DIR / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=LOG_FORMAT,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("ComBase爬虫初始化完成")
    
    def load_progress(self):
        """加载爬取进度"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                self.logger.info(f"已加载进度: 第 {progress.get('current_page', 1)} 页")
                return progress
            except Exception as e:
                self.logger.error(f"加载进度文件失败: {e}")
        
        return {
            'current_page': 1,
            'total_pages': TOTAL_PAGES,
            'completed_pages': [],
            'failed_pages': [],
            'total_records': 0,
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
    
    def save_progress(self):
        """保存爬取进度"""
        self.progress['last_update'] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            self.logger.error(f"保存进度失败: {e}")
    
    def start_scraping(self, start_page=None, end_page=None, username=None, password=None):
        """开始爬取数据"""
        try:
            # 检查登录凭据
            if not username or not password:
                if not LOGIN_USERNAME or not LOGIN_PASSWORD:
                    raise Exception("请在config.py中设置LOGIN_USERNAME和LOGIN_PASSWORD，或通过参数传入")
                username = LOGIN_USERNAME
                password = LOGIN_PASSWORD

            # 确定爬取范围
            start_page = start_page or self.progress['current_page']
            end_page = end_page or TOTAL_PAGES

            self.logger.info(f"开始爬取第 {start_page} 到第 {end_page} 页")

            # 初始化浏览器
            self.browser = ComBaseBrowserController()

            # 登录系统
            if not self.browser.login(username, password):
                raise Exception("登录失败，请检查用户名和密码")

            # 导航到搜索结果页面
            if not self.browser.navigate_to_search_results():
                raise Exception("无法导航到搜索结果页面")
            
            # 创建进度条
            with tqdm(range(start_page, end_page + 1), desc="爬取进度") as pbar:
                for page_num in pbar:
                    pbar.set_description(f"处理第 {page_num} 页")
                    
                    success = self.scrape_single_page(page_num)
                    
                    if success:
                        self.progress['completed_pages'].append(page_num)
                        self.progress['current_page'] = page_num + 1
                    else:
                        self.progress['failed_pages'].append(page_num)
                        self.logger.warning(f"第 {page_num} 页处理失败")
                    
                    # 更新进度
                    self.save_progress()
                    
                    # 显示统计信息
                    stats = self.data_processor.get_statistics()
                    pbar.set_postfix({
                        'Records': stats['total_records'],
                        'Failed': len(self.progress['failed_pages'])
                    })
                    
                    # 页面间延迟
                    time.sleep(2)
            
            self.logger.info("爬取完成")
            self.print_final_statistics()
            
        except KeyboardInterrupt:
            self.logger.info("用户中断爬取")
        except Exception as e:
            self.logger.error(f"爬取过程中出错: {e}")
        finally:
            self.cleanup()
    
    @retry(tries=MAX_RETRIES, delay=RETRY_DELAY, logger=logging.getLogger(__name__))
    def scrape_single_page(self, page_num):
        """爬取单个页面的数据"""
        try:
            # 跳转到指定页面
            if not self.browser.go_to_page(page_num):
                return False
            
            # 选择所有记录
            if not self.browser.select_all_records():
                self.logger.warning(f"第 {page_num} 页没有可选择的记录")
                return True  # 空页面也算成功
            
            # 导出数据
            if not self.browser.export_data():
                return False
            
            # 处理下载的Excel文件
            records_added = self.data_processor.process_latest_excel_files()
            
            if records_added > 0:
                self.progress['total_records'] += records_added
                self.logger.info(f"第 {page_num} 页成功添加 {records_added} 条记录")
            
            return True
            
        except Exception as e:
            self.logger.error(f"处理第 {page_num} 页时出错: {e}")
            return False
    
    def retry_failed_pages(self):
        """重试失败的页面"""
        failed_pages = self.progress['failed_pages'].copy()
        
        if not failed_pages:
            self.logger.info("没有需要重试的页面")
            return
        
        self.logger.info(f"开始重试 {len(failed_pages)} 个失败的页面")
        
        # 清空失败列表，重新记录
        self.progress['failed_pages'] = []
        
        for page_num in tqdm(failed_pages, desc="重试失败页面"):
            success = self.scrape_single_page(page_num)
            
            if success:
                self.progress['completed_pages'].append(page_num)
                self.logger.info(f"重试第 {page_num} 页成功")
            else:
                self.progress['failed_pages'].append(page_num)
                self.logger.warning(f"重试第 {page_num} 页仍然失败")
            
            self.save_progress()
            time.sleep(2)
    
    def export_data_to_database(self):
        """将处理好的数据导入数据库"""
        try:
            if self.data_processor.master_df.empty:
                self.logger.warning("没有数据可以导入数据库")
                return
            
            inserted, updated = self.db_manager.insert_records(self.data_processor.master_df)
            self.logger.info(f"数据库导入完成: 新增 {inserted} 条，更新 {updated} 条")
            
        except Exception as e:
            self.logger.error(f"导入数据库失败: {e}")
    
    def print_final_statistics(self):
        """打印最终统计信息"""
        stats = self.data_processor.get_statistics()
        
        print("\n" + "="*50)
        print("爬取完成统计")
        print("="*50)
        print(f"总记录数: {stats['total_records']}")
        print(f"唯一微生物: {stats['unique_organisms']}")
        print(f"食品类别: {stats['unique_food_categories']}")
        print(f"已完成页面: {len(self.progress['completed_pages'])}")
        print(f"失败页面: {len(self.progress['failed_pages'])}")
        print(f"处理文件数: {stats['processed_files']}")
        print(f"数据文件大小: {stats['data_file_size'] / 1024 / 1024:.2f} MB")
        
        if self.progress['failed_pages']:
            print(f"\n失败页面: {self.progress['failed_pages']}")
        
        print("="*50)
    
    def cleanup(self):
        """清理资源"""
        if self.browser:
            self.browser.close()
        
        if self.db_manager:
            self.db_manager.close()
        
        # 清理旧文件
        self.data_processor.cleanup_old_files()
        
        self.logger.info("资源清理完成")

def main():
    """主函数"""
    scraper = ComBaseScraper()
    
    try:
        # 开始爬取
        scraper.start_scraping()
        
        # 重试失败的页面
        scraper.retry_failed_pages()
        
        # 导出数据到数据库
        scraper.export_data_to_database()
        
        # 导出到其他格式
        exported_files = scraper.data_processor.export_to_formats()
        print(f"\n数据已导出到: {[str(f) for f in exported_files]}")
        
    except Exception as e:
        logging.error(f"程序执行失败: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()
