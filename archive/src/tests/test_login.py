#!/usr/bin/env python3
"""
ComBase登录功能测试
"""
import time
import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import LOGIN_URL, SEARCH_RESULTS_URL, SELECTORS

class LoginTester:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.setup_browser()
    
    def setup_browser(self):
        """设置浏览器"""
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1200,800")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
        print("✓ 浏览器启动成功")
    
    def test_login(self, username, password):
        """测试登录功能"""
        try:
            print(f"访问登录页面: {LOGIN_URL}")
            self.driver.get(LOGIN_URL)
            time.sleep(2)
            
            print(f"当前URL: {self.driver.current_url}")
            print(f"页面标题: {self.driver.title}")
            
            # 查找并填写用户名
            print("查找用户名输入框...")
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["username_input"]))
            )
            print(f"✓ 找到用户名输入框: {SELECTORS['username_input']}")
            
            username_input.clear()
            username_input.send_keys(username)
            print("✓ 用户名已输入")
            
            # 查找并填写密码
            print("查找密码输入框...")
            password_input = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["password_input"])
            print(f"✓ 找到密码输入框: {SELECTORS['password_input']}")
            
            password_input.clear()
            password_input.send_keys(password)
            print("✓ 密码已输入")
            
            # 查找并点击登录按钮
            print("查找登录按钮...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, SELECTORS["login_button"])
            print(f"✓ 找到登录按钮: {SELECTORS['login_button']}")
            
            print("点击登录按钮...")
            login_button.click()
            
            # 等待页面跳转
            print("等待登录结果...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"登录后URL: {current_url}")
            
            # 检查登录结果
            if "Login.aspx" not in current_url:
                print("✓ 登录成功！已跳转到其他页面")
                
                # 尝试访问搜索结果页面
                print(f"\n测试访问搜索结果页面: {SEARCH_RESULTS_URL}")
                self.driver.get(SEARCH_RESULTS_URL)
                time.sleep(3)
                
                search_url = self.driver.current_url
                search_title = self.driver.title
                
                print(f"搜索页面URL: {search_url}")
                print(f"搜索页面标题: {search_title}")
                
                # 分析搜索结果页面
                self.analyze_search_page()
                
                return True
            else:
                print("✗ 登录失败，仍在登录页面")
                
                # 检查错误信息
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .message, [id*='error'], [class*='error']")
                    if error_elements:
                        for elem in error_elements:
                            if elem.text.strip():
                                print(f"错误信息: {elem.text}")
                except:
                    pass
                
                return False
                
        except Exception as e:
            print(f"✗ 登录测试失败: {e}")
            return False
    
    def analyze_search_page(self):
        """分析搜索结果页面"""
        print("\n=== 分析搜索结果页面 ===")
        
        try:
            # 查找表格
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"找到 {len(tables)} 个表格")
            
            for i, table in enumerate(tables):
                table_id = table.get_attribute("id") or ""
                table_class = table.get_attribute("class") or ""
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"  表格 {i+1}: ID='{table_id}', Class='{table_class}', 行数={len(rows)}")
            
            # 查找复选框
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            print(f"\n找到 {len(checkboxes)} 个复选框")
            
            for i, cb in enumerate(checkboxes[:5]):  # 只显示前5个
                cb_id = cb.get_attribute("id") or ""
                cb_name = cb.get_attribute("name") or ""
                print(f"  复选框 {i+1}: ID='{cb_id}', Name='{cb_name}'")
            
            # 查找导出按钮
            export_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[value*='Export'], input[value*='export'], button[id*='Export'], button[id*='export']")
            print(f"\n找到 {len(export_buttons)} 个导出按钮")
            
            for i, btn in enumerate(export_buttons):
                btn_id = btn.get_attribute("id") or ""
                btn_value = btn.get_attribute("value") or ""
                btn_text = btn.text or ""
                print(f"  按钮 {i+1}: ID='{btn_id}', Value='{btn_value}', Text='{btn_text}'")
            
            # 查找分页控件
            page_controls = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[id*='Page'], a[id*='Page'], span[id*='Page']")
            print(f"\n找到 {len(page_controls)} 个分页控件")
            
            for i, ctrl in enumerate(page_controls[:5]):  # 只显示前5个
                ctrl_id = ctrl.get_attribute("id") or ""
                ctrl_text = ctrl.text or ""
                print(f"  控件 {i+1}: ID='{ctrl_id}', Text='{ctrl_text}'")
            
            # 生成更新的选择器建议
            self.generate_updated_selectors(tables, checkboxes, export_buttons, page_controls)
            
        except Exception as e:
            print(f"页面分析失败: {e}")
    
    def generate_updated_selectors(self, tables, checkboxes, export_buttons, page_controls):
        """生成更新的选择器配置"""
        print("\n=== 建议的选择器更新 ===")
        
        selectors = {}
        
        # 结果表格
        if tables:
            main_table = tables[0]  # 假设第一个表格是主要的数据表格
            table_id = main_table.get_attribute("id")
            if table_id:
                selectors['results_table'] = f"table[id='{table_id}']"
            else:
                selectors['results_table'] = "table"
        
        # 复选框
        if checkboxes:
            # 查找全选复选框
            select_all_cb = None
            record_cbs = []
            
            for cb in checkboxes:
                cb_id = cb.get_attribute("id") or ""
                cb_name = cb.get_attribute("name") or ""
                
                if "selectall" in cb_id.lower() or "selectall" in cb_name.lower():
                    select_all_cb = cb
                else:
                    record_cbs.append(cb)
            
            if select_all_cb:
                selectors['select_all_checkbox'] = f"input[id='{select_all_cb.get_attribute('id')}']"
            
            if record_cbs:
                first_record_cb = record_cbs[0]
                cb_id = first_record_cb.get_attribute("id")
                if cb_id:
                    # 提取ID模式
                    import re
                    pattern = re.sub(r'\d+', '*', cb_id)
                    selectors['record_checkboxes'] = f"input[id*='{pattern.split('*')[0]}']"
        
        # 导出按钮
        if export_buttons:
            export_btn = export_buttons[0]
            btn_id = export_btn.get_attribute("id")
            if btn_id:
                selectors['export_button'] = f"input[id='{btn_id}']"
        
        print("建议添加到config.py的SELECTORS中:")
        for key, value in selectors.items():
            print(f"    '{key}': '{value}',")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()

def main():
    """主函数"""
    print("ComBase登录功能测试")
    print("=" * 40)
    
    # 获取登录信息
    username = input("请输入ComBase用户名: ").strip()
    password = getpass.getpass("请输入ComBase密码: ")
    
    if not username or not password:
        print("用户名和密码不能为空")
        return
    
    tester = LoginTester()
    
    try:
        success = tester.test_login(username, password)
        
        if success:
            print("\n🎉 登录测试成功！")
            print("网站访问正常，可以开始数据爬取。")
        else:
            print("\n❌ 登录测试失败")
            print("请检查用户名和密码是否正确。")
        
        print("\n按回车键关闭浏览器...")
        input()
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中出错: {e}")
    finally:
        tester.close()

if __name__ == "__main__":
    main()
