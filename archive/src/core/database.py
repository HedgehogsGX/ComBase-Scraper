"""
数据库模型和操作
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pandas as pd
from config import DATABASE_URL

Base = declarative_base()

class ComBaseRecord(Base):
    __tablename__ = 'combase_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(50), unique=True, nullable=False, index=True)
    organism = Column(String(200), nullable=False)
    food_category = Column(String(100))
    food_name = Column(String(200))
    temperature_c = Column(Float)
    aw = Column(Float)
    ph = Column(Float)
    assumed = Column(String(50))
    max_rate = Column(String(100))
    conditions = Column(Text)
    logcs = Column(Text)  # 存储时间序列数据，格式：time1;value1;time2;value2...
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseManager:
    def __init__(self, database_url=DATABASE_URL):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def insert_records(self, records_df):
        """批量插入记录，自动处理重复数据"""
        inserted_count = 0
        updated_count = 0
        
        for _, row in records_df.iterrows():
            existing_record = self.session.query(ComBaseRecord).filter_by(
                record_id=row.get('Record ID')
            ).first()
            
            if existing_record:
                # 更新现有记录
                for column in ComBaseRecord.__table__.columns:
                    if column.name not in ['id', 'created_at', 'updated_at']:
                        value = self._get_column_value(row, column.name)
                        if value is not None:
                            setattr(existing_record, column.name, value)
                existing_record.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # 创建新记录
                record = ComBaseRecord(
                    record_id=row.get('Record ID'),
                    organism=row.get('Organism'),
                    food_category=row.get('Food category'),
                    food_name=row.get('Food Name'),
                    temperature_c=self._safe_float(row.get('Temperature (C)')),
                    aw=self._safe_float(row.get('Aw')),
                    ph=self._safe_float(row.get('pH')),
                    assumed=row.get('Assumed'),
                    max_rate=row.get('Max.rate(logc.conc / h)'),
                    conditions=row.get('Conditions'),
                    logcs=row.get('Logcs')
                )
                self.session.add(record)
                inserted_count += 1
        
        self.session.commit()
        return inserted_count, updated_count
    
    def _get_column_value(self, row, column_name):
        """根据列名获取对应的行值"""
        column_mapping = {
            'record_id': 'Record ID',
            'organism': 'Organism',
            'food_category': 'Food category',
            'food_name': 'Food Name',
            'temperature_c': 'Temperature (C)',
            'aw': 'Aw',
            'ph': 'pH',
            'assumed': 'Assumed',
            'max_rate': 'Max.rate(logc.conc / h)',
            'conditions': 'Conditions',
            'logcs': 'Logcs'
        }
        return row.get(column_mapping.get(column_name))
    
    def _safe_float(self, value):
        """安全转换为浮点数"""
        if pd.isna(value) or value == '' or value == 'Not available':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_processed_record_ids(self):
        """获取已处理的记录ID列表"""
        records = self.session.query(ComBaseRecord.record_id).all()
        return [record[0] for record in records]
    
    def get_total_records(self):
        """获取总记录数"""
        return self.session.query(ComBaseRecord).count()
    
    def export_to_csv(self, filename):
        """导出数据到CSV文件"""
        query = self.session.query(ComBaseRecord)
        df = pd.read_sql(query.statement, self.engine)
        df.to_csv(filename, index=False)
        return len(df)
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()
