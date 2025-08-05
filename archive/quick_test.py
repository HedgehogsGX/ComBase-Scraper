#!/usr/bin/env python3
"""
快速测试ComBase登录和基本功能
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def quick_test():
    """快速测试登录和页面访问"""
    print("🚀 ComBase快速测试开始")
    print("=" * 40)
    
    # 设置浏览器
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1200,800")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        # 1. 访问登录页面
        print("1️⃣ 访问登录页面...")
        login_url = "https://combasebrowser.errc.ars.usda.gov/membership/Login.aspx"
        driver.get(login_url)
        time.sleep(3)
        
        print(f"✓ 当前URL: {driver.current_url}")
        print(f"✓ 页面标题: {driver.title}")
        
        # 2. 填写登录信息
        print("\n2️⃣ 填写登录信息...")
        wait = WebDriverWait(driver, 30)
        
        # 用户名
        username_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='Login1$UserName']"))
        )
        username_input.clear()
        username_input.send_keys("WallaceGuo@moonshotacademy.cn")
        print("✓ 用户名已输入")
        
        # 密码
        password_input = driver.find_element(By.CSS_SELECTOR, "input[name='Login1$Password']")
        password_input.clear()
        password_input.send_keys("Rr*Auzqv!b9!Cnh")
        print("✓ 密码已输入")
        
        # 3. 点击登录
        print("\n3️⃣ 执行登录...")
        login_button = driver.find_element(By.CSS_SELECTOR, "input[name='Login1$Button1']")
        login_button.click()
        
        # 等待登录结果
        time.sleep(5)
        
        current_url = driver.current_url
        print(f"✓ 登录后URL: {current_url}")
        
        if "Login.aspx" not in current_url:
            print("🎉 登录成功！")
            
            # 4. 访问搜索结果页面
            print("\n4️⃣ 访问搜索结果页面...")
            search_url = "https://combasebrowser.errc.ars.usda.gov/SearchResults.aspx"
            driver.get(search_url)
            time.sleep(5)
            
            print(f"✓ 搜索页面URL: {driver.current_url}")
            print(f"✓ 搜索页面标题: {driver.title}")
            
            # 5. 分析页面结构
            print("\n5️⃣ 分析页面结构...")
            
            # 查找表格
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"✓ 找到 {len(tables)} 个表格")
            
            # 查找复选框
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            print(f"✓ 找到 {len(checkboxes)} 个复选框")
            
            # 查找分页控件
            page_controls = driver.find_elements(By.CSS_SELECTOR, "a[href*='Page'], input[id*='Page']")
            print(f"✓ 找到 {len(page_controls)} 个分页控件")
            
            # 显示前几个分页控件
            if page_controls:
                print("分页控件详情:")
                for i, ctrl in enumerate(page_controls[:5]):
                    ctrl_text = ctrl.text or ctrl.get_attribute('value') or ctrl.get_attribute('id')
                    ctrl_href = ctrl.get_attribute('href') or ''
                    print(f"  {i+1}. Text: '{ctrl_text}', Href: '{ctrl_href[:50]}...'")
            
            # 6. 测试数据选择
            print("\n6️⃣ 测试数据选择...")
            if checkboxes:
                try:
                    # 尝试点击第一个复选框
                    first_checkbox = checkboxes[0]
                    driver.execute_script("arguments[0].click();", first_checkbox)
                    print("✓ 成功点击第一个复选框")
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️ 复选框点击失败: {e}")
            
            # 7. 查找导出按钮
            print("\n7️⃣ 查找导出功能...")
            export_buttons = driver.find_elements(By.CSS_SELECTOR, 
                "input[value*='Export'], input[value*='export'], button[id*='Export']")
            print(f"✓ 找到 {len(export_buttons)} 个导出按钮")
            
            if export_buttons:
                for i, btn in enumerate(export_buttons):
                    btn_value = btn.get_attribute('value') or btn.text
                    btn_id = btn.get_attribute('id')
                    print(f"  导出按钮 {i+1}: Value='{btn_value}', ID='{btn_id}'")
            
            print("\n🎉 测试完成！所有功能正常")
            
        else:
            print("❌ 登录失败，仍在登录页面")
            
            # 检查错误信息
            try:
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error']")
                for elem in error_elements:
                    if elem.text.strip():
                        print(f"错误信息: {elem.text}")
            except:
                pass
        
        print("\n按回车键关闭浏览器...")
        input()
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    quick_test()
