#!/usr/bin/env python3
"""
ComBase数据处理器
处理爬取的原始数据，提取完整信息并整理存储
"""

import os
import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import re

class ComBaseDataProcessor:
    """ComBase数据处理器"""
    
    def __init__(self, data_dir: str = "data", processed_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.total_records = 0
        self.duplicate_records = 0
        self.unique_records = 0
        
    def find_data_files(self) -> List[Path]:
        """查找所有数据文件"""
        csv_files = []
        
        # 查找CSV文件
        patterns = [
            "combase_*.csv",
            "combase_pages_*.csv",
            "combase_batch_*.csv",
            "combase_complete_*.csv",
            "test_*.csv"
        ]
        
        for pattern in patterns:
            csv_files.extend(self.data_dir.glob(pattern))
        
        # 排除已处理的文件
        csv_files = [f for f in csv_files if "processed" not in str(f)]
        
        print(f"找到 {len(csv_files)} 个数据文件:")
        for file in csv_files:
            print(f"  - {file.name}")
            
        return csv_files
    
    def load_and_merge_data(self, files: List[Path]) -> pd.DataFrame:
        """加载并合并所有数据文件"""
        all_data = []
        
        for file in files:
            try:
                df = pd.read_csv(file)
                print(f"加载 {file.name}: {len(df)} 条记录")
                all_data.append(df)
            except Exception as e:
                print(f"加载 {file.name} 失败: {e}")
                continue
        
        if not all_data:
            print("❌ 没有成功加载任何数据文件")
            return pd.DataFrame()
        
        # 合并所有数据
        merged_df = pd.concat(all_data, ignore_index=True)
        self.total_records = len(merged_df)
        
        print(f"\n📊 数据合并结果:")
        print(f"总记录数: {self.total_records}")
        
        return merged_df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除重复记录"""
        print("\n🔍 检查重复记录...")
        
        # 基于record_id去重
        before_count = len(df)
        df_unique = df.drop_duplicates(subset=['record_id'], keep='first')
        after_count = len(df_unique)
        
        self.duplicate_records = before_count - after_count
        self.unique_records = after_count
        
        print(f"去重前: {before_count} 条记录")
        print(f"去重后: {after_count} 条记录")
        print(f"重复记录: {self.duplicate_records} 条")
        
        return df_unique
    
    def validate_data_consistency(self, df: pd.DataFrame):
        """验证数据一致性"""
        print("\n🔍 验证数据一致性...")
        
        # 检查页面记录数
        page_counts = df['page_number'].value_counts().sort_index()
        
        print("各页面记录数:")
        inconsistent_pages = []
        for page, count in page_counts.items():
            status = "✓" if count == 10 else "⚠️"
            print(f"  第 {page} 页: {count} 条记录 {status}")
            if count != 10:
                inconsistent_pages.append(page)
        
        if inconsistent_pages:
            print(f"⚠️ 发现 {len(inconsistent_pages)} 个页面记录数不是10条")
            print(f"异常页面: {inconsistent_pages}")
        else:
            print("✅ 所有页面记录数都正确")
        
        # 检查record_id连续性
        record_ids = df['record_id'].astype(int).sort_values()
        gaps = []
        for i in range(1, len(record_ids)):
            if record_ids.iloc[i] - record_ids.iloc[i-1] > 1:
                gaps.append((record_ids.iloc[i-1], record_ids.iloc[i]))
        
        if gaps:
            print(f"⚠️ 发现 {len(gaps)} 个record_id间隙:")
            for start, end in gaps[:5]:  # 只显示前5个
                print(f"  {start} -> {end}")
        else:
            print("✅ record_id连续无间隙")
    
    def enhance_data_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """增强数据结构，添加更多字段"""
        print("\n🔧 增强数据结构...")
        
        enhanced_df = df.copy()
        
        # 1. 解析食品信息
        enhanced_df['food_category'] = enhanced_df['food'].apply(self.extract_food_category)
        enhanced_df['food_name'] = enhanced_df['food'].apply(self.extract_food_name)
        
        # 2. 解析时间序列统计
        enhanced_df['logc_range'] = enhanced_df.apply(
            lambda row: row['logc_final'] - row['logc_initial'] if pd.notna(row['logc_final']) and pd.notna(row['logc_initial']) else None, 
            axis=1
        )
        
        enhanced_df['logc_max'] = enhanced_df['logc_series_json'].apply(self.extract_max_from_series)
        enhanced_df['logc_min'] = enhanced_df['logc_series_json'].apply(self.extract_min_from_series)
        
        # 3. 添加数据质量标记
        enhanced_df['has_time_series'] = enhanced_df['logc_points'].notna() & (enhanced_df['logc_points'] > 0)
        enhanced_df['data_completeness'] = enhanced_df.apply(self.calculate_completeness, axis=1)
        
        # 4. 添加处理时间戳
        enhanced_df['processed_at'] = datetime.now().isoformat()
        
        print(f"✅ 数据结构增强完成，新增 {len(enhanced_df.columns) - len(df.columns)} 个字段")
        
        return enhanced_df
    
    def extract_food_category(self, food_text: str) -> str:
        """提取食品类别"""
        if pd.isna(food_text) or not food_text:
            return "Unknown"
        
        food_text = food_text.lower()
        
        # 定义食品类别映射
        categories = {
            'beef': ['beef', 'steak', 'striploin', 'cube roll'],
            'seafood': ['salmon', 'fish', 'oyster', 'sole', 'seafood'],
            'poultry': ['chicken', 'turkey', 'poultry'],
            'dairy': ['milk', 'cheese', 'yogurt', 'dairy'],
            'vegetable': ['vegetable', 'lettuce', 'carrot'],
            'processed_meat': ['precooked', 'smoked', 'cured']
        }
        
        for category, keywords in categories.items():
            if any(keyword in food_text for keyword in keywords):
                return category.replace('_', ' ').title()
        
        return "Other"
    
    def extract_food_name(self, food_text: str) -> str:
        """提取食品名称"""
        if pd.isna(food_text) or not food_text:
            return "Unknown"
        
        # 移除"in "前缀
        if food_text.startswith("in "):
            return food_text[3:].strip()
        
        return food_text.strip()
    
    def extract_max_from_series(self, series_json: str) -> float:
        """从时间序列中提取最大值"""
        try:
            if pd.isna(series_json):
                return None
            series_data = json.loads(series_json)
            values = [point[1] for point in series_data]
            return max(values) if values else None
        except:
            return None
    
    def extract_min_from_series(self, series_json: str) -> float:
        """从时间序列中提取最小值"""
        try:
            if pd.isna(series_json):
                return None
            series_data = json.loads(series_json)
            values = [point[1] for point in series_data]
            return min(values) if values else None
        except:
            return None
    
    def calculate_completeness(self, row) -> float:
        """计算数据完整度"""
        total_fields = 8  # 主要字段数量
        complete_fields = 0
        
        fields_to_check = ['organism', 'food', 'temperature', 'aw', 'ph', 'logc_points', 'logc_duration', 'logc_series_json']
        
        for field in fields_to_check:
            if field in row and pd.notna(row[field]) and str(row[field]).strip() not in ['', 'Not specified', 'None']:
                complete_fields += 1
        
        return complete_fields / total_fields
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """生成汇总统计"""
        stats = {
            'total_records': len(df),
            'unique_organisms': df['organism'].nunique(),
            'unique_foods': df['food_name'].nunique(),
            'food_categories': df['food_category'].value_counts().to_dict(),
            'temperature_range': {
                'min': df['temperature'].astype(str).str.extract(r'(\d+)').astype(float).min().iloc[0] if not df['temperature'].empty else None,
                'max': df['temperature'].astype(str).str.extract(r'(\d+)').astype(float).max().iloc[0] if not df['temperature'].empty else None
            },
            'time_series_stats': {
                'records_with_series': df['has_time_series'].sum(),
                'avg_data_points': df['logc_points'].mean(),
                'avg_duration_hours': df['logc_duration'].mean()
            },
            'data_quality': {
                'avg_completeness': df['data_completeness'].mean(),
                'high_quality_records': (df['data_completeness'] >= 0.8).sum()
            }
        }
        
        return stats
    
    def save_processed_data(self, df: pd.DataFrame, stats: Dict):
        """保存处理后的数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. 保存主数据文件
        main_file = self.processed_dir / f"combase_processed_{timestamp}.csv"
        df.to_csv(main_file, index=False, encoding='utf-8')
        print(f"✅ 主数据文件已保存: {main_file}")
        
        # 2. 保存统计报告
        stats_file = self.processed_dir / f"combase_statistics_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ 统计报告已保存: {stats_file}")
        
        # 3. 保存简化版本（只包含主要字段）
        essential_columns = [
            'record_id', 'organism', 'food_category', 'food_name', 
            'temperature', 'aw', 'ph', 'page_number',
            'logc_points', 'logc_duration', 'logc_initial', 'logc_final',
            'logc_min', 'logc_max', 'logc_range',
            'has_time_series', 'data_completeness'
        ]
        
        essential_df = df[essential_columns]
        essential_file = self.processed_dir / f"combase_essential_{timestamp}.csv"
        essential_df.to_csv(essential_file, index=False, encoding='utf-8')
        print(f"✅ 精简数据文件已保存: {essential_file}")
        
        # 4. 生成可读的统计报告
        report_file = self.processed_dir / f"combase_report_{timestamp}.txt"
        self.generate_readable_report(stats, report_file)
        print(f"✅ 可读报告已保存: {report_file}")
        
        return main_file, essential_file, stats_file, report_file
    
    def generate_readable_report(self, stats: Dict, report_file: Path):
        """生成可读的统计报告"""
        report = f"""
ComBase数据处理报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 数据概览:
- 总记录数: {stats['total_records']:,}
- 唯一微生物: {stats['unique_organisms']} 种
- 唯一食品: {stats['unique_foods']} 种

🍖 食品类别分布:
"""
        
        for category, count in stats['food_categories'].items():
            percentage = count / stats['total_records'] * 100
            report += f"- {category}: {count:,} 条 ({percentage:.1f}%)\n"
        
        report += f"""
🌡️ 温度范围:
- 最低温度: {stats['temperature_range']['min']}°C
- 最高温度: {stats['temperature_range']['max']}°C

📈 时间序列数据:
- 包含时间序列: {stats['time_series_stats']['records_with_series']:,} 条
- 平均数据点: {stats['time_series_stats']['avg_data_points']:.1f} 个
- 平均观察时长: {stats['time_series_stats']['avg_duration_hours']:.1f} 小时

✅ 数据质量:
- 平均完整度: {stats['data_quality']['avg_completeness']:.1%}
- 高质量记录: {stats['data_quality']['high_quality_records']:,} 条

🔧 处理统计:
- 原始记录: {self.total_records:,}
- 重复记录: {self.duplicate_records:,}
- 唯一记录: {self.unique_records:,}
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def process_all_data(self):
        """处理所有数据的主函数"""
        print("🚀 ComBase数据处理器启动")
        print("=" * 50)
        
        # 1. 查找数据文件
        data_files = self.find_data_files()
        if not data_files:
            print("❌ 未找到数据文件")
            return None, None
        
        # 2. 加载并合并数据
        df = self.load_and_merge_data(data_files)
        if df.empty:
            print("❌ 数据加载失败")
            return None, None
        
        # 3. 去除重复
        df = self.remove_duplicates(df)
        
        # 4. 验证数据一致性
        self.validate_data_consistency(df)
        
        # 5. 增强数据结构
        df = self.enhance_data_structure(df)
        
        # 6. 生成统计
        stats = self.generate_summary_statistics(df)
        
        # 7. 保存处理后的数据
        files = self.save_processed_data(df, stats)
        
        print("\n" + "=" * 50)
        print("🎉 数据处理完成!")
        print("=" * 50)
        print(f"处理记录: {len(df):,} 条")
        print(f"输出文件: {len(files)} 个")
        print(f"保存位置: {self.processed_dir}")
        
        return df, stats


def main():
    """主函数"""
    print("🔧 ComBase数据处理器")
    print("处理爬取的原始数据，提取完整信息并整理存储")
    print("=" * 60)
    
    try:
        processor = ComBaseDataProcessor()
        df, stats = processor.process_all_data()
        
        if df is not None:
            print(f"\n📋 处理结果预览:")
            print(f"数据形状: {df.shape}")
            print(f"列名: {list(df.columns)}")
            
            # 显示前几条记录
            print(f"\n📊 数据样例:")
            print(df[['record_id', 'organism', 'food_category', 'food_name', 'temperature', 'logc_points']].head())
            
    except Exception as e:
        print(f"❌ 处理过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
