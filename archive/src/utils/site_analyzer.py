#!/usr/bin/env python3
"""
ComBase网站结构分析工具
用于分析网站的DOM结构，找到正确的选择器
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import LOGIN_URL, SEARCH_RESULTS_URL

class ComBaseSiteAnalyzer:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """设置浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def analyze_login_page(self):
        """分析登录页面结构"""
        print("分析登录页面...")
        self.driver.get(LOGIN_URL)
        time.sleep(3)
        
        print("\n=== 登录页面分析 ===")
        
        # 查找用户名输入框
        username_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
        print(f"找到 {len(username_inputs)} 个文本输入框:")
        for i, elem in enumerate(username_inputs):
            print(f"  {i+1}. ID: {elem.get_attribute('id')}, Name: {elem.get_attribute('name')}")
        
        # 查找密码输入框
        password_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        print(f"\n找到 {len(password_inputs)} 个密码输入框:")
        for i, elem in enumerate(password_inputs):
            print(f"  {i+1}. ID: {elem.get_attribute('id')}, Name: {elem.get_attribute('name')}")
        
        # 查找登录按钮
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button")
        print(f"\n找到 {len(buttons)} 个按钮:")
        for i, elem in enumerate(buttons):
            print(f"  {i+1}. ID: {elem.get_attribute('id')}, Name: {elem.get_attribute('name')}, Value: {elem.get_attribute('value')}, Text: {elem.text}")
    
    def manual_login(self):
        """手动登录（用户在浏览器中操作）"""
        print("\n请在浏览器中手动登录...")
        print("登录完成后，按回车键继续...")
        input()
    
    def analyze_search_results_page(self):
        """分析搜索结果页面结构"""
        print("\n=== 搜索结果页面分析 ===")
        
        # 导航到搜索结果页面
        self.driver.get(SEARCH_RESULTS_URL)
        time.sleep(5)
        
        # 查找表格
        tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
        print(f"找到 {len(tables)} 个表格:")
        for i, table in enumerate(tables):
            print(f"  {i+1}. ID: {table.get_attribute('id')}, Class: {table.get_attribute('class')}")
        
        # 查找复选框
        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        print(f"\n找到 {len(checkboxes)} 个复选框:")
        for i, checkbox in enumerate(checkboxes):
            print(f"  {i+1}. ID: {checkbox.get_attribute('id')}, Name: {checkbox.get_attribute('name')}")
        
        # 查找导出相关按钮
        export_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[value*='Export'], button[id*='Export'], a[id*='Export']")
        print(f"\n找到 {len(export_buttons)} 个导出按钮:")
        for i, button in enumerate(export_buttons):
            print(f"  {i+1}. ID: {button.get_attribute('id')}, Name: {button.get_attribute('name')}, Value: {button.get_attribute('value')}")
        
        # 查找分页控件
        page_controls = self.driver.find_elements(By.CSS_SELECTOR, "input[id*='Page'], input[id*='page'], a[id*='Page'], a[id*='page']")
        print(f"\n找到 {len(page_controls)} 个分页控件:")
        for i, control in enumerate(page_controls):
            print(f"  {i+1}. ID: {control.get_attribute('id')}, Name: {control.get_attribute('name')}, Text: {control.text}")
        
        # 查找页面信息
        page_info_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[id*='Page'], div[id*='Page'], span[id*='page'], div[id*='page']")
        print(f"\n找到 {len(page_info_elements)} 个页面信息元素:")
        for i, elem in enumerate(page_info_elements):
            print(f"  {i+1}. ID: {elem.get_attribute('id')}, Text: {elem.text[:50]}")
    
    def test_interactions(self):
        """测试交互功能"""
        print("\n=== 测试交互功能 ===")
        
        # 测试全选功能
        try:
            select_all = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][id*='SelectAll']")
            print("找到全选复选框，测试点击...")
            select_all.click()
            time.sleep(2)
            print("全选测试完成")
        except Exception as e:
            print(f"全选测试失败: {e}")
        
        # 测试导出功能
        try:
            export_button = self.driver.find_element(By.CSS_SELECTOR, "input[value*='Export']")
            print("找到导出按钮，但不会实际点击（避免下载文件）")
        except Exception as e:
            print(f"导出按钮测试失败: {e}")
    
    def generate_selectors(self):
        """生成选择器配置"""
        print("\n=== 生成选择器配置 ===")
        
        selectors = {}
        
        # 用户名输入框
        try:
            username_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
            selectors['username_input'] = f"input[name='{username_input.get_attribute('name')}']"
        except:
            selectors['username_input'] = "input[type='text']"
        
        # 密码输入框
        try:
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            selectors['password_input'] = f"input[name='{password_input.get_attribute('name')}']"
        except:
            selectors['password_input'] = "input[type='password']"
        
        # 登录按钮
        try:
            login_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            selectors['login_button'] = f"input[name='{login_button.get_attribute('name')}']"
        except:
            selectors['login_button'] = "input[type='submit']"
        
        # 导航到搜索结果页面分析
        self.driver.get(SEARCH_RESULTS_URL)
        time.sleep(3)
        
        # 结果表格
        try:
            table = self.driver.find_element(By.CSS_SELECTOR, "table")
            selectors['results_table'] = f"table[id='{table.get_attribute('id')}']" if table.get_attribute('id') else "table"
        except:
            selectors['results_table'] = "table"
        
        # 全选复选框
        try:
            select_all = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][id*='SelectAll']")
            selectors['select_all_checkbox'] = f"input[id='{select_all.get_attribute('id')}']"
        except:
            selectors['select_all_checkbox'] = "input[type='checkbox'][id*='SelectAll']"
        
        # 记录复选框
        try:
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']:not([id*='SelectAll'])")
            if checkboxes:
                first_checkbox = checkboxes[0]
                checkbox_id = first_checkbox.get_attribute('id')
                # 提取ID模式
                import re
                pattern = re.sub(r'\d+', '*', checkbox_id)
                selectors['record_checkboxes'] = f"input[id*='{pattern.split('*')[0]}']"
            else:
                selectors['record_checkboxes'] = "input[type='checkbox']:not([id*='SelectAll'])"
        except:
            selectors['record_checkboxes'] = "input[type='checkbox']"
        
        # 导出按钮
        try:
            export_button = self.driver.find_element(By.CSS_SELECTOR, "input[value*='Export']")
            selectors['export_button'] = f"input[id='{export_button.get_attribute('id')}']"
        except:
            selectors['export_button'] = "input[value*='Export']"
        
        print("建议的选择器配置:")
        for key, value in selectors.items():
            print(f"    '{key}': '{value}',")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()

def main():
    """主函数"""
    analyzer = ComBaseSiteAnalyzer()
    
    try:
        # 分析登录页面
        analyzer.analyze_login_page()
        
        # 手动登录
        analyzer.manual_login()
        
        # 分析搜索结果页面
        analyzer.analyze_search_results_page()
        
        # 测试交互
        analyzer.test_interactions()
        
        # 生成选择器
        analyzer.generate_selectors()
        
        print("\n分析完成！请根据上述信息更新config.py中的SELECTORS配置。")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
    finally:
        print("\n按回车键关闭浏览器...")
        input()
        analyzer.close()

if __name__ == "__main__":
    main()
