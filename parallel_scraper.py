#!/usr/bin/env python3
"""
并行ComBase爬虫 - 10个线程同时爬取不同页面
"""
import sys
import os
import time
import json
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.main_scraper import ComBaseMainScraper

class ParallelComBaseScraper:
    def __init__(self, total_pages=6075, num_threads=10, records_per_file=1000):
        self.total_pages = total_pages
        self.num_threads = num_threads
        self.records_per_file = records_per_file
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)
        
        # 线程安全的进度跟踪
        self.progress_lock = threading.Lock()
        self.completed_pages = 0
        self.total_records = 0
        self.active_threads = 0
        self.start_time = time.time()
        
        # 分配页面范围给每个线程
        self.page_ranges = self.distribute_pages()
        
    def distribute_pages(self):
        """将页面分配给不同线程，每个线程处理不同的页面范围"""
        pages_per_thread = self.total_pages // self.num_threads
        ranges = []
        
        for i in range(self.num_threads):
            start_page = i * pages_per_thread + 1
            if i == self.num_threads - 1:  # 最后一个线程处理剩余页面
                end_page = self.total_pages
            else:
                end_page = (i + 1) * pages_per_thread
            
            ranges.append((start_page, end_page, i))
        
        return ranges
    
    def clear_screen(self):
        """清屏"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def format_time(self, seconds):
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def draw_progress_bar(self, current, total, width=50):
        """绘制进度条"""
        progress = current / total if total > 0 else 0
        filled = int(width * progress)
        bar = '█' * filled + '░' * (width - filled)
        percentage = progress * 100
        return f"|{bar}| {percentage:.1f}%"
    
    def display_progress(self):
        """显示总体进度"""
        with self.progress_lock:
            self.clear_screen()
            
            elapsed = time.time() - self.start_time
            progress_percent = (self.completed_pages / self.total_pages) * 100
            
            print("🚀 Parallel ComBase Scraper Progress")
            print("=" * 70)
            print(f"⏰ Runtime: {self.format_time(elapsed)}")
            print(f"📄 Completed Pages: {self.completed_pages:,} / {self.total_pages:,}")
            print(f"📊 Completion: {progress_percent:.2f}%")
            print(f"🔄 Active Threads: {self.active_threads}/{self.num_threads}")
            print()
            
            # 进度条
            progress_bar = self.draw_progress_bar(self.completed_pages, self.total_pages)
            print(f"📈 Progress: {progress_bar}")
            print()
            
            print(f"📝 Total Records: {self.total_records:,}")
            print(f"📁 Records per File: {self.records_per_file:,}")
            print()
            
            # 速度和时间估算
            if elapsed > 0 and self.completed_pages > 0:
                pages_per_hour = (self.completed_pages / elapsed) * 3600
                remaining_pages = self.total_pages - self.completed_pages
                if pages_per_hour > 0:
                    remaining_seconds = remaining_pages / (pages_per_hour / 3600)
                    print(f"⚡ Speed: {pages_per_hour:.1f} pages/hour")
                    print(f"⏱️ ETA: {self.format_time(remaining_seconds)}")
            
            print()
            print("💡 Press Ctrl+C to stop all threads safely")
            print("=" * 70)
    
    def worker_thread(self, start_page, end_page, thread_id):
        """工作线程函数"""
        try:
            with self.progress_lock:
                self.active_threads += 1
            
            print(f"🔧 Thread {thread_id}: Starting pages {start_page}-{end_page}")
            
            # 创建独立的爬虫实例
            thread_output_dir = self.output_dir / f"thread_{thread_id}"
            scraper = ComBaseMainScraper(output_dir=str(thread_output_dir))
            scraper.records_per_file = self.records_per_file
            
            # 重写进度回调
            def update_progress(page_num):
                with self.progress_lock:
                    self.completed_pages += 1
                    # 估算记录数（假设每页10条记录）
                    self.total_records += 10
                self.display_progress()
            
            # 开始爬取
            scraper.run_main_scraping(
                username="WallaceGuo@moonshotacademy.cn",
                password="Rr*Auzqv!b9!Cnh",
                start_page=start_page,
                end_page=end_page,
                progress_callback=update_progress,
                search_delay=120  # 搜索后等待2分钟
            )
            
            print(f"✅ Thread {thread_id}: Completed pages {start_page}-{end_page}")
            
        except Exception as e:
            print(f"❌ Thread {thread_id}: Error - {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            with self.progress_lock:
                self.active_threads -= 1
    
    def run(self):
        """运行并行爬虫"""
        print("🎯 Starting Parallel ComBase Scraper")
        print("=" * 70)
        print("Configuration:")
        print(f"  - Total Pages: {self.total_pages:,}")
        print(f"  - Threads: {self.num_threads}")
        print(f"  - Records per File: {self.records_per_file:,}")
        print(f"  - Search Delay: 2 minutes")
        print("  - Using organism deduplication")
        print("=" * 70)
        
        # 显示页面分配
        print("\n📋 Page Distribution:")
        for start, end, thread_id in self.page_ranges:
            pages_count = end - start + 1
            print(f"  Thread {thread_id}: Pages {start:,}-{end:,} ({pages_count:,} pages)")
        print()
        
        try:
            # 显示初始进度
            self.display_progress()
            
            # 启动线程池
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                # 提交所有任务
                futures = []
                for start_page, end_page, thread_id in self.page_ranges:
                    future = executor.submit(self.worker_thread, start_page, end_page, thread_id)
                    futures.append(future)
                
                # 等待所有任务完成
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"❌ Thread failed: {e}")
            
            # 最终显示
            self.display_progress()
            print("\n🎉 All threads completed!")
            
        except KeyboardInterrupt:
            self.display_progress()
            print("\n\n⏸️ Scraping interrupted by user")
            print("💾 Saved data will not be lost")
            
            # 显示最终统计
            elapsed = time.time() - self.start_time
            print(f"\n📊 Final Statistics:")
            print(f"  - Runtime: {self.format_time(elapsed)}")
            print(f"  - Pages Completed: {self.completed_pages:,} / {self.total_pages:,}")
            print(f"  - Total Records: {self.total_records:,}")
            print(f"  - Completion: {(self.completed_pages / self.total_pages) * 100:.2f}%")
            
        except Exception as e:
            self.display_progress()
            print(f"\n❌ Error during parallel scraping: {e}")
            import traceback
            traceback.print_exc()

def main():
    # 配置参数
    TOTAL_PAGES = 6075
    NUM_THREADS = 10
    RECORDS_PER_FILE = 1000
    
    scraper = ParallelComBaseScraper(
        total_pages=TOTAL_PAGES,
        num_threads=NUM_THREADS,
        records_per_file=RECORDS_PER_FILE
    )
    scraper.run()

if __name__ == "__main__":
    main()
