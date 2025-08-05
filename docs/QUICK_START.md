# ComBase 爬虫快速启动指南

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置登录信息
在 `config.py` 中设置你的ComBase账号：
```python
LOGIN_USERNAME = "your_username"
LOGIN_PASSWORD = "your_password"
```

### 3. 分析网站结构（首次使用）
```bash
python site_analyzer.py
```
这会帮助你确认网站的DOM结构和选择器。

### 4. 测试环境
```bash
python test_setup.py
```

### 5. 开始爬取
```bash
python run.py
```

## 📋 针对ComBase网站的完整解决方案

这个爬虫专门针对ComBase网站设计，解决了你提到的所有问题：

### ✅ 处理AJAX/单页应用
- URL不变化的网站完全支持
- 智能等待AJAX请求完成
- 通过DOM变化判断页面状态
- 使用JavaScript触发分页操作

### ✅ 自动化处理5101页数据
- 自动登录ComBase系统
- 自动勾选每页的所有记录
- 自动点击导出按钮
- 智能处理AJAX分页跳转
- 支持断点续传

### ✅ 智能数据整合
- 自动下载和处理5101个Excel文件
- 去重处理，避免重复数据
- 统一数据格式和结构
- 实时数据验证

### ✅ 多种存储方案
1. **CSV文件**: `data/combase_master_data.csv`
2. **SQLite数据库**: `data/combase_data.db`
3. **Excel文件**: 可导出为Excel格式
4. **JSON文件**: 可导出为JSON格式

### ✅ 健壮的错误处理
- 网络错误自动重试
- 浏览器崩溃自动恢复
- 失败页面单独重试
- 数据完整性验证

### ✅ 实时监控
- 进度实时显示
- 完成时间估算
- 系统资源监控
- 错误统计分析

## 🎯 核心优势

### 1. 完全自动化
```bash
# 一键启动，无需人工干预
python scraper.py
```

### 2. 断点续传
```bash
# 中断后继续爬取
python run.py --continue
```

### 3. 失败重试
```bash
# 重试失败的页面
python run.py --retry
```

### 4. 实时监控
```bash
# 另开终端监控进度
python monitor.py
```

## 📊 数据处理流程

```
网页数据 → Excel下载 → 数据清洗 → 去重处理 → 统一存储
    ↓           ↓          ↓         ↓         ↓
  5101页    5101个文件   标准化格式   唯一记录   多种格式
```

## 🔧 配置选项

在 `config.py` 中可以调整：

```python
# 基本配置
TOTAL_PAGES = 5101          # 总页数
HEADLESS = False            # 是否显示浏览器
MAX_RETRIES = 3             # 重试次数
RETRY_DELAY = 5             # 重试延迟

# 性能优化
PAGE_LOAD_TIMEOUT = 30      # 页面加载超时
DOWNLOAD_TIMEOUT = 60       # 下载超时
```

## 📈 预期结果

### 数据量估算
- **总页数**: 5,101页
- **每页记录**: ~10条
- **总记录数**: ~51,000条
- **文件大小**: ~100-200MB
- **处理时间**: 8-12小时（取决于网络）

### 输出文件
```
data/
├── combase_master_data.csv     # 主数据文件
├── combase_data.db            # SQLite数据库
├── scraping_progress.json     # 爬取进度
└── processed/                 # 已处理的Excel文件

logs/
└── scraper_YYYYMMDD_HHMMSS.log  # 详细日志

downloads/
└── (临时Excel文件)
```

## 🔑 ComBase特殊说明

### 网站特点
- **AJAX单页应用**: URL不会改变，所有操作通过JavaScript完成
- **需要登录**: 必须有有效的ComBase账号
- **动态加载**: 数据通过AJAX动态加载，需要等待
- **ASP.NET框架**: 使用ViewState和PostBack机制

### 首次使用步骤
1. **注册ComBase账号**: 访问 https://combasebrowser.errc.ars.usda.gov/SignUp.aspx
2. **分析网站结构**: 运行 `python site_analyzer.py`
3. **更新选择器**: 根据分析结果更新config.py中的SELECTORS
4. **测试小范围**: 先测试1-10页确保正常工作

## 🛠️ 故障排除

### 常见问题

1. **登录失败**
   ```bash
   # 检查用户名密码是否正确
   # 确保账号未被锁定
   # 尝试手动登录网站验证
   ```

2. **选择器失效**
   ```bash
   # 运行网站分析工具
   python site_analyzer.py
   # 根据结果更新config.py中的SELECTORS
   ```

3. **AJAX等待超时**
   ```bash
   # 增加等待时间
   # 在config.py中调整PAGE_LOAD_TIMEOUT
   ```

4. **网络连接问题**
   ```bash
   # 测试网站连接
   curl -I https://combasebrowser.errc.ars.usda.gov
   ```

### 调试模式

```bash
# 显示浏览器窗口（调试用）
# 在config.py中设置 HEADLESS = False

# 查看详细日志
tail -f logs/scraper_*.log

# 检查错误统计
python -c "
from error_handler import ErrorHandler
eh = ErrorHandler()
print(eh.get_error_summary())
"
```

## 💡 使用建议

1. **首次运行**: 建议先测试少量页面
   ```bash
   python run.py --start 1 --end 10
   ```

2. **稳定网络**: 在稳定的网络环境下运行

3. **充足空间**: 确保有1-2GB可用磁盘空间

4. **定期备份**: 系统会自动创建备份

5. **监控运行**: 使用monitor.py实时查看进度

## 🎉 完成后

爬取完成后，你将获得：
- 完整的ComBase数据集
- 多种格式的数据文件
- 详细的爬取日志
- 数据质量报告

可以直接用于机器学习模型训练！
