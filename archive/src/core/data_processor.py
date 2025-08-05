"""
Excel文件处理和数据整合模块
"""
import pandas as pd
import os
import shutil
from pathlib import Path
import logging
import re
from datetime import datetime
from config import DOWNLOAD_DIR, DATA_DIR, EXCEL_COLUMNS, REQUIRED_COLUMNS

class DataProcessor:
    def __init__(self, download_dir=DOWNLOAD_DIR, data_dir=DATA_DIR):
        self.download_dir = Path(download_dir)
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # 创建合并数据的存储文件
        self.master_csv = self.data_dir / "combase_master_data.csv"
        self.master_df = self._load_or_create_master_df()
    
    def _load_or_create_master_df(self):
        """加载或创建主数据DataFrame"""
        if self.master_csv.exists():
            try:
                df = pd.read_csv(self.master_csv)
                self.logger.info(f"已加载现有主数据文件，包含 {len(df)} 条记录")
                return df
            except Exception as e:
                self.logger.error(f"加载主数据文件失败: {e}")
        
        # 创建新的DataFrame
        df = pd.DataFrame(columns=EXCEL_COLUMNS)
        self.logger.info("创建新的主数据DataFrame")
        return df
    
    def process_latest_excel_files(self):
        """处理最新下载的Excel文件"""
        excel_files = list(self.download_dir.glob("*.xlsx"))
        
        if not excel_files:
            self.logger.warning("下载目录中没有找到Excel文件")
            return 0
        
        # 按修改时间排序，处理最新的文件
        excel_files.sort(key=os.path.getmtime, reverse=True)
        processed_count = 0
        
        for excel_file in excel_files:
            if self._is_file_processed(excel_file):
                continue
                
            try:
                records_added = self._process_single_excel(excel_file)
                if records_added > 0:
                    processed_count += records_added
                    self._mark_file_as_processed(excel_file)
                    self.logger.info(f"成功处理文件 {excel_file.name}，添加 {records_added} 条记录")
                
            except Exception as e:
                self.logger.error(f"处理文件 {excel_file.name} 失败: {e}")
        
        if processed_count > 0:
            self._save_master_data()
            self.logger.info(f"本次处理共添加 {processed_count} 条新记录")
        
        return processed_count
    
    def _process_single_excel(self, excel_file):
        """处理单个Excel文件"""
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file)
            
            # 数据清洗和标准化
            df = self._clean_data(df)
            
            # 检查必需列
            missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_columns:
                self.logger.warning(f"文件 {excel_file.name} 缺少必需列: {missing_columns}")
                return 0
            
            # 去重处理
            initial_count = len(df)
            df = df.drop_duplicates(subset=['Record ID'], keep='first')
            if len(df) < initial_count:
                self.logger.info(f"文件内去重: {initial_count} -> {len(df)}")
            
            # 与主数据合并，避免重复
            new_records = df[~df['Record ID'].isin(self.master_df['Record ID'])]
            
            if len(new_records) > 0:
                self.master_df = pd.concat([self.master_df, new_records], ignore_index=True)
                return len(new_records)
            else:
                self.logger.info(f"文件 {excel_file.name} 中没有新记录")
                return 0
                
        except Exception as e:
            self.logger.error(f"处理Excel文件时出错: {e}")
            raise
    
    def _clean_data(self, df):
        """清洗和标准化数据"""
        # 标准化列名
        df.columns = df.columns.str.strip()
        
        # 处理数值列
        numeric_columns = ['Temperature (C)', 'Aw', 'pH']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 处理文本列
        text_columns = ['Record ID', 'Organism', 'Food category', 'Food Name', 'Conditions']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
        
        # 处理Logcs列（时间序列数据）
        if 'Logcs' in df.columns:
            df['Logcs'] = df['Logcs'].apply(self._clean_logcs_data)
        
        # 添加处理时间戳
        df['processed_at'] = datetime.now().isoformat()
        
        return df
    
    def _clean_logcs_data(self, logcs_value):
        """清洗Logcs时间序列数据"""
        if pd.isna(logcs_value) or logcs_value == '':
            return ''
        
        try:
            # 确保数据格式为字符串
            logcs_str = str(logcs_value)
            
            # 移除多余的空格和特殊字符
            logcs_str = re.sub(r'\s+', '', logcs_str)
            
            # 验证数据格式（应该是 time;value;time;value... 的格式）
            parts = logcs_str.split(';')
            if len(parts) % 2 != 0:
                self.logger.warning(f"Logcs数据格式异常: {logcs_str[:50]}...")
            
            return logcs_str
            
        except Exception as e:
            self.logger.warning(f"清洗Logcs数据时出错: {e}")
            return str(logcs_value)
    
    def _is_file_processed(self, excel_file):
        """检查文件是否已经处理过"""
        processed_marker = self.processed_dir / f"{excel_file.stem}.processed"
        return processed_marker.exists()
    
    def _mark_file_as_processed(self, excel_file):
        """标记文件为已处理"""
        processed_marker = self.processed_dir / f"{excel_file.stem}.processed"
        processed_marker.touch()
        
        # 移动文件到已处理目录
        processed_file = self.processed_dir / excel_file.name
        shutil.move(str(excel_file), str(processed_file))
    
    def _save_master_data(self):
        """保存主数据到CSV文件"""
        try:
            self.master_df.to_csv(self.master_csv, index=False)
            self.logger.info(f"主数据已保存到 {self.master_csv}")
        except Exception as e:
            self.logger.error(f"保存主数据失败: {e}")
    
    def get_statistics(self):
        """获取数据统计信息"""
        stats = {
            'total_records': len(self.master_df),
            'unique_organisms': self.master_df['Organism'].nunique() if 'Organism' in self.master_df.columns else 0,
            'unique_food_categories': self.master_df['Food category'].nunique() if 'Food category' in self.master_df.columns else 0,
            'processed_files': len(list(self.processed_dir.glob("*.processed"))),
            'data_file_size': self.master_csv.stat().st_size if self.master_csv.exists() else 0
        }
        return stats
    
    def export_to_formats(self, formats=['csv', 'excel', 'json']):
        """导出数据到不同格式"""
        exported_files = []
        
        if 'csv' in formats:
            csv_file = self.data_dir / "combase_export.csv"
            self.master_df.to_csv(csv_file, index=False)
            exported_files.append(csv_file)
        
        if 'excel' in formats:
            excel_file = self.data_dir / "combase_export.xlsx"
            self.master_df.to_excel(excel_file, index=False)
            exported_files.append(excel_file)
        
        if 'json' in formats:
            json_file = self.data_dir / "combase_export.json"
            self.master_df.to_json(json_file, orient='records', indent=2)
            exported_files.append(json_file)
        
        return exported_files
    
    def cleanup_old_files(self, days=7):
        """清理旧的临时文件"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        cleaned_count = 0
        
        for file_path in self.processed_dir.glob("*"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                cleaned_count += 1
        
        self.logger.info(f"清理了 {cleaned_count} 个旧文件")
        return cleaned_count
