#!/usr/bin/env python3
"""
ComBase智能爬虫 - 解决跳转缓慢问题
特性:
1. 连续爬取，避免重新跳转
2. 智能暂停/继续功能  
3. 分段保存，避免数据丢失
4. 快速恢复机制
"""

import os
import time
import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

@dataclass
class TimeSeriesData:
    """时间序列数据"""
    time_hours: List[float]
    values: List[float]

@dataclass
class CompleteComBaseRecord:
    """完整的ComBase记录数据结构"""
    record_id: str
    organism: str
    food: str
    temperature: str
    aw: str
    ph: str
    page_number: int
    logc_series: Optional[TimeSeriesData] = None
    
    def to_flat_dict(self) -> Dict:
        """转换为扁平字典，用于CSV输出"""
        flat_data = {
            'record_id': self.record_id,
            'organism': self.organism,
            'food': self.food,
            'temperature': self.temperature,
            'aw': self.aw,
            'ph': self.ph,
            'page_number': self.page_number
        }
        
        if self.logc_series:
            flat_data['logc_points'] = len(self.logc_series.time_hours)
            flat_data['logc_duration'] = max(self.logc_series.time_hours) if self.logc_series.time_hours else 0
            flat_data['logc_initial'] = self.logc_series.values[0] if self.logc_series.values else None
            flat_data['logc_final'] = self.logc_series.values[-1] if self.logc_series.values else None
            flat_data['logc_series_json'] = json.dumps(list(zip(self.logc_series.time_hours, self.logc_series.values)))
        else:
            flat_data['logc_points'] = 0
            flat_data['logc_duration'] = 0
            flat_data['logc_initial'] = None
            flat_data['logc_final'] = None
            flat_data['logc_series_json'] = None
        
        return flat_data

class ComBaseSmartScraper:
    """ComBase智能爬虫"""
    
    def __init__(self, output_dir: str = "data", segment_size: int = 50):
        """初始化爬虫"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.segment_size = segment_size  # 每段保存的页数
        self.driver = None
        self.wait = None
        
        # 状态控制
        self.is_paused = False
        self.should_stop = False
        
        # 进度文件
        self.progress_file = self.output_dir / "smart_scraping_progress.json"
        self.progress = self.load_progress()
        
        # 设置日志
        self.setup_logging()
        
        # ComBase配置
        self.login_url = "https://combasebrowser.errc.ars.usda.gov/membership/Login.aspx"
        self.search_url = "https://combasebrowser.errc.ars.usda.gov/SearchResults.aspx"
        
        # 统计信息
        self.total_pages = 6075
        self.current_segment = 0
        self.segment_records = []
        
    def setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"smart_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_progress(self) -> Dict:
        """加载进度"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "start_time": datetime.now().isoformat(),
            "current_page": 1,
            "completed_segments": [],
            "total_records": 0,
            "last_segment": 0,
            "status": "ready"  # ready, running, paused, completed
        }
    
    def save_progress(self):
        """保存进度"""
        self.progress["last_update"] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def setup_driver(self):
        """设置Chrome浏览器"""
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1400,1000")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.logger.info("浏览器初始化完成")
        
    def login(self, username: str, password: str) -> bool:
        """登录ComBase系统"""
        try:
            self.logger.info("开始登录")
            self.driver.get(self.login_url)
            time.sleep(3)
            
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='Login1$UserName']"))
            )
            username_input.clear()
            username_input.send_keys(username)
            
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='Login1$Password']")
            password_input.clear()
            password_input.send_keys(password)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "input[name='Login1$Button1']")
            login_button.click()
            time.sleep(5)
            
            if "Login.aspx" not in self.driver.current_url:
                self.logger.info("登录成功")
                return True
            else:
                self.logger.error("登录失败")
                return False
                
        except Exception as e:
            self.logger.error(f"登录出错: {e}")
            return False
            
    def navigate_to_search_results(self) -> bool:
        """导航到搜索结果页面"""
        try:
            self.logger.info("导航到搜索结果页面")
            self.driver.get(self.search_url)
            time.sleep(5)
            
            if "SearchResults.aspx" in self.driver.current_url:
                self.logger.info("搜索结果页面加载成功")
                return True
            else:
                self.logger.error("搜索结果页面加载失败")
                return False
                
        except Exception as e:
            self.logger.error(f"导航失败: {e}")
            return False
    
    def go_to_next_page(self) -> bool:
        """跳转到下一页"""
        try:
            next_link = self.driver.find_element(By.XPATH, "//div[@class='cbpagination']//a[@data-action='next']")
            if next_link and 'disabled' not in next_link.get_attribute('class'):
                next_link.click()
                time.sleep(1.5)  # 减少等待时间
                
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.exportchk")))
                    return True
                except:
                    return False
            return False
        except Exception as e:
            self.logger.debug(f"下一页跳转失败: {e}")
            return False
    
    def parse_time_series(self, value_string: str) -> Optional[TimeSeriesData]:
        """解析时间序列数据"""
        try:
            if not value_string or value_string.strip() == "":
                return None
                
            pattern = r'\[([0-9.]+),([0-9.]+)\]'
            matches = re.findall(pattern, value_string)
            
            if not matches:
                return None
                
            time_hours = []
            values = []
            
            for time_str, value_str in matches:
                time_hours.append(float(time_str))
                values.append(float(value_str))
                
            return TimeSeriesData(time_hours=time_hours, values=values)
            
        except Exception as e:
            self.logger.debug(f"解析时间序列失败: {e}")
            return None
    
    def parse_page_data(self, page_number: int) -> List[CompleteComBaseRecord]:
        """解析当前页面的数据"""
        try:
            time.sleep(1)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            records = []
            checkboxes = soup.find_all('input', {'data-recordid': True, 'class': 'exportchk'})
            
            for i, checkbox in enumerate(checkboxes):
                try:
                    record_id = checkbox.get('data-recordid')
                    record_container = checkbox.find_parent('div', class_='col-lg-9')
                    
                    if not record_container:
                        continue
                    
                    # 提取基础数据
                    organism = ""
                    food = ""
                    temperature = ""
                    aw = ""
                    ph = ""

                    # 获取记录编号
                    record_number = ""
                    record_nb_span = record_container.find('span', id=lambda x: x and 'lblRecordNb' in x)
                    if record_nb_span:
                        record_number = record_nb_span.get_text(strip=True)

                    # 获取organism和food信息
                    record_titles = record_container.find_all('span', class_='recordTitle')
                    organism_part = ""
                    food_part = ""

                    if len(record_titles) >= 2:
                        organism_part = record_titles[0].get_text(strip=True)  # Aerobic total spoilage bacteria
                        food_part = record_titles[2].get_text(strip=True) if len(record_titles) > 2 else ""  # in precooked beef

                    # 构建完整的organism名称：编号 + organism + food
                    if record_number and organism_part:
                        if food_part:
                            organism = f"{record_number} {organism_part} {food_part}"
                        else:
                            organism = f"{record_number} {organism_part}"
                    else:
                        organism = organism_part

                    # food字段保持原来的逻辑（用于向后兼容）
                    food = food_part
                    
                    temp_span = record_container.find('span', id='lblTemp')
                    if temp_span:
                        temperature = temp_span.get_text(strip=True)
                    
                    aw_span = record_container.find('span', id='lblAw')
                    if aw_span:
                        aw = aw_span.get_text(strip=True)
                    
                    ph_span = record_container.find('span', id='lblPh')
                    if ph_span:
                        ph = ph_span.get_text(strip=True)
                    
                    # 提取时间序列数据
                    logc_series = None
                    hidden_logcs = soup.find('input', {'id': f'ContentPlaceHolder1_CBListView_HiddenLogcs_{i}'})
                    if hidden_logcs:
                        logc_value = hidden_logcs.get('value', '')
                        logc_series = self.parse_time_series(logc_value)
                    
                    record = CompleteComBaseRecord(
                        record_id=record_id,
                        organism=organism,
                        food=food,
                        temperature=temperature,
                        aw=aw,
                        ph=ph,
                        page_number=page_number,
                        logc_series=logc_series
                    )
                    
                    records.append(record)
                    
                except Exception as e:
                    self.logger.debug(f"解析记录失败: {e}")
                    continue
            
            return records

        except Exception as e:
            self.logger.error(f"解析第 {page_number} 页失败: {e}")
            return []

    def save_segment_data(self, segment_number: int):
        """保存段数据"""
        if not self.segment_records:
            return False

        filename = f"combase_smart_segment_{segment_number:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 保存CSV格式
        csv_file = self.output_dir / f"{filename}.csv"
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if self.segment_records:
                    fieldnames = list(self.segment_records[0].to_flat_dict().keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for record in self.segment_records:
                        writer.writerow(record.to_flat_dict())

            print(f"✅ 段 {segment_number} 数据已保存: {csv_file.name} ({len(self.segment_records)} 条记录)")

            # 更新进度
            start_page = self.progress['current_page'] - len(self.segment_records)//10 + 1
            end_page = self.progress['current_page']

            self.progress["completed_segments"].append({
                "segment": segment_number,
                "file": csv_file.name,
                "records": len(self.segment_records),
                "pages": f"{start_page}-{end_page}"
            })
            self.progress["total_records"] += len(self.segment_records)
            self.progress["last_segment"] = segment_number

            # 清空段记录
            self.segment_records = []
            return True

        except Exception as e:
            print(f"❌ 段 {segment_number} 保存出错: {e}")
            return False

    def run_smart_scraping(self, username: str, password: str, start_page: int = None):
        """运行智能爬取"""
        print("🚀 ComBase智能爬虫启动")
        print("=" * 60)
        print("💡 特性:")
        print("  - 连续爬取，无需重新跳转")
        print("  - 分段保存，防止数据丢失")
        print("  - 支持Ctrl+C安全中断")
        print("=" * 60)

        # 确定起始页面
        if start_page is None:
            start_page = self.progress.get("current_page", 1)

        print(f"📋 从第 {start_page} 页开始爬取")
        print(f"🎯 目标: 第 {start_page} 页到第 {self.total_pages} 页")
        print(f"📦 分段大小: {self.segment_size} 页")

        start_time = datetime.now()
        self.progress["status"] = "running"
        self.progress["current_page"] = start_page

        try:
            self.setup_driver()

            if not self.login(username, password):
                return

            if not self.navigate_to_search_results():
                return

            # 如果不是从第1页开始，需要跳转
            if start_page > 1:
                print(f"🔄 跳转到第 {start_page} 页...")
                for i in range(1, start_page):
                    if not self.go_to_next_page():
                        print(f"❌ 跳转失败，停在第 {i} 页")
                        return
                    if i % 50 == 0:
                        print(f"  已跳转到第 {i} 页...")
                print(f"✅ 成功跳转到第 {start_page} 页")

            # 开始连续爬取
            current_page = start_page
            while current_page <= self.total_pages and not self.should_stop:
                try:
                    # 解析当前页面
                    page_records = self.parse_page_data(current_page)

                    if page_records:
                        self.segment_records.extend(page_records)
                        print(f"✓ 第 {current_page} 页: {len(page_records)} 条记录")
                    else:
                        print(f"✗ 第 {current_page} 页: 解析失败")

                    # 更新当前页面
                    self.progress["current_page"] = current_page

                    # 检查是否需要保存段数据
                    if len(self.segment_records) >= self.segment_size * 10:  # 每段50页 * 10条/页
                        self.current_segment += 1
                        self.save_segment_data(self.current_segment)
                        self.save_progress()

                    # 显示进度
                    if current_page % 50 == 0:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        pages_processed = current_page - start_page + 1
                        avg_time_per_page = elapsed / pages_processed
                        remaining_pages = self.total_pages - current_page
                        estimated_remaining_time = remaining_pages * avg_time_per_page

                        print(f"\n📊 进度报告 (第 {current_page} 页):")
                        print(f"总进度: {current_page}/{self.total_pages} 页 ({current_page/self.total_pages*100:.1f}%)")
                        print(f"当前段记录: {len(self.segment_records)} 条")
                        print(f"总记录: {self.progress['total_records'] + len(self.segment_records)} 条")
                        print(f"平均速度: {avg_time_per_page:.1f} 秒/页")
                        print(f"预计剩余时间: {estimated_remaining_time/3600:.1f} 小时")
                        print(f"完成段数: {len(self.progress['completed_segments'])}")
                        print("-" * 50)

                    # 跳转到下一页
                    if current_page < self.total_pages:
                        if not self.go_to_next_page():
                            print(f"❌ 第 {current_page} 页后无法继续翻页")
                            break

                    current_page += 1

                except Exception as e:
                    print(f"❌ 处理第 {current_page} 页失败: {e}")
                    current_page += 1
                    continue

            # 保存最后一段数据
            if self.segment_records:
                self.current_segment += 1
                self.save_segment_data(self.current_segment)

            # 更新最终状态
            if current_page > self.total_pages:
                self.progress["status"] = "completed"
                print("🎉 所有页面爬取完成！")
            else:
                self.progress["status"] = "paused"
                print(f"⏸️ 爬取暂停在第 {current_page} 页")

        except KeyboardInterrupt:
            print("\n⏹️ 用户中断，保存当前进度...")
            if self.segment_records:
                self.current_segment += 1
                self.save_segment_data(self.current_segment)
            self.progress["status"] = "paused"
        except Exception as e:
            print(f"\n❌ 爬取过程出错: {e}")
            self.progress["status"] = "error"
        finally:
            # 保存最终进度
            self.save_progress()

            if self.driver:
                self.driver.quit()

        # 最终统计
        total_time = (datetime.now() - start_time).total_seconds()
        print(f"\n" + "=" * 60)
        print("📊 爬取完成统计")
        print("=" * 60)
        print(f"总耗时: {total_time/3600:.1f} 小时")
        print(f"处理页面: {current_page - start_page}")
        print(f"完成段数: {len(self.progress['completed_segments'])}")
        print(f"总记录数: {self.progress['total_records']}")
        print(f"最终状态: {self.progress['status']}")


def main():
    """主函数"""
    print("🚀 ComBase智能爬虫")
    print("解决跳转缓慢问题，支持暂停/继续")
    print("=" * 60)

    try:
        # 检查是否有进度文件
        progress_file = Path("data/smart_scraping_progress.json")
        start_page = None

        if progress_file.exists():
            with open(progress_file, 'r') as f:
                progress = json.load(f)

            print(f"📋 发现进度文件:")
            print(f"当前页面: {progress.get('current_page', 1)}")
            print(f"完成段数: {len(progress.get('completed_segments', []))}")
            print(f"总记录数: {progress.get('total_records', 0)}")
            print(f"状态: {progress.get('status', 'unknown')}")

            if progress.get('status') in ['paused', 'running']:
                resume = input("\n是否从上次中断处继续? (y/n): ").strip().lower()
                if resume == 'y':
                    start_page = progress.get('current_page', 1)
                else:
                    # 清理进度文件重新开始
                    progress_file.unlink()
                    print("🗑️ 已清理进度文件，将重新开始")

        username = input("ComBase用户名: ").strip()
        password = input("ComBase密码: ").strip()

        if not username or not password:
            print("❌ 用户名和密码不能为空")
            return

        # 创建爬虫实例
        scraper = ComBaseSmartScraper(segment_size=50)  # 每段50页

        # 开始智能爬取
        scraper.run_smart_scraping(username, password, start_page)

    except KeyboardInterrupt:
        print("\n⏹️ 用户中断")
    except Exception as e:
        print(f"❌ 程序出错: {e}")


if __name__ == "__main__":
    main()
