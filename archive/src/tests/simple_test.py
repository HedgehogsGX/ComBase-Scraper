#!/usr/bin/env python3
"""
简化的ComBase网站测试
"""
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def test_network():
    """测试网络连接"""
    print("=== 测试网络连接 ===")
    
    urls_to_test = [
        "https://combasebrowser.errc.ars.usda.gov",
        "https://combasebrowser.errc.ars.usda.gov/Login.aspx",
        "https://google.com"  # 测试基本网络连接
    ]
    
    for url in urls_to_test:
        try:
            print(f"测试: {url}")
            response = requests.get(url, timeout=10)
            print(f"  ✓ 状态码: {response.status_code}")
            print(f"  ✓ 最终URL: {response.url}")
            print(f"  ✓ 响应时间: {response.elapsed.total_seconds():.2f}秒")
            
            if "combasebrowser" in url:
                content = response.text.lower()
                if "login" in content:
                    print("  ✓ 发现登录相关内容")
                if "username" in content or "user" in content:
                    print("  ✓ 发现用户名字段")
                if "password" in content:
                    print("  ✓ 发现密码字段")
            
            print()
            
        except requests.exceptions.Timeout:
            print(f"  ✗ 超时")
        except requests.exceptions.ConnectionError:
            print(f"  ✗ 连接失败")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        print()

def test_browser():
    """测试浏览器访问"""
    print("=== 测试浏览器访问 ===")
    
    try:
        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1200,800")
        
        # 启动浏览器
        print("启动浏览器...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✓ 浏览器启动成功")
        
        # 访问ComBase网站
        print("访问ComBase网站...")
        driver.get("https://combasebrowser.errc.ars.usda.gov")
        time.sleep(3)
        
        print(f"✓ 当前URL: {driver.current_url}")
        print(f"✓ 页面标题: {driver.title}")
        
        # 分析页面元素
        print("\n分析页面元素:")
        
        # 查找输入框
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"找到 {len(inputs)} 个输入框:")
        
        for i, inp in enumerate(inputs[:10]):  # 只显示前10个
            input_type = inp.get_attribute("type") or "text"
            input_name = inp.get_attribute("name") or ""
            input_id = inp.get_attribute("id") or ""
            
            print(f"  {i+1}. Type: {input_type}, Name: {input_name}, ID: {input_id}")
        
        # 查找按钮
        buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button'], button")
        print(f"\n找到 {len(buttons)} 个按钮:")
        
        for i, btn in enumerate(buttons[:5]):  # 只显示前5个
            btn_value = btn.get_attribute("value") or ""
            btn_text = btn.text or ""
            btn_id = btn.get_attribute("id") or ""
            
            print(f"  {i+1}. ID: {btn_id}, Value: {btn_value}, Text: {btn_text}")
        
        # 等待用户查看
        print("\n浏览器已打开ComBase网站")
        print("请查看网站是否正常显示")
        print("如果需要登录，请手动登录")
        print("完成后按回车键继续...")
        input()
        
        # 检查登录后状态
        current_url = driver.current_url
        print(f"\n当前URL: {current_url}")
        
        if "Login.aspx" not in current_url:
            print("✓ 已离开登录页面")
            
            # 尝试访问搜索结果页面
            print("尝试访问搜索结果页面...")
            driver.get("https://combasebrowser.errc.ars.usda.gov/SearchResults.aspx")
            time.sleep(3)
            
            print(f"搜索结果页URL: {driver.current_url}")
            print(f"搜索结果页标题: {driver.title}")
            
            # 查找表格和数据
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"找到 {len(tables)} 个表格")
            
            checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            print(f"找到 {len(checkboxes)} 个复选框")
            
            if len(tables) > 0 or len(checkboxes) > 0:
                print("✓ 发现数据表格或复选框，网站功能正常")
            else:
                print("⚠️ 未发现预期的数据元素")
        
        print("\n按回车键关闭浏览器...")
        input()
        driver.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 浏览器测试失败: {e}")
        return False

def main():
    """主函数"""
    print("ComBase网站简化测试")
    print("=" * 40)
    
    # 测试网络连接
    test_network()
    
    # 询问是否继续浏览器测试
    response = input("是否继续浏览器测试? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        test_browser()
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()
