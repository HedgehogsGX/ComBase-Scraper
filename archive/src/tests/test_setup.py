#!/usr/bin/env python3
"""
测试脚本 - 验证环境配置和基本功能
"""
import sys
import importlib
from pathlib import Path

def test_imports():
    """测试所有必需的包是否可以导入"""
    required_packages = [
        'selenium',
        'pandas',
        'openpyxl',
        'requests',
        'sqlalchemy',
        'tqdm',
        'webdriver_manager',
        'retry'
    ]
    
    print("测试包导入...")
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}")
        except ImportError as e:
            print(f"✗ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n缺少以下包，请运行: pip install {' '.join(failed_imports)}")
        return False
    
    print("所有包导入成功！")
    return True

def test_directories():
    """测试目录创建"""
    print("\n测试目录创建...")
    
    from config import DOWNLOAD_DIR, DATA_DIR, LOG_DIR
    
    directories = [DOWNLOAD_DIR, DATA_DIR, LOG_DIR]
    
    for directory in directories:
        try:
            directory.mkdir(exist_ok=True)
            print(f"✓ {directory}")
        except Exception as e:
            print(f"✗ {directory}: {e}")
            return False
    
    print("所有目录创建成功！")
    return True

def test_database():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    
    try:
        from src.core.database import DatabaseManager
        db = DatabaseManager()
        print("✓ 数据库连接成功")
        
        # 测试表创建
        total_records = db.get_total_records()
        print(f"✓ 当前记录数: {total_records}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False

def test_browser_setup():
    """测试浏览器设置（不启动浏览器）"""
    print("\n测试浏览器配置...")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        
        # 下载ChromeDriver
        driver_path = ChromeDriverManager().install()
        print(f"✓ ChromeDriver路径: {driver_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ 浏览器配置失败: {e}")
        print("请确保已安装Chrome浏览器")
        return False

def test_data_processor():
    """测试数据处理器"""
    print("\n测试数据处理器...")
    
    try:
        from src.core.data_processor import DataProcessor
        processor = DataProcessor()
        
        stats = processor.get_statistics()
        print(f"✓ 数据处理器初始化成功")
        print(f"  当前记录数: {stats['total_records']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据处理器测试失败: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("\n测试配置...")
    
    try:
        import config
        
        required_configs = [
            'BASE_URL', 'TOTAL_PAGES', 'DOWNLOAD_DIR', 
            'DATA_DIR', 'LOG_DIR', 'SELECTORS'
        ]
        
        for config_name in required_configs:
            if hasattr(config, config_name):
                print(f"✓ {config_name}: {getattr(config, config_name)}")
            else:
                print(f"✗ 缺少配置: {config_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("ComBase爬虫环境测试")
    print("=" * 50)
    
    tests = [
        ("包导入", test_imports),
        ("目录创建", test_directories),
        ("配置文件", test_config),
        ("数据库", test_database),
        ("数据处理器", test_data_processor),
        ("浏览器配置", test_browser_setup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试出错: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！环境配置正确。")
        print("\n可以开始使用爬虫:")
        print("  python run.py")
        print("  或")
        print("  python scraper.py")
    else:
        print("⚠️  部分测试失败，请检查配置。")
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
