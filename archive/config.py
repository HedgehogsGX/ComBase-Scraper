"""
ComBase数据爬取配置文件
"""
import os
from pathlib import Path

# 基础配置
BASE_URL = "https://combasebrowser.errc.ars.usda.gov"
LOGIN_URL = "https://combasebrowser.errc.ars.usda.gov/membership/Login.aspx"
SEARCH_RESULTS_URL = "https://combasebrowser.errc.ars.usda.gov/SearchResults.aspx"
DOWNLOAD_DIR = Path("downloads")
DATA_DIR = Path("data")
LOG_DIR = Path("logs")

# 登录配置 - 需要用户提供
LOGIN_USERNAME = ""  # 用户需要填写
LOGIN_PASSWORD = ""  # 用户需要填写

# 创建必要的目录
for dir_path in [DOWNLOAD_DIR, DATA_DIR, LOG_DIR]:
    dir_path.mkdir(exist_ok=True)

# 爬取配置 - 根据实际测试结果更新
TOTAL_PAGES = 6075  # 实际发现有6075页数据
RECORDS_PER_PAGE = 10
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒
PAGE_LOAD_TIMEOUT = 30  # 秒
DOWNLOAD_TIMEOUT = 60  # 秒

# 浏览器配置
HEADLESS = False  # 设为True可以无界面运行
WINDOW_SIZE = (1920, 1080)

# 数据库配置
DATABASE_URL = "sqlite:///data/combase_data.db"

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 选择器配置（根据ComBase网站实际测试结果）
SELECTORS = {
    # 登录页面 - 基于实际测试结果
    "username_input": "input[name='Login1$UserName']",
    "password_input": "input[name='Login1$Password']",
    "login_button": "input[name='Login1$Button1']",

    # 搜索结果页面 - 根据调试结果更新
    "select_all_checkbox": "input[type='checkbox'][id*='SelectAll']",
    "record_checkboxes": "input[id='chkRecordSummary']",  # 调试发现的正确选择器
    "export_button": "input[id='cbBtnExportToExcel']",
    "results_table": "table[id*='gvResults']",
    "page_info": "span[id*='lblPageInfo']",
    "loading_indicator": "div[id*='UpdateProgress']",

    # 分页控件
    "next_page_button": "input[id*='btnNext']",
    "page_number_input": "input[id*='txtPageNumber']",
    "go_to_page_button": "input[id*='btnGoToPage']",
    "first_page_button": "input[id*='btnFirst']",
    "last_page_button": "input[id*='btnLast']"
}

# Excel文件配置
EXCEL_COLUMNS = [
    "Record ID", "Organism", "Food category", "Food Name", 
    "Temperature (C)", "Aw", "pH", "Assumed", "Max.rate(logc.conc / h)", 
    "Conditions", "Logcs"
]

# 数据清洗配置
REQUIRED_COLUMNS = ["Record ID", "Organism", "Food category"]
