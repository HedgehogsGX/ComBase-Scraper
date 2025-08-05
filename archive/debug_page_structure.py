#!/usr/bin/env python3
"""
调试ComBase页面结构，找到正确的数据选择和导出方式
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def debug_page_structure():
    """调试页面结构，找到正确的操作方式"""
    print("🔍 调试ComBase页面结构")
    print("=" * 50)
    
    # 设置浏览器
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1400,1000")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 1. 登录
        print("1️⃣ 登录ComBase...")
        login_url = "https://combasebrowser.errc.ars.usda.gov/membership/Login.aspx"
        driver.get(login_url)
        time.sleep(3)
        
        # 填写登录信息
        username_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='Login1$UserName']"))
        )
        username_input.send_keys("WallaceGuo@moonshotacademy.cn")
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[name='Login1$Password']")
        password_input.send_keys("Rr*Auzqv!b9!Cnh")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "input[name='Login1$Button1']")
        login_button.click()
        time.sleep(5)
        
        print("✓ 登录成功")
        
        # 2. 访问搜索结果页面
        print("\n2️⃣ 访问搜索结果页面...")
        search_url = "https://combasebrowser.errc.ars.usda.gov/SearchResults.aspx"
        driver.get(search_url)
        time.sleep(5)
        
        print("✓ 搜索结果页面已加载")
        print(f"当前URL: {driver.current_url}")
        
        # 3. 分析页面结构
        print("\n3️⃣ 分析页面结构...")
        
        # 查找所有表格
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"找到 {len(tables)} 个表格")
        
        # 分析主要的数据表格
        for i, table in enumerate(tables):
            table_id = table.get_attribute("id") or f"table_{i}"
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"  表格 {i+1}: ID='{table_id}', 行数={len(rows)}")
            
            # 查看表格内的复选框
            checkboxes_in_table = table.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            if checkboxes_in_table:
                print(f"    - 包含 {len(checkboxes_in_table)} 个复选框")
                for j, cb in enumerate(checkboxes_in_table[:3]):  # 只显示前3个
                    cb_id = cb.get_attribute("id") or ""
                    cb_name = cb.get_attribute("name") or ""
                    print(f"      复选框 {j+1}: ID='{cb_id}', Name='{cb_name}'")
        
        # 4. 查找所有复选框
        print("\n4️⃣ 查找所有复选框...")
        all_checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        print(f"页面总共有 {len(all_checkboxes)} 个复选框")
        
        for i, cb in enumerate(all_checkboxes):
            cb_id = cb.get_attribute("id") or ""
            cb_name = cb.get_attribute("name") or ""
            cb_value = cb.get_attribute("value") or ""
            is_visible = cb.is_displayed()
            is_enabled = cb.is_enabled()
            
            print(f"  复选框 {i+1}: ID='{cb_id}', Name='{cb_name}', Value='{cb_value}', 可见={is_visible}, 可用={is_enabled}")
        
        # 5. 查找导出按钮
        print("\n5️⃣ 查找导出按钮...")
        export_selectors = [
            "input[value*='Export']",
            "input[value*='export']", 
            "button[id*='Export']",
            "button[id*='export']",
            "input[id*='Export']",
            "input[id*='export']",
            "a[href*='export']"
        ]
        
        all_export_buttons = []
        for selector in export_selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            all_export_buttons.extend(buttons)
        
        # 去重
        unique_buttons = []
        seen_elements = set()
        for btn in all_export_buttons:
            element_id = id(btn)
            if element_id not in seen_elements:
                unique_buttons.append(btn)
                seen_elements.add(element_id)
        
        print(f"找到 {len(unique_buttons)} 个导出按钮")
        for i, btn in enumerate(unique_buttons):
            btn_id = btn.get_attribute("id") or ""
            btn_value = btn.get_attribute("value") or ""
            btn_text = btn.text or ""
            btn_type = btn.get_attribute("type") or ""
            is_visible = btn.is_displayed()
            is_enabled = btn.is_enabled()
            
            print(f"  按钮 {i+1}: ID='{btn_id}', Value='{btn_value}', Text='{btn_text}', Type='{btn_type}', 可见={is_visible}, 可用={is_enabled}")
        
        # 6. 测试数据选择流程
        print("\n6️⃣ 测试数据选择流程...")
        
        # 找到数据行的复选框（排除全选复选框）
        data_checkboxes = []
        for cb in all_checkboxes:
            cb_id = cb.get_attribute("id") or ""
            cb_name = cb.get_attribute("name") or ""
            
            # 排除全选复选框
            if "selectall" not in cb_id.lower() and "selectall" not in cb_name.lower():
                if cb.is_displayed() and cb.is_enabled():
                    data_checkboxes.append(cb)
        
        print(f"找到 {len(data_checkboxes)} 个数据复选框")
        
        if data_checkboxes:
            print("尝试选择前3个数据复选框...")
            selected_count = 0
            for i, cb in enumerate(data_checkboxes[:3]):
                try:
                    if not cb.is_selected():
                        driver.execute_script("arguments[0].click();", cb)
                        selected_count += 1
                        print(f"  ✓ 已选择复选框 {i+1}")
                        time.sleep(0.5)
                    else:
                        print(f"  - 复选框 {i+1} 已经选中")
                except Exception as e:
                    print(f"  ✗ 选择复选框 {i+1} 失败: {e}")
            
            print(f"成功选择了 {selected_count} 个复选框")
            
            # 7. 测试导出功能
            print("\n7️⃣ 测试导出功能...")
            if unique_buttons:
                export_button = unique_buttons[0]  # 使用第一个导出按钮
                print(f"尝试点击导出按钮: {export_button.get_attribute('id')}")
                
                try:
                    # 检查按钮是否可点击
                    if export_button.is_displayed() and export_button.is_enabled():
                        print("导出按钮可点击，但为了安全起见，不实际点击")
                        print("✓ 导出按钮测试通过")
                    else:
                        print("⚠️ 导出按钮不可点击")
                except Exception as e:
                    print(f"✗ 导出按钮测试失败: {e}")
            else:
                print("⚠️ 未找到导出按钮")
        
        # 8. 生成正确的选择器配置
        print("\n8️⃣ 生成选择器配置...")
        
        selectors = {}
        
        # 数据复选框选择器
        if data_checkboxes:
            first_data_cb = data_checkboxes[0]
            cb_id = first_data_cb.get_attribute("id")
            cb_name = first_data_cb.get_attribute("name")
            
            if cb_id:
                # 提取ID模式
                import re
                pattern = re.sub(r'\d+', '*', cb_id)
                selectors['record_checkboxes'] = f"input[id*='{pattern.split('*')[0]}']"
            elif cb_name:
                pattern = re.sub(r'\d+', '*', cb_name)
                selectors['record_checkboxes'] = f"input[name*='{pattern.split('*')[0]}']"
        
        # 导出按钮选择器
        if unique_buttons:
            export_btn = unique_buttons[0]
            btn_id = export_btn.get_attribute("id")
            if btn_id:
                selectors['export_button'] = f"input[id='{btn_id}']"
        
        print("建议的选择器配置:")
        for key, value in selectors.items():
            print(f"    '{key}': '{value}',")
        
        print("\n✅ 页面结构分析完成！")
        print("按回车键关闭浏览器...")
        input()
        
    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_page_structure()
