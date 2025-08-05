#!/usr/bin/env python3
"""
ComBase网站访问测试脚本
测试网站连接、页面结构和登录功能
"""
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class ComBaseWebsiteTest:
    def __init__(self):
        self.base_url = "https://combasebrowser.errc.ars.usda.gov"
        self.login_url = f"{self.base_url}/Login.aspx"
        self.search_url = f"{self.base_url}/SearchResults.aspx"
        self.driver = None
    
    def test_basic_connectivity(self):
        """测试基本网络连接"""
        print("=== 测试网络连接 ===")
        
        try:
            response = requests.get(self.base_url, timeout=10)
            print(f"✓ 网站可访问")
            print(f"  状态码: {response.status_code}")
            print(f"  响应时间: {response.elapsed.total_seconds():.2f}秒")
            
            # 检查是否重定向到登录页面
            if "Login.aspx" in response.url:
                print("  → 自动重定向到登录页面")
            
            return True
            
        except requests.exceptions.Timeout:
            print("✗ 网站访问超时")
            return False
        except requests.exceptions.ConnectionError:
            print("✗ 网络连接失败")
            return False
        except Exception as e:
            print(f"✗ 访问失败: {e}")
            return False
    
    def test_login_page(self):
        """测试登录页面"""
        print("\n=== 测试登录页面 ===")
        
        try:
            response = requests.get(self.login_url, timeout=10)
            print(f"✓ 登录页面可访问 (状态码: {response.status_code})")
            
            # 检查页面内容
            content = response.text.lower()
            if "username" in content or "user name" in content:
                print("✓ 发现用户名输入框")
            if "password" in content:
                print("✓ 发现密码输入框")
            if "login" in content or "sign in" in content:
                print("✓ 发现登录按钮")
            
            return True
            
        except Exception as e:
            print(f"✗ 登录页面访问失败: {e}")
            return False
    
    def setup_browser(self):
        """设置浏览器"""
        print("\n=== 设置浏览器 ===")
        
        try:
            chrome_options = Options()
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✓ 浏览器启动成功")
            return True
            
        except Exception as e:
            print(f"✗ 浏览器启动失败: {e}")
            return False
    
    def analyze_login_page_structure(self):
        """分析登录页面结构"""
        print("\n=== 分析登录页面结构 ===")
        
        try:
            self.driver.get(self.login_url)
            time.sleep(3)
            
            print(f"当前URL: {self.driver.current_url}")
            print(f"页面标题: {self.driver.title}")
            
            # 查找输入框
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"\n找到 {len(inputs)} 个输入元素:")
            
            for i, inp in enumerate(inputs):
                input_type = inp.get_attribute("type")
                input_name = inp.get_attribute("name")
                input_id = inp.get_attribute("id")
                input_value = inp.get_attribute("value")
                
                print(f"  {i+1}. Type: {input_type}, Name: {input_name}, ID: {input_id}, Value: {input_value}")
            
            # 查找表单
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            print(f"\n找到 {len(forms)} 个表单:")
            for i, form in enumerate(forms):
                form_action = form.get_attribute("action")
                form_method = form.get_attribute("method")
                print(f"  {i+1}. Action: {form_action}, Method: {form_method}")
            
            return True
            
        except Exception as e:
            print(f"✗ 页面结构分析失败: {e}")
            return False
    
    def test_manual_login(self):
        """测试手动登录"""
        print("\n=== 手动登录测试 ===")
        print("请在浏览器中手动输入用户名和密码进行登录")
        print("登录成功后，按回车键继续...")
        
        try:
            input()  # 等待用户操作
            
            current_url = self.driver.current_url
            print(f"登录后URL: {current_url}")
            
            if "Login.aspx" not in current_url:
                print("✓ 登录成功，已跳转到其他页面")
                
                # 检查是否有用户信息
                try:
                    user_info = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Welcome') or contains(text(), 'Hello') or contains(text(), 'User')]")
                    print(f"✓ 发现用户信息: {user_info.text}")
                except:
                    print("未发现明显的用户信息元素")
                
                return True
            else:
                print("✗ 仍在登录页面，可能登录失败")
                return False
                
        except Exception as e:
            print(f"✗ 登录测试失败: {e}")
            return False
    
    def test_search_results_page(self):
        """测试搜索结果页面"""
        print("\n=== 测试搜索结果页面 ===")
        
        try:
            self.driver.get(self.search_url)
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"搜索结果页URL: {current_url}")
            print(f"页面标题: {self.driver.title}")
            
            # 查找表格
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"\n找到 {len(tables)} 个表格:")
            for i, table in enumerate(tables):
                table_id = table.get_attribute("id")
                table_class = table.get_attribute("class")
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"  {i+1}. ID: {table_id}, Class: {table_class}, 行数: {len(rows)}")
            
            # 查找复选框
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            print(f"\n找到 {len(checkboxes)} 个复选框:")
            for i, cb in enumerate(checkboxes[:5]):  # 只显示前5个
                cb_id = cb.get_attribute("id")
                cb_name = cb.get_attribute("name")
                print(f"  {i+1}. ID: {cb_id}, Name: {cb_name}")
            
            # 查找按钮
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button'], button")
            print(f"\n找到 {len(buttons)} 个按钮:")
            for i, btn in enumerate(buttons):
                btn_id = btn.get_attribute("id")
                btn_value = btn.get_attribute("value")
                btn_text = btn.text
                print(f"  {i+1}. ID: {btn_id}, Value: {btn_value}, Text: {btn_text}")
            
            return True
            
        except Exception as e:
            print(f"✗ 搜索结果页面测试失败: {e}")
            return False
    
    def generate_selector_config(self):
        """生成选择器配置建议"""
        print("\n=== 生成选择器配置建议 ===")
        
        try:
            # 回到登录页面分析
            self.driver.get(self.login_url)
            time.sleep(2)
            
            config_suggestions = {}
            
            # 用户名输入框
            username_candidates = [
                "input[type='text']",
                "input[name*='user']",
                "input[name*='User']",
                "input[id*='user']",
                "input[id*='User']"
            ]
            
            for selector in username_candidates:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    config_suggestions['username_input'] = f"input[name='{element.get_attribute('name')}']"
                    break
                except:
                    continue
            
            # 密码输入框
            try:
                password_element = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                config_suggestions['password_input'] = f"input[name='{password_element.get_attribute('name')}']"
            except:
                config_suggestions['password_input'] = "input[type='password']"
            
            # 登录按钮
            login_button_candidates = [
                "input[type='submit']",
                "input[value*='Login']",
                "input[value*='Sign']",
                "button[type='submit']"
            ]
            
            for selector in login_button_candidates:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    config_suggestions['login_button'] = f"input[name='{element.get_attribute('name')}']"
                    break
                except:
                    continue
            
            print("建议的选择器配置:")
            for key, value in config_suggestions.items():
                print(f"    '{key}': '{value}',")
            
            return config_suggestions
            
        except Exception as e:
            print(f"✗ 配置生成失败: {e}")
            return {}
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
    
    def run_all_tests(self):
        """运行所有测试"""
        print("ComBase网站访问测试")
        print("=" * 50)
        
        tests = [
            ("网络连接", self.test_basic_connectivity),
            ("登录页面", self.test_login_page),
            ("浏览器设置", self.setup_browser),
            ("登录页面结构", self.analyze_login_page_structure),
            ("手动登录", self.test_manual_login),
            ("搜索结果页面", self.test_search_results_page),
            ("生成配置", self.generate_selector_config)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} 测试出错: {e}")
                results[test_name] = False
        
        print("\n" + "=" * 50)
        print("测试结果汇总:")
        for test_name, result in results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"  {test_name}: {status}")
        
        return results

def main():
    """主函数"""
    tester = ComBaseWebsiteTest()
    
    try:
        results = tester.run_all_tests()
        
        print("\n" + "=" * 50)
        print("测试完成！")
        
        if all(results.values()):
            print("🎉 所有测试通过，网站访问正常！")
        else:
            print("⚠️ 部分测试失败，请检查网络连接或网站状态")
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中出错: {e}")
    finally:
        print("\n按回车键关闭浏览器...")
        input()
        tester.close()

if __name__ == "__main__":
    main()
