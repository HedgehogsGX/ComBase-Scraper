"""
浏览器自动化控制模块
"""
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging
from config import *

class ComBaseBrowserController:
    def __init__(self, headless=HEADLESS, download_dir=DOWNLOAD_DIR):
        self.download_dir = Path(download_dir).absolute()
        self.download_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.wait = None
        self._setup_driver(headless)
    
    def _setup_driver(self, headless):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        # 设置下载目录
        prefs = {
            "download.default_directory": str(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 其他选项
        chrome_options.add_argument(f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 自动下载ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT)
        
        self.logger.info("浏览器驱动初始化完成")
    
    def login(self, username, password):
        """登录ComBase系统"""
        try:
            # 导航到登录页面
            self.driver.get(LOGIN_URL)
            self.logger.info("已导航到登录页面")

            # 等待登录表单加载
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["username_input"]))
            )
            password_input = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["password_input"])
            login_button = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["login_button"])

            # 输入用户名和密码
            username_input.clear()
            username_input.send_keys(username)
            password_input.clear()
            password_input.send_keys(password)

            # 点击登录
            login_button.click()
            self.logger.info("已提交登录信息")

            # 等待登录完成（检查是否跳转或出现错误信息）
            time.sleep(3)

            # 检查是否登录成功
            current_url = self.driver.current_url
            if "Login.aspx" not in current_url or "SearchResults.aspx" in current_url:
                self.logger.info("登录成功")
                return True
            else:
                self.logger.error("登录失败，请检查用户名和密码")
                return False

        except Exception as e:
            self.logger.error(f"登录过程出错: {e}")
            return False

    def navigate_to_search_results(self):
        """导航到搜索结果页面"""
        try:
            self.driver.get(SEARCH_RESULTS_URL)
            self.logger.info(f"已导航到搜索结果页面")

            # 等待页面加载完成
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # 等待结果表格加载
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["results_table"]))
                )
                self.logger.info("搜索结果表格已加载")
            except TimeoutException:
                self.logger.warning("未找到结果表格，可能需要先执行搜索")

            time.sleep(2)  # 额外等待确保AJAX完成
            return True

        except Exception as e:
            self.logger.error(f"导航到搜索结果失败: {e}")
            return False
    
    def go_to_page(self, page_number):
        """跳转到指定页面（AJAX方式）"""
        try:
            # 方法1: 使用页面输入框
            try:
                page_input = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["page_number_input"])
                go_button = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["go_to_page_button"])

                page_input.clear()
                page_input.send_keys(str(page_number))
                go_button.click()

                self.logger.info(f"通过页面输入框跳转到第 {page_number} 页")

            except NoSuchElementException:
                # 方法2: 使用JavaScript直接触发分页
                self.logger.info(f"使用JavaScript跳转到第 {page_number} 页")
                script = f"""
                try {{
                    // 查找分页相关的JavaScript函数
                    if (typeof window.__doPostBack !== 'undefined') {{
                        window.__doPostBack('ctl00$ContentPlaceHolder1$gvResults', 'Page${page_number}');
                    }} else if (typeof window.WebForm_DoPostBackWithOptions !== 'undefined') {{
                        var options = {{
                            eventTarget: 'ctl00$ContentPlaceHolder1$gvResults',
                            eventArgument: 'Page${page_number}',
                            validation: true,
                            validationGroup: '',
                            actionUrl: '',
                            trackFocus: false,
                            clientSubmit: true
                        }};
                        window.WebForm_DoPostBackWithOptions(options);
                    }} else {{
                        // 尝试查找分页链接并点击
                        var pageLinks = document.querySelectorAll('a[href*="Page${page_number}"]');
                        if (pageLinks.length > 0) {{
                            pageLinks[0].click();
                        }}
                    }}
                }} catch(e) {{
                    console.log('分页JavaScript执行失败:', e);
                }}
                """
                self.driver.execute_script(script)

            # 等待AJAX请求完成
            self._wait_for_ajax_complete()

            # 验证页面是否成功跳转
            if self._verify_page_number(page_number):
                self.logger.info(f"成功跳转到第 {page_number} 页")
                return True
            else:
                self.logger.warning(f"跳转到第 {page_number} 页可能失败")
                return False

        except Exception as e:
            self.logger.error(f"跳转到第 {page_number} 页失败: {e}")
            return False

    def _wait_for_ajax_complete(self, timeout=30):
        """等待AJAX请求完成"""
        try:
            # 等待加载指示器消失
            try:
                loading_indicator = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["loading_indicator"])
                WebDriverWait(self.driver, timeout).until(
                    EC.invisibility_of_element(loading_indicator)
                )
            except (NoSuchElementException, TimeoutException):
                pass

            # 等待JavaScript执行完成
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return jQuery.active == 0") if
                driver.execute_script("return typeof jQuery !== 'undefined'") else True
            )

            # 额外等待确保DOM更新完成
            time.sleep(1)

        except Exception as e:
            self.logger.warning(f"等待AJAX完成时出错: {e}")

    def _verify_page_number(self, expected_page):
        """验证当前页码"""
        try:
            # 从页面信息元素获取当前页码
            page_info = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["page_info"])
            page_text = page_info.text

            # 解析页码信息（格式可能是 "Page 1 of 100" 等）
            import re
            match = re.search(r'Page\s+(\d+)', page_text, re.IGNORECASE)
            if match:
                current_page = int(match.group(1))
                return current_page == expected_page

            return True  # 如果无法验证，假设成功

        except Exception:
            return True  # 如果无法验证，假设成功
    
    def select_all_records(self):
        """选择当前页面的所有记录"""
        try:
            # 等待表格加载完成
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["results_table"]))
            )

            # 方法1: 查找全选复选框
            try:
                select_all = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["select_all_checkbox"])
                if select_all.is_displayed() and select_all.is_enabled():
                    if not select_all.is_selected():
                        # 使用JavaScript点击，避免元素被遮挡
                        self.driver.execute_script("arguments[0].click();", select_all)
                        time.sleep(0.5)  # 等待选择生效
                        self.logger.info("已点击全选复选框")
                        return True
                    else:
                        self.logger.info("全选复选框已选中")
                        return True
            except NoSuchElementException:
                self.logger.warning("未找到全选复选框，尝试逐个选择")

            # 方法2: 使用调试发现的正确选择器选择数据复选框
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[id='chkRecordSummary']")

            if not checkboxes:
                self.logger.warning("未找到任何数据复选框")
                return False

            self.logger.info(f"找到 {len(checkboxes)} 个数据复选框")

            selected_count = 0
            for i, checkbox in enumerate(checkboxes):
                try:
                    if checkbox.is_displayed() and checkbox.is_enabled():
                        if not checkbox.is_selected():
                            # 使用JavaScript点击确保成功
                            self.driver.execute_script("arguments[0].click();", checkbox)
                            selected_count += 1
                            self.logger.debug(f"已选择第 {i+1} 个复选框")
                        else:
                            selected_count += 1
                            self.logger.debug(f"第 {i+1} 个复选框已经选中")
                        time.sleep(0.2)  # 稍微等待一下
                except Exception as e:
                    self.logger.warning(f"选择第 {i+1} 个复选框时出错: {e}")
                    continue

            self.logger.info(f"成功选择了 {selected_count} 个记录")
            return selected_count > 0

        except Exception as e:
            self.logger.error(f"选择记录失败: {e}")
            return False
    
    def export_data(self):
        """导出选中的数据"""
        try:
            # 等待导出按钮变为可用状态
            time.sleep(2)

            # 使用调试发现的正确选择器查找导出按钮
            export_button = None

            # 尝试不同的导出按钮选择器
            export_selectors = [
                "input[id='cbBtnExportToExcel']",  # 调试发现的正确选择器
                "input[value='Export']",
                "input[type='submit'][value='Export']"
            ]

            for selector in export_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            export_button = btn
                            self.logger.info(f"找到导出按钮: {selector}")
                            break
                    if export_button:
                        break
                except NoSuchElementException:
                    continue

            if not export_button:
                self.logger.error("未找到导出按钮")
                return False

            # 检查按钮是否可用，如果不可用则等待
            if not export_button.is_enabled():
                self.logger.warning("导出按钮不可用，等待激活...")
                # 等待按钮变为可用
                for _ in range(10):  # 最多等待10秒
                    time.sleep(1)
                    if export_button.is_enabled():
                        self.logger.info("导出按钮已激活")
                        break
                else:
                    self.logger.error("导出按钮始终不可用")
                    return False

            # 记录导出前的文件数量
            files_before = len(list(self.download_dir.glob("*.xlsx")))
            files_before += len(list(self.download_dir.glob("*.xls")))
            files_before += len(list(self.download_dir.glob("*.csv")))

            # 点击导出按钮
            self.driver.execute_script("arguments[0].click();", export_button)
            self.logger.info("已点击导出按钮")

            # 等待可能的弹窗或确认对话框
            time.sleep(2)

            # 处理可能的文件格式选择对话框
            try:
                # 查找Excel格式选项
                excel_option = self.driver.find_element(By.XPATH, "//input[@value='Excel' or @value='xlsx']")
                excel_option.click()

                # 查找确认按钮
                confirm_button = self.driver.find_element(By.XPATH, "//input[@value='OK' or @value='Export' or @value='Download']")
                confirm_button.click()

                self.logger.info("已选择Excel格式并确认导出")
            except NoSuchElementException:
                self.logger.info("未发现格式选择对话框，直接下载")

            # 等待文件下载完成
            download_success = self._wait_for_download(files_before)

            if download_success:
                self.logger.info("文件下载完成")
                return True
            else:
                self.logger.error("文件下载超时")
                return False

        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            return False
    
    def _wait_for_download(self, files_before, timeout=DOWNLOAD_TIMEOUT):
        """等待文件下载完成"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 检查是否有新的文件（支持多种格式）
            current_files = []
            current_files.extend(list(self.download_dir.glob("*.xlsx")))
            current_files.extend(list(self.download_dir.glob("*.xls")))
            current_files.extend(list(self.download_dir.glob("*.csv")))

            if len(current_files) > files_before:
                # 检查文件是否下载完成（不是临时文件）
                latest_file = max(current_files, key=os.path.getctime)
                file_name = str(latest_file)

                # 检查是否为临时文件
                if not (file_name.endswith('.crdownload') or
                       file_name.endswith('.tmp') or
                       file_name.endswith('.part')):
                    # 额外检查文件大小是否稳定
                    initial_size = latest_file.stat().st_size
                    time.sleep(2)
                    final_size = latest_file.stat().st_size

                    if initial_size == final_size and final_size > 0:
                        self.logger.info(f"下载完成: {latest_file.name} ({final_size} bytes)")
                        return True

            time.sleep(1)

        self.logger.warning(f"下载超时 ({timeout}秒)")
        return False
    
    def get_current_page_info(self):
        """获取当前页面信息"""
        try:
            # 尝试从页面元素获取信息
            page_info_element = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["page_info"])
            page_info = page_info_element.text
            
            # 解析页面信息，提取当前页码和总页数
            # 这里需要根据实际网站的页面信息格式进行调整
            return page_info
            
        except NoSuchElementException:
            # 如果找不到页面信息元素，从URL获取
            current_url = self.driver.current_url
            if "page=" in current_url:
                page_num = current_url.split("page=")[1].split("&")[0]
                return f"Page {page_num}"
            
            return "Unknown page"
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.logger.info("浏览器已关闭")
