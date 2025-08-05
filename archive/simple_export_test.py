#!/usr/bin/env python3
"""
简化的导出功能测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.browser_controller import ComBaseBrowserController
import time

def test_export_functionality():
    """测试导出功能"""
    print("🧪 测试ComBase导出功能")
    print("=" * 40)
    
    browser = None
    try:
        # 1. 初始化浏览器控制器
        print("1️⃣ 初始化浏览器...")
        browser = ComBaseBrowserController()
        print("✓ 浏览器初始化成功")
        
        # 2. 登录
        print("\n2️⃣ 执行登录...")
        login_success = browser.login("WallaceGuo@moonshotacademy.cn", "Rr*Auzqv!b9!Cnh")
        if not login_success:
            print("❌ 登录失败")
            return False
        print("✓ 登录成功")
        
        # 3. 导航到搜索结果页面
        print("\n3️⃣ 导航到搜索结果页面...")
        nav_success = browser.navigate_to_search_results()
        if not nav_success:
            print("❌ 导航失败")
            return False
        print("✓ 导航成功")
        
        # 4. 测试数据选择
        print("\n4️⃣ 测试数据选择...")
        select_success = browser.select_all_records()
        if not select_success:
            print("❌ 数据选择失败")
            return False
        print("✓ 数据选择成功")
        
        # 5. 测试导出功能
        print("\n5️⃣ 测试导出功能...")
        export_success = browser.export_data()
        if not export_success:
            print("❌ 导出失败")
            return False
        print("✓ 导出成功")
        
        print("\n🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False
    finally:
        if browser:
            print("\n清理资源...")
            browser.close()

if __name__ == "__main__":
    success = test_export_functionality()
    if success:
        print("\n✅ 导出功能测试完全成功！")
        print("修复后的代码可以正确选择数据并导出")
    else:
        print("\n❌ 导出功能测试失败")
        print("需要进一步调试")
