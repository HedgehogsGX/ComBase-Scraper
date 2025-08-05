#!/usr/bin/env python3
"""
ComBase爬虫启动脚本
提供命令行界面和交互式菜单
"""
import argparse
import sys
from pathlib import Path
from src.core.scraper import ComBaseScraper
from src.utils.monitor import ScrapingMonitor
from src.core.data_processor import DataProcessor
from src.core.database import DatabaseManager

def show_menu():
    """显示交互式菜单"""
    print("\n" + "="*50)
    print("ComBase 数据爬取工具")
    print("="*50)
    print("1. 开始爬取数据")
    print("2. 继续未完成的爬取")
    print("3. 重试失败的页面")
    print("4. 查看爬取状态")
    print("5. 导出数据")
    print("6. 数据统计")
    print("7. 清理和维护")
    print("0. 退出")
    print("="*50)

def start_scraping(start_page=None, end_page=None, username=None, password=None):
    """开始爬取"""
    # 获取登录信息
    if not username:
        username = input("请输入ComBase用户名: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("请输入ComBase密码: ")

    scraper = ComBaseScraper()
    try:
        scraper.start_scraping(start_page, end_page, username, password)
        scraper.retry_failed_pages()
        scraper.export_data_to_database()
        print("\n爬取完成！")
    except KeyboardInterrupt:
        print("\n用户中断爬取")
    finally:
        scraper.cleanup()

def continue_scraping():
    """继续未完成的爬取"""
    # 获取登录信息
    username = input("请输入ComBase用户名: ").strip()
    import getpass
    password = getpass.getpass("请输入ComBase密码: ")

    scraper = ComBaseScraper()
    try:
        current_page = scraper.progress.get('current_page', 1)
        print(f"从第 {current_page} 页继续爬取...")
        scraper.start_scraping(start_page=current_page, username=username, password=password)
        scraper.retry_failed_pages()
        scraper.export_data_to_database()
        print("\n爬取完成！")
    except KeyboardInterrupt:
        print("\n用户中断爬取")
    finally:
        scraper.cleanup()

def retry_failed():
    """重试失败的页面"""
    scraper = ComBaseScraper()
    try:
        failed_count = len(scraper.progress.get('failed_pages', []))
        if failed_count == 0:
            print("没有失败的页面需要重试")
            return
        
        print(f"发现 {failed_count} 个失败页面，开始重试...")
        scraper.retry_failed_pages()
        print("\n重试完成！")
    except KeyboardInterrupt:
        print("\n用户中断重试")
    finally:
        scraper.cleanup()

def show_status():
    """显示爬取状态"""
    monitor = ScrapingMonitor()
    monitor.print_dashboard()

def export_data():
    """导出数据"""
    print("\n选择导出格式:")
    print("1. CSV")
    print("2. Excel")
    print("3. JSON")
    print("4. 全部格式")
    
    choice = input("请选择 (1-4): ").strip()
    
    processor = DataProcessor()
    
    if choice == '1':
        formats = ['csv']
    elif choice == '2':
        formats = ['excel']
    elif choice == '3':
        formats = ['json']
    elif choice == '4':
        formats = ['csv', 'excel', 'json']
    else:
        print("无效选择")
        return
    
    try:
        exported_files = processor.export_to_formats(formats)
        print(f"\n数据已导出到:")
        for file_path in exported_files:
            print(f"  - {file_path}")
    except Exception as e:
        print(f"导出失败: {e}")

def show_statistics():
    """显示数据统计"""
    processor = DataProcessor()
    stats = processor.get_statistics()
    
    print("\n" + "="*40)
    print("数据统计信息")
    print("="*40)
    print(f"总记录数: {stats['total_records']}")
    print(f"唯一微生物: {stats['unique_organisms']}")
    print(f"食品类别数: {stats['unique_food_categories']}")
    print(f"已处理文件: {stats['processed_files']}")
    print(f"数据文件大小: {stats['data_file_size'] / 1024 / 1024:.2f} MB")
    print("="*40)

def cleanup_maintenance():
    """清理和维护"""
    print("\n维护选项:")
    print("1. 清理旧文件")
    print("2. 数据完整性检查")
    print("3. 创建数据备份")
    print("4. 全部执行")
    
    choice = input("请选择 (1-4): ").strip()
    
    processor = DataProcessor()
    
    if choice in ['1', '4']:
        cleaned = processor.cleanup_old_files()
        print(f"清理了 {cleaned} 个旧文件")
    
    if choice in ['2', '4']:
        from src.utils.error_handler import ErrorHandler
        error_handler = ErrorHandler()
        issues = error_handler.validate_data_integrity(processor)
        if issues:
            print(f"发现数据问题: {issues}")
        else:
            print("数据完整性检查通过")
    
    if choice in ['3', '4']:
        from src.utils.error_handler import ErrorHandler
        error_handler = ErrorHandler()
        backup_file = error_handler.create_backup(processor)
        if backup_file:
            print(f"备份已创建: {backup_file}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ComBase数据爬取工具')
    parser.add_argument('--start', type=int, help='起始页面')
    parser.add_argument('--end', type=int, help='结束页面')
    parser.add_argument('--username', type=str, help='ComBase用户名')
    parser.add_argument('--password', type=str, help='ComBase密码')
    parser.add_argument('--continue', action='store_true', help='继续未完成的爬取')
    parser.add_argument('--retry', action='store_true', help='重试失败的页面')
    parser.add_argument('--status', action='store_true', help='显示状态')
    parser.add_argument('--monitor', action='store_true', help='启动监控')
    parser.add_argument('--export', action='store_true', help='导出数据')
    parser.add_argument('--analyze', action='store_true', help='分析网站结构')
    
    args = parser.parse_args()
    
    # 命令行模式
    if len(sys.argv) > 1:
        if args.analyze:
            from src.utils.site_analyzer import ComBaseSiteAnalyzer
            analyzer = ComBaseSiteAnalyzer()
            analyzer.main()
        elif args.monitor:
            monitor = ScrapingMonitor()
            monitor.main()
        elif args.status:
            show_status()
        elif args.export:
            export_data()
        elif args.retry:
            retry_failed()
        elif getattr(args, 'continue'):
            continue_scraping()
        else:
            start_scraping(args.start, args.end, args.username, args.password)
        return
    
    # 交互式模式
    while True:
        show_menu()
        choice = input("\n请选择操作 (0-7): ").strip()
        
        if choice == '0':
            print("再见！")
            break
        elif choice == '1':
            start_page = input("起始页面 (回车默认从第1页): ").strip()
            end_page = input("结束页面 (回车默认到最后一页): ").strip()
            
            start_page = int(start_page) if start_page else None
            end_page = int(end_page) if end_page else None
            
            start_scraping(start_page, end_page)
        elif choice == '2':
            continue_scraping()
        elif choice == '3':
            retry_failed()
        elif choice == '4':
            show_status()
        elif choice == '5':
            export_data()
        elif choice == '6':
            show_statistics()
        elif choice == '7':
            cleanup_maintenance()
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()
