# ComBase爬虫项目

简化的ComBase数据爬取工具，使用修复后的完整organism名称格式。

## 🚀 快速开始

```bash
python simple_scraper.py
```

## 📁 项目结构

```
├── simple_scraper.py          # 主爬虫程序（单终端显示进度）
├── data/                      # 输出数据目录
│   └── combase_records_*.csv  # 爬取的数据文件
├── src/                       # 核心代码
│   ├── scrapers/              # 爬虫模块
│   ├── processors/            # 数据处理模块
│   └── utils/                 # 工具模块
├── config/                    # 配置文件
├── logs/                      # 日志文件
└── docs/                      # 文档
```

## ✨ 特性

- ✅ **完整名称格式**: organism字段包含编号、生物名称和食物描述
  - 例如: `31. Aerobic total spoilage bacteria in oyster (Saccostrea glomerata)`
- ✅ **进度显示**: 实时进度条、当前页数、保存次数
- ✅ **自动保存**: 每1000条记录保存一个文件
- ✅ **安全中断**: 支持Ctrl+C安全停止
- ✅ **简洁界面**: 单终端显示所有信息

## 📊 数据格式

修复后的数据包含完整的organism名称：

```csv
record_id,organism,food,temperature,aw,ph,page_number,logc_points,logc_duration,logc_initial,logc_final,logc_series_json
4284,1. Aerobic total spoilage bacteria in precooked beef,in precooked beef,4,Not specified,6,1,7,2040.0,3.5,4.5,"[[0.0, 3.5], [168.0, 5.2], ...]"
```

## 🎯 目标

- 爬取所有6075页数据
- 每1000条记录保存一个文件
- 使用修复后的完整organism名称格式

## 💡 使用说明

1. 运行 `python simple_scraper.py`
2. 观察进度条和统计信息
3. 按Ctrl+C可以安全停止
4. 数据保存在 `data/` 目录下
