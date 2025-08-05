#!/usr/bin/env python3
"""
分批处理的ComBase爬虫 - 解决浏览器会话稳定性问题
"""
import sys
import os
import time
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.browser_controller import ComBaseBrowserController
from src.core.data_processor import DataProcessor

class BatchScraper:
    def __init__(self, batch_size=10):
        self.batch_size = batch_size
        self.data_processor = DataProcessor()
        self.progress_file = Path("data/batch_progress.json")
        
    def load_progress(self):
        """加载批处理进度"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            "completed_batches": [],
            "failed_batches": [],
            "current_batch": 1,
            "total_pages_processed": 0
        }
    
    def save_progress(self, progress):
        """保存批处理进度"""
        self.progress_file.parent.mkdir(exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def process_batch(self, start_page, end_page, username, password):
        """处理一个批次的页面"""
        print(f"\n🔄 处理批次: 第{start_page}-{end_page}页")
        print("=" * 50)
        
        browser = None
        success_count = 0
        failed_pages = []
        
        try:
            # 1. 初始化浏览器
            print("1️⃣ 初始化浏览器...")
            browser = ComBaseBrowserController()
            print("✓ 浏览器初始化成功")
            
            # 2. 登录
            print("2️⃣ 执行登录...")
            login_success = browser.login(username, password)
            if not login_success:
                print("❌ 登录失败")
                return 0, list(range(start_page, end_page + 1))
            print("✓ 登录成功")
            
            # 3. 导航到搜索结果页面
            print("3️⃣ 导航到搜索结果页面...")
            nav_success = browser.navigate_to_search_results()
            if not nav_success:
                print("❌ 导航失败")
                return 0, list(range(start_page, end_page + 1))
            print("✓ 导航成功")
            
            # 4. 处理每一页
            for page_num in range(start_page, end_page + 1):
                print(f"\n📄 处理第 {page_num} 页...")
                
                try:
                    # 跳转到指定页面
                    if page_num > 1:  # 第1页已经在搜索结果页面
                        jump_success = browser.go_to_page(page_num)
                        if not jump_success:
                            print(f"❌ 跳转到第 {page_num} 页失败")
                            failed_pages.append(page_num)
                            continue
                        print(f"✓ 成功跳转到第 {page_num} 页")
                    
                    # 选择数据
                    select_success = browser.select_all_records()
                    if not select_success:
                        print(f"❌ 第 {page_num} 页数据选择失败")
                        failed_pages.append(page_num)
                        continue
                    print(f"✓ 第 {page_num} 页数据选择成功")
                    
                    # 导出数据
                    export_success = browser.export_data()
                    if not export_success:
                        print(f"❌ 第 {page_num} 页导出失败")
                        failed_pages.append(page_num)
                        continue
                    print(f"✓ 第 {page_num} 页导出成功")
                    
                    success_count += 1
                    
                    # 短暂休息避免过快操作
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"❌ 第 {page_num} 页处理出错: {e}")
                    failed_pages.append(page_num)
                    continue
            
            print(f"\n📊 批次处理完成:")
            print(f"  成功: {success_count} 页")
            print(f"  失败: {len(failed_pages)} 页")
            if failed_pages:
                print(f"  失败页面: {failed_pages}")
            
            return success_count, failed_pages
            
        except Exception as e:
            print(f"❌ 批次处理出错: {e}")
            return 0, list(range(start_page, end_page + 1))
        finally:
            if browser:
                print("🧹 清理浏览器资源...")
                browser.close()
    
    def run_batch_scraping(self, start_page, end_page, username, password):
        """运行分批爬取"""
        print("🚀 ComBase分批爬取开始")
        print("=" * 60)
        print(f"总页面范围: {start_page} - {end_page}")
        print(f"批次大小: {self.batch_size}")
        print(f"预计批次数: {(end_page - start_page + 1 + self.batch_size - 1) // self.batch_size}")
        print("=" * 60)
        
        # 加载进度
        progress = self.load_progress()
        
        total_success = 0
        total_failed = []
        
        # 分批处理
        for batch_start in range(start_page, end_page + 1, self.batch_size):
            batch_end = min(batch_start + self.batch_size - 1, end_page)
            batch_num = (batch_start - start_page) // self.batch_size + 1
            
            # 检查是否已经处理过这个批次
            if batch_num in progress.get("completed_batches", []):
                print(f"⏭️ 跳过已完成的批次 {batch_num} (第{batch_start}-{batch_end}页)")
                continue
            
            print(f"\n🎯 开始批次 {batch_num}")
            
            # 处理当前批次
            success_count, failed_pages = self.process_batch(
                batch_start, batch_end, username, password
            )
            
            # 更新统计
            total_success += success_count
            total_failed.extend(failed_pages)
            
            # 更新进度
            if success_count > 0:
                progress["completed_batches"].append(batch_num)
            if failed_pages:
                progress["failed_batches"].extend(failed_pages)
            progress["current_batch"] = batch_num + 1
            progress["total_pages_processed"] = total_success
            
            self.save_progress(progress)
            
            # 批次间休息
            if batch_start + self.batch_size <= end_page:
                print(f"\n⏸️ 批次间休息 10 秒...")
                time.sleep(10)
        
        # 最终统计
        print("\n" + "=" * 60)
        print("🎉 分批爬取完成！")
        print("=" * 60)
        print(f"总成功页面: {total_success}")
        print(f"总失败页面: {len(total_failed)}")
        print(f"成功率: {total_success / (end_page - start_page + 1) * 100:.1f}%")
        
        if total_failed:
            print(f"\n失败页面列表: {total_failed}")
            print("可以稍后重试这些页面")
        
        return total_success, total_failed

def main():
    """主函数"""
    print("🎯 ComBase分批爬取工具")
    print("=" * 40)
    
    # 获取用户输入
    try:
        start_page = int(input("起始页面 (默认1): ") or "1")
        end_page = int(input("结束页面 (默认10): ") or "10")
        batch_size = int(input("批次大小 (默认5): ") or "5")
        
        username = input("ComBase用户名: ").strip()
        password = input("ComBase密码: ").strip()
        
        if not username or not password:
            print("❌ 用户名和密码不能为空")
            return
        
        # 创建分批爬取器
        scraper = BatchScraper(batch_size=batch_size)
        
        # 开始爬取
        success_count, failed_pages = scraper.run_batch_scraping(
            start_page, end_page, username, password
        )
        
        if success_count > 0:
            print(f"\n✅ 爬取成功！共处理 {success_count} 页")
        else:
            print(f"\n❌ 爬取失败！")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断爬取")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")

if __name__ == "__main__":
    main()
