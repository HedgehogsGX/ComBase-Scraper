#!/usr/bin/env python3
"""
测试运行器 - 统一运行所有测试
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_basic_tests():
    """运行基础测试"""
    print("🚀 开始ComBase爬虫测试")
    print("=" * 50)
    
    # 1. 网络连接测试
    print("\n1️⃣ 网络连接测试")
    print("-" * 30)
    try:
        from src.tests.simple_test import test_network
        test_network()
    except Exception as e:
        print(f"❌ 网络测试失败: {e}")
    
    # 2. 环境配置测试
    print("\n2️⃣ 环境配置测试")
    print("-" * 30)
    try:
        # 测试包导入
        required_packages = ['selenium', 'requests', 'webdriver_manager']
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ {package}")
            except ImportError:
                print(f"✗ {package} - 需要安装")
        
        # 测试ChromeDriver
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        print(f"✓ ChromeDriver: {driver_path}")
        
    except Exception as e:
        print(f"❌ 环境测试失败: {e}")
    
    # 3. 配置文件测试
    print("\n3️⃣ 配置文件测试")
    print("-" * 30)
    try:
        import config
        print(f"✓ 登录URL: {config.LOGIN_URL}")
        print(f"✓ 搜索URL: {config.SEARCH_RESULTS_URL}")
        print(f"✓ 选择器数量: {len(config.SELECTORS)}")
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")

def run_browser_test():
    """运行浏览器测试"""
    print("\n4️⃣ 浏览器访问测试")
    print("-" * 30)
    
    response = input("是否运行浏览器测试? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        try:
            from src.tests.simple_test import test_browser
            test_browser()
        except Exception as e:
            print(f"❌ 浏览器测试失败: {e}")
    else:
        print("⏭️ 跳过浏览器测试")

def run_login_test():
    """运行登录测试"""
    print("\n5️⃣ 登录功能测试")
    print("-" * 30)
    
    response = input("是否运行登录测试? (需要ComBase账号) (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        try:
            import subprocess
            subprocess.run([sys.executable, "src/tests/test_login.py"])
        except Exception as e:
            print(f"❌ 登录测试失败: {e}")
    else:
        print("⏭️ 跳过登录测试")

def show_next_steps():
    """显示下一步操作"""
    print("\n" + "=" * 50)
    print("🎯 测试完成！下一步操作:")
    print("=" * 50)
    print("1. 如果所有测试通过:")
    print("   python run.py --analyze  # 分析网站结构")
    print("   python run.py           # 开始爬取")
    print()
    print("2. 如果需要登录测试:")
    print("   python src/tests/test_login.py")
    print()
    print("3. 如果需要详细环境测试:")
    print("   python src/tests/test_setup.py")
    print()
    print("4. 查看项目文档:")
    print("   cat docs/QUICK_START.md")
    print("   cat PROJECT_STRUCTURE.md")

def main():
    """主函数"""
    try:
        # 运行基础测试
        run_basic_tests()
        
        # 运行浏览器测试
        run_browser_test()
        
        # 运行登录测试
        run_login_test()
        
        # 显示下一步
        show_next_steps()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中出错: {e}")

if __name__ == "__main__":
    main()
