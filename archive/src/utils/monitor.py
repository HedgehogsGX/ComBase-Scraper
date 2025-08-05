"""
监控和管理工具
"""
import json
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from config import DATA_DIR, LOG_DIR

class ScrapingMonitor:
    def __init__(self):
        self.progress_file = DATA_DIR / "scraping_progress.json"
        self.monitor_file = DATA_DIR / "monitor_stats.json"
        self.start_time = datetime.now()
    
    def get_current_status(self):
        """获取当前爬取状态"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                
                total_pages = progress.get('total_pages', 5101)
                completed_pages = len(progress.get('completed_pages', []))
                failed_pages = len(progress.get('failed_pages', []))
                current_page = progress.get('current_page', 1)
                
                completion_rate = (completed_pages / total_pages) * 100 if total_pages > 0 else 0
                
                return {
                    'status': 'running' if current_page <= total_pages else 'completed',
                    'current_page': current_page,
                    'total_pages': total_pages,
                    'completed_pages': completed_pages,
                    'failed_pages': failed_pages,
                    'completion_rate': round(completion_rate, 2),
                    'total_records': progress.get('total_records', 0),
                    'start_time': progress.get('start_time'),
                    'last_update': progress.get('last_update')
                }
            else:
                return {'status': 'not_started'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_system_stats(self):
        """获取系统资源使用情况"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('.').percent,
                'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def estimate_completion_time(self):
        """估算完成时间"""
        status = self.get_current_status()
        
        if status.get('status') != 'running':
            return None
        
        completed = status.get('completed_pages', 0)
        total = status.get('total_pages', 5101)
        
        if completed == 0:
            return None
        
        try:
            start_time = datetime.fromisoformat(status.get('start_time', ''))
            elapsed = datetime.now() - start_time
            
            # 计算平均每页处理时间
            avg_time_per_page = elapsed.total_seconds() / completed
            remaining_pages = total - completed
            
            estimated_remaining = timedelta(seconds=avg_time_per_page * remaining_pages)
            estimated_completion = datetime.now() + estimated_remaining
            
            return {
                'estimated_completion': estimated_completion.isoformat(),
                'estimated_remaining': str(estimated_remaining),
                'avg_time_per_page': round(avg_time_per_page, 2)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_data_statistics(self):
        """获取数据统计信息"""
        try:
            master_csv = DATA_DIR / "combase_master_data.csv"
            
            if not master_csv.exists():
                return {'status': 'no_data'}
            
            df = pd.read_csv(master_csv)
            
            stats = {
                'total_records': len(df),
                'file_size_mb': round(master_csv.stat().st_size / 1024 / 1024, 2),
                'last_modified': datetime.fromtimestamp(master_csv.stat().st_mtime).isoformat()
            }
            
            if 'Organism' in df.columns:
                stats['unique_organisms'] = df['Organism'].nunique()
                stats['top_organisms'] = df['Organism'].value_counts().head(5).to_dict()
            
            if 'Food category' in df.columns:
                stats['unique_food_categories'] = df['Food category'].nunique()
                stats['top_food_categories'] = df['Food category'].value_counts().head(5).to_dict()
            
            if 'Temperature (C)' in df.columns:
                temp_stats = df['Temperature (C)'].describe()
                stats['temperature_stats'] = {
                    'mean': round(temp_stats['mean'], 2) if pd.notna(temp_stats['mean']) else None,
                    'min': round(temp_stats['min'], 2) if pd.notna(temp_stats['min']) else None,
                    'max': round(temp_stats['max'], 2) if pd.notna(temp_stats['max']) else None
                }
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def save_monitor_snapshot(self):
        """保存监控快照"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'scraping_status': self.get_current_status(),
            'system_stats': self.get_system_stats(),
            'data_stats': self.get_data_statistics(),
            'completion_estimate': self.estimate_completion_time()
        }
        
        try:
            with open(self.monitor_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
        except Exception as e:
            print(f"保存监控快照失败: {e}")
    
    def print_dashboard(self):
        """打印监控面板"""
        status = self.get_current_status()
        system = self.get_system_stats()
        data_stats = self.get_data_statistics()
        completion = self.estimate_completion_time()
        
        print("\n" + "="*60)
        print("ComBase 爬虫监控面板")
        print("="*60)
        
        # 爬取状态
        print(f"状态: {status.get('status', 'unknown')}")
        if status.get('status') == 'running':
            print(f"当前页面: {status.get('current_page', 0)}/{status.get('total_pages', 0)}")
            print(f"完成率: {status.get('completion_rate', 0)}%")
            print(f"已完成页面: {status.get('completed_pages', 0)}")
            print(f"失败页面: {status.get('failed_pages', 0)}")
            print(f"总记录数: {status.get('total_records', 0)}")
        
        # 完成时间估算
        if completion and 'estimated_completion' in completion:
            print(f"预计完成时间: {completion['estimated_completion'][:19]}")
            print(f"预计剩余时间: {completion['estimated_remaining']}")
            print(f"平均每页耗时: {completion['avg_time_per_page']} 秒")
        
        print("-" * 60)
        
        # 系统资源
        print("系统资源:")
        print(f"CPU使用率: {system.get('cpu_percent', 0)}%")
        print(f"内存使用率: {system.get('memory_percent', 0)}%")
        print(f"磁盘使用率: {system.get('disk_usage', 0)}%")
        
        print("-" * 60)
        
        # 数据统计
        if data_stats.get('total_records'):
            print("数据统计:")
            print(f"总记录数: {data_stats['total_records']}")
            print(f"文件大小: {data_stats['file_size_mb']} MB")
            print(f"唯一微生物: {data_stats.get('unique_organisms', 0)}")
            print(f"食品类别: {data_stats.get('unique_food_categories', 0)}")
        
        print("="*60)

def main():
    """监控主函数"""
    monitor = ScrapingMonitor()
    
    try:
        while True:
            monitor.print_dashboard()
            monitor.save_monitor_snapshot()
            
            print(f"\n监控更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("按 Ctrl+C 退出监控")
            
            time.sleep(30)  # 每30秒更新一次
            
    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    main()
