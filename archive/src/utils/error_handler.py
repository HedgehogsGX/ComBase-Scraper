"""
错误处理和恢复机制
"""
import logging
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException,
    ElementNotInteractableException, StaleElementReferenceException
)
from config import DATA_DIR, MAX_RETRIES, RETRY_DELAY

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_log_file = DATA_DIR / "error_log.json"
        self.error_stats = self.load_error_stats()
    
    def load_error_stats(self):
        """加载错误统计"""
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            'total_errors': 0,
            'error_types': {},
            'error_pages': {},
            'last_error_time': None,
            'recovery_attempts': 0
        }
    
    def save_error_stats(self):
        """保存错误统计"""
        try:
            with open(self.error_log_file, 'w') as f:
                json.dump(self.error_stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"保存错误统计失败: {e}")
    
    def log_error(self, error, page_num=None, context=""):
        """记录错误"""
        error_type = type(error).__name__
        error_message = str(error)
        timestamp = datetime.now().isoformat()
        
        # 更新统计
        self.error_stats['total_errors'] += 1
        self.error_stats['error_types'][error_type] = self.error_stats['error_types'].get(error_type, 0) + 1
        self.error_stats['last_error_time'] = timestamp
        
        if page_num:
            self.error_stats['error_pages'][str(page_num)] = {
                'error_type': error_type,
                'error_message': error_message,
                'timestamp': timestamp,
                'context': context
            }
        
        # 记录详细日志
        self.logger.error(f"错误类型: {error_type}, 页面: {page_num}, 上下文: {context}, 消息: {error_message}")
        
        self.save_error_stats()
    
    def should_retry(self, error, attempt_count):
        """判断是否应该重试"""
        if attempt_count >= MAX_RETRIES:
            return False
        
        # 可重试的错误类型
        retryable_errors = [
            TimeoutException,
            WebDriverException,
            ElementNotInteractableException,
            StaleElementReferenceException,
            ConnectionError,
            Exception  # 通用异常也可以重试
        ]
        
        return any(isinstance(error, err_type) for err_type in retryable_errors)
    
    def get_retry_delay(self, attempt_count, base_delay=RETRY_DELAY):
        """计算重试延迟（指数退避）"""
        return base_delay * (2 ** (attempt_count - 1))
    
    def handle_browser_error(self, browser_controller, error):
        """处理浏览器相关错误"""
        error_type = type(error).__name__
        
        if error_type in ['WebDriverException', 'SessionNotCreatedException']:
            self.logger.warning("浏览器会话异常，尝试重新初始化")
            try:
                browser_controller.close()
                time.sleep(5)
                browser_controller._setup_driver(browser_controller.headless)
                return True
            except Exception as e:
                self.logger.error(f"重新初始化浏览器失败: {e}")
                return False
        
        elif error_type in ['TimeoutException', 'NoSuchElementException']:
            self.logger.warning("页面元素超时或未找到，尝试刷新页面")
            try:
                browser_controller.driver.refresh()
                time.sleep(3)
                return True
            except Exception as e:
                self.logger.error(f"刷新页面失败: {e}")
                return False
        
        return False
    
    def validate_data_integrity(self, data_processor):
        """验证数据完整性"""
        issues = []
        
        try:
            df = data_processor.master_df
            
            # 检查必需列
            required_columns = ['Record ID', 'Organism', 'Food category']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                issues.append(f"缺少必需列: {missing_columns}")
            
            # 检查重复记录
            if 'Record ID' in df.columns:
                duplicates = df['Record ID'].duplicated().sum()
                if duplicates > 0:
                    issues.append(f"发现 {duplicates} 条重复记录")
            
            # 检查空值
            for col in required_columns:
                if col in df.columns:
                    null_count = df[col].isnull().sum()
                    if null_count > 0:
                        issues.append(f"列 {col} 有 {null_count} 个空值")
            
            # 检查数据类型
            if 'Temperature (C)' in df.columns:
                non_numeric = df['Temperature (C)'].apply(lambda x: not str(x).replace('.', '').replace('-', '').isdigit() if pd.notna(x) else False).sum()
                if non_numeric > 0:
                    issues.append(f"温度列有 {non_numeric} 个非数值")
            
            if issues:
                self.logger.warning(f"数据完整性检查发现问题: {issues}")
            else:
                self.logger.info("数据完整性检查通过")
            
            return issues
            
        except Exception as e:
            self.logger.error(f"数据完整性检查失败: {e}")
            return [f"检查过程出错: {e}"]
    
    def create_backup(self, data_processor):
        """创建数据备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = DATA_DIR / f"backup_combase_data_{timestamp}.csv"
            
            if not data_processor.master_df.empty:
                data_processor.master_df.to_csv(backup_file, index=False)
                self.logger.info(f"数据备份已创建: {backup_file}")
                return backup_file
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
        
        return None
    
    def recover_from_backup(self, data_processor, backup_file=None):
        """从备份恢复数据"""
        try:
            if backup_file is None:
                # 查找最新的备份文件
                backup_files = list(DATA_DIR.glob("backup_combase_data_*.csv"))
                if not backup_files:
                    self.logger.error("没有找到备份文件")
                    return False
                
                backup_file = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            import pandas as pd
            data_processor.master_df = pd.read_csv(backup_file)
            self.logger.info(f"已从备份恢复数据: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"从备份恢复失败: {e}")
            return False
    
    def cleanup_old_backups(self, keep_days=7):
        """清理旧备份文件"""
        try:
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            backup_files = list(DATA_DIR.glob("backup_combase_data_*.csv"))
            
            cleaned_count = 0
            for backup_file in backup_files:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_time:
                    backup_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"清理了 {cleaned_count} 个旧备份文件")
            
        except Exception as e:
            self.logger.error(f"清理备份文件失败: {e}")
    
    def get_error_summary(self):
        """获取错误摘要"""
        return {
            'total_errors': self.error_stats['total_errors'],
            'most_common_errors': sorted(
                self.error_stats['error_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'error_pages_count': len(self.error_stats['error_pages']),
            'last_error_time': self.error_stats['last_error_time']
        }

class CircuitBreaker:
    """断路器模式实现"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)
    
    def call(self, func, *args, **kwargs):
        """执行函数调用，带断路器保护"""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
                self.logger.info("断路器进入半开状态，尝试恢复")
            else:
                raise Exception("断路器开启，拒绝执行")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self):
        """判断是否应该尝试重置"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).total_seconds() > self.recovery_timeout
    
    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            self.logger.info("断路器已关闭，恢复正常")
    
    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            self.logger.warning(f"断路器开启，失败次数: {self.failure_count}")
