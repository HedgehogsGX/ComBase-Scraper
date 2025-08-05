#!/usr/bin/env python3
"""
简化的ComBase爬虫 - 单终端显示进度条
"""
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.main_scraper import ComBaseMainScraper

class SimpleProgressScraper:
    def __init__(self):
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)
        self.total_pages = 6075
        self.records_per_file = 1000
        self.current_page = 1
        self.total_records = 0
        self.save_count = 0
        self.start_time = time.time()
        
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
        progress = current / total
        filled = int(width * progress)
        bar = '█' * filled + '░' * (width - filled)
        percentage = progress * 100
        return f"|{bar}| {percentage:.1f}%"
    
    def display_progress(self):
        """Display progress information"""
        self.clear_screen()

        elapsed = time.time() - self.start_time
        progress_percent = (self.current_page / self.total_pages) * 100

        print("🚀 ComBase Scraper Progress")
        print("=" * 60)
        print(f"⏰ Runtime: {self.format_time(elapsed)}")
        print(f"📄 Current Page: {self.current_page:,} / {self.total_pages:,}")
        print(f"📊 Completion: {progress_percent:.2f}%")
        print()

        # Progress bar
        progress_bar = self.draw_progress_bar(self.current_page, self.total_pages)
        print(f"📈 Progress: {progress_bar}")
        print()

        print(f"📝 Total Records: {self.total_records:,}")
        print(f"💾 Files Saved: {self.save_count}")
        print(f"📁 Records per File: {self.records_per_file:,}")
        print()

        # Speed and time estimation
        if elapsed > 0 and self.current_page > 1:
            pages_per_hour = (self.current_page / elapsed) * 3600
            remaining_pages = self.total_pages - self.current_page
            if pages_per_hour > 0:
                remaining_seconds = remaining_pages / (pages_per_hour / 3600)
                print(f"⚡ Speed: {pages_per_hour:.1f} pages/hour")
                print(f"⏱️ ETA: {self.format_time(remaining_seconds)}")

        print()
        print("💡 Press Ctrl+C to stop safely")
        print("=" * 60)
    
    def run(self):
        """Run the scraper"""
        print("🎯 ComBase Simple Scraper Starting")
        print("=" * 60)
        print("Configuration:")
        print(f"  - Target Pages: {self.total_pages:,}")
        print(f"  - Records per File: {self.records_per_file:,}")
        print(f"  - Output Directory: {self.output_dir}/")
        print("  - Using fixed complete organism name format")
        print("=" * 60)
        
        # 创建爬虫实例
        scraper = ComBaseMainScraper(output_dir=str(self.output_dir))
        scraper.records_per_file = self.records_per_file
        
        # 重写进度回调
        original_save_method = scraper.save_records_file

        def progress_callback(file_number):
            self.save_count += 1
            self.total_records = len(scraper.current_records) * self.save_count
            self.display_progress()
            return original_save_method(file_number)

        scraper.save_records_file = progress_callback

        # 重写页面解析回调来更新当前页面
        original_parse_method = scraper.parse_page_data

        def page_callback(page_number):
            self.current_page = page_number
            self.display_progress()
            return original_parse_method(page_number)

        scraper.parse_page_data = page_callback
        
        try:
            # 显示初始进度
            self.display_progress()
            time.sleep(2)
            
            # 开始爬取
            scraper.run_main_scraping(
                username="WallaceGuo@moonshotacademy.cn",
                password="Rr*Auzqv!b9!Cnh",
                start_page=1
            )
            
            # Final display
            self.display_progress()
            print("\n🎉 Scraping completed!")

        except KeyboardInterrupt:
            self.display_progress()
            print("\n\n⏸️ Scraping interrupted by user")
            print("💾 Saved data will not be lost")

            # Show final statistics
            elapsed = time.time() - self.start_time
            print(f"\n📊 Final Statistics:")
            print(f"  - Runtime: {self.format_time(elapsed)}")
            print(f"  - Pages Completed: {self.current_page:,} / {self.total_pages:,}")
            print(f"  - Total Records: {self.total_records:,}")
            print(f"  - Files Saved: {self.save_count}")
            print(f"  - Completion: {(self.current_page / self.total_pages) * 100:.2f}%")

        except Exception as e:
            self.display_progress()
            print(f"\n❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()

def main():
    scraper = SimpleProgressScraper()
    scraper.run()

if __name__ == "__main__":
    main()
