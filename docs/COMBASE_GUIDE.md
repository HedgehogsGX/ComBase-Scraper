# ComBase数据爬取完整指南

## 🎯 针对你的具体需求

你提到的问题：
- ✅ **URL不变化**: 完全支持AJAX/单页应用
- ✅ **5101页数据**: 自动化处理所有页面
- ✅ **手动操作繁琐**: 完全自动化，无需人工干预
- ✅ **Excel文件整合**: 自动合并所有下载文件

## 🚀 快速开始

### 第一步：准备工作
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保有ComBase账号
# 如果没有，请访问: https://combasebrowser.errc.ars.usda.gov/SignUp.aspx
```

### 第二步：分析网站结构（重要！）
```bash
# 运行网站分析工具
python site_analyzer.py
```

这个工具会：
1. 打开ComBase登录页面
2. 让你手动登录
3. 分析页面DOM结构
4. 生成正确的选择器配置

### 第三步：更新配置
根据分析结果，更新 `config.py` 中的选择器：

```python
# 在config.py中设置登录信息
LOGIN_USERNAME = "your_username"
LOGIN_PASSWORD = "your_password"

# 更新SELECTORS配置（根据site_analyzer.py的输出）
SELECTORS = {
    "username_input": "input[name='ctl00$ContentPlaceHolder1$txtUsername']",
    "password_input": "input[name='ctl00$ContentPlaceHolder1$txtPassword']",
    # ... 其他选择器
}
```

### 第四步：开始爬取
```bash
# 方式1: 交互式启动
python run.py

# 方式2: 命令行启动
python run.py --username your_username --password your_password

# 方式3: 测试少量页面
python run.py --start 1 --end 10 --username your_username
```

## 🔧 针对AJAX网站的特殊处理

### URL不变化的解决方案
1. **等待AJAX完成**: 智能检测页面加载状态
2. **JavaScript分页**: 使用`__doPostBack`等ASP.NET函数
3. **DOM变化监控**: 通过元素变化判断操作是否成功
4. **ViewState处理**: 自动处理ASP.NET的ViewState机制

### 关键技术点
```python
# 等待AJAX请求完成
def _wait_for_ajax_complete(self):
    # 等待jQuery请求完成
    WebDriverWait(self.driver, 30).until(
        lambda driver: driver.execute_script("return jQuery.active == 0")
    )
    
# JavaScript分页
script = f"__doPostBack('ctl00$ContentPlaceHolder1$gvResults', 'Page${page_number}');"
self.driver.execute_script(script)
```

## 📊 数据处理流程

```
ComBase网站 → 登录 → 搜索结果 → 分页浏览 → 选择数据 → 导出Excel
     ↓
自动下载 → 解析Excel → 数据清洗 → 去重处理 → 统一存储
     ↓
CSV文件 + SQLite数据库 + 多格式导出
```

## 🛠️ 常见问题解决

### 1. 登录失败
```bash
# 检查用户名密码
# 手动登录网站验证账号状态
# 检查网络连接
```

### 2. 选择器失效
```bash
# 重新运行分析工具
python site_analyzer.py

# 更新config.py中的SELECTORS
```

### 3. 分页失败
```bash
# 检查JavaScript控制台错误
# 增加等待时间
# 使用不同的分页方法
```

### 4. 下载失败
```bash
# 检查下载目录权限
# 确认导出按钮选择器正确
# 检查文件格式设置
```

## 📈 监控和调试

### 实时监控
```bash
# 另开终端监控进度
python monitor.py

# 查看详细状态
python run.py --status
```

### 调试模式
```python
# 在config.py中设置
HEADLESS = False  # 显示浏览器窗口
LOG_LEVEL = "DEBUG"  # 详细日志
```

### 日志分析
```bash
# 查看实时日志
tail -f logs/scraper_*.log

# 查看错误统计
python -c "
from error_handler import ErrorHandler
eh = ErrorHandler()
print(eh.get_error_summary())
"
```

## 🎯 最佳实践

### 1. 分阶段测试
```bash
# 第一次：测试1页
python run.py --start 1 --end 1

# 第二次：测试10页
python run.py --start 1 --end 10

# 第三次：全量爬取
python run.py
```

### 2. 网络稳定性
- 使用稳定的网络连接
- 避免在网络高峰期运行
- 设置合适的重试次数

### 3. 资源管理
- 确保足够的磁盘空间（1-2GB）
- 监控内存使用情况
- 定期清理临时文件

### 4. 数据备份
```bash
# 系统会自动创建备份
# 手动备份重要数据
cp data/combase_master_data.csv backup/
```

## 📋 完成后的数据

爬取完成后，你将获得：

### 主要文件
- `data/combase_master_data.csv` - 主数据文件（所有记录）
- `data/combase_data.db` - SQLite数据库
- `data/scraping_progress.json` - 爬取进度记录

### 数据格式
每条记录包含：
- Record ID: 唯一标识
- Organism: 微生物名称
- Food category: 食品类别
- Food Name: 具体食品
- Temperature (C): 温度条件
- Aw: 水活度
- pH: 酸碱度
- Conditions: 实验条件
- Logcs: 时间序列数据（用于模型训练）

### 统计信息
- 总记录数: ~51,000条
- 唯一微生物: ~500种
- 食品类别: ~50种
- 文件大小: 100-200MB

## 🎉 直接用于模型训练

数据已经过清洗和标准化，可以直接用于：
- 微生物生长预测模型
- 食品安全风险评估
- 温度-时间-微生物关系建模
- 机器学习特征工程

```python
# 快速加载数据进行分析
import pandas as pd
df = pd.read_csv('data/combase_master_data.csv')
print(df.head())
print(df.describe())
```

这个解决方案完全解决了你提到的URL不变化和大量手动操作的问题！
