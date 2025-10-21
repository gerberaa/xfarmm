#!/usr/bin/env python3
"""
Advanced Console Menu for Twitter/X Automation System

Complete management interface for accounts, tasks, proxies, and automation.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API
from twitter_automation import TwitterAutomation
from telegram_bot import TwitterTelegramBot, TwitterBotConfig


class Colors:
    """Console colors for better UX."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    """Print colored header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
    print(f"{text.center(60)}")
    print(f"{'='*60}{Colors.END}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.END}")


def clear_screen():
    """Clear console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def load_env_file(file_path: str = "config.env"):
    """Load environment variables from file."""
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


class TaskManager:
    """Manages automation tasks (posts to process)."""
    
    def __init__(self):
        self.tasks_file = "tasks.json"
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from file."""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = []
        else:
            self.tasks = []
    
    def save_tasks(self):
        """Save tasks to file."""
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False, default=str)
    
    def add_task(self, url: str, likes: int = 0, retweets: int = 0, views: int = 0, 
                 scheduled_time: str = None, priority: str = "normal"):
        """Add a new task."""
        task = {
            "id": len(self.tasks) + 1,
            "url": url,
            "likes": likes,
            "retweets": retweets,
            "views": views,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "scheduled_time": scheduled_time,
            "processed_at": None,
            "result": None
        }
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def get_pending_tasks(self):
        """Get all pending tasks."""
        return [task for task in self.tasks if task["status"] == "pending"]
    
    def get_task_by_id(self, task_id: int):
        """Get task by ID."""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None
    
    def update_task_status(self, task_id: int, status: str, result: dict = None):
        """Update task status."""
        task = self.get_task_by_id(task_id)
        if task:
            task["status"] = status
            task["result"] = result
            if status == "completed":
                task["processed_at"] = datetime.now().isoformat()
            self.save_tasks()


class ProxyManager:
    """Manages proxy settings for accounts."""
    
    def __init__(self):
        self.proxies_file = "proxies.json"
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxy assignments from file."""
        if os.path.exists(self.proxies_file):
            try:
                with open(self.proxies_file, 'r', encoding='utf-8') as f:
                    self.proxies = json.load(f)
            except:
                self.proxies = {}
        else:
            self.proxies = {}
    
    def save_proxies(self):
        """Save proxy assignments to file."""
        with open(self.proxies_file, 'w', encoding='utf-8') as f:
            json.dump(self.proxies, f, indent=2, ensure_ascii=False)
    
    def assign_proxy(self, username: str, proxy: str):
        """Assign proxy to account."""
        self.proxies[username] = proxy
        self.save_proxies()
    
    def get_proxy(self, username: str):
        """Get proxy for account."""
        return self.proxies.get(username, None)
    
    def remove_proxy(self, username: str):
        """Remove proxy assignment."""
        if username in self.proxies:
            del self.proxies[username]
            self.save_proxies()
    
    async def test_proxy(self, proxy: str) -> dict:
        """Test a single proxy connection."""
        import httpx
        
        try:
            # Переконуємося що проксі має правильний формат
            if not proxy.startswith(('http://', 'https://', 'socks5://')):
                proxy = 'http://' + proxy
            
            # Використовуємо інший сервіс для тестування, так як httpbin.org може блокувати проксі
            test_urls = [
                "http://ip-api.com/json/",
                "https://api.ipify.org?format=json",
                "http://httpbin.org/ip"
            ]
            
            async with httpx.AsyncClient(proxy=proxy, timeout=15.0) as client:
                for url in test_urls:
                    try:
                        response = await client.get(url)
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                # Різні сервіси повертають IP в різних полях
                                ip = data.get('query') or data.get('ip') or data.get('origin', 'Unknown')
                                return {
                                    "success": True,
                                    "ip": ip,
                                    "service": url.split('/')[2],
                                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
                                }
                            except:
                                # Якщо не JSON, але код 200
                                return {
                                    "success": True,
                                    "ip": "Connected",
                                    "service": url.split('/')[2],
                                    "response_time": 0
                                }
                    except:
                        continue  # Пробуємо наступний URL
                
                return {
                    "success": False,
                    "error": "All test services failed"
                }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class AdvancedTwitterManager:
    """Advanced management system for Twitter automation."""
    
    def __init__(self):
        self.api = API()
        self.fast_mode = True  # За замовчуванням використовуємо швидкий режим
        self.automation = TwitterAutomation(self.api, fast_mode=self.fast_mode)
        self.task_manager = TaskManager()
        self.proxy_manager = ProxyManager()
        load_env_file()
    
    def main_menu(self):
        """Display main menu."""
        while True:
            clear_screen()
            print_header("🚀 ADVANCED TWITTER/X AUTOMATION SYSTEM")
            
            print(f"{Colors.BOLD}📋 ГОЛОВНЕ МЕНЮ:{Colors.END}")
            print(f"{Colors.CYAN}1.{Colors.END} 👥 Управління акаунтами")
            print(f"{Colors.CYAN}2.{Colors.END} 🎯 Управління завданнями (постами)")
            print(f"{Colors.CYAN}3.{Colors.END} 🌐 Управління проксі")
            print(f"{Colors.CYAN}4.{Colors.END} 🤖 Telegram бот")
            print(f"{Colors.CYAN}5.{Colors.END} ⚡ Швидка обробка посту")
            print(f"{Colors.CYAN}6.{Colors.END} 📊 Статистика та моніторинг")
            print(f"{Colors.CYAN}7.{Colors.END} ⚙️ Налаштування системи")
            print(f"{Colors.CYAN}8.{Colors.END} 🧪 Тестування")
            print(f"{Colors.CYAN}9.{Colors.END} ❌ Вихід")
            
            choice = input(f"\n{Colors.YELLOW}Оберіть опцію (1-9): {Colors.END}").strip()
            
            if choice == "1":
                self.accounts_menu()
            elif choice == "2":
                self.tasks_menu()
            elif choice == "3":
                self.proxy_menu()
            elif choice == "4":
                self.telegram_menu()
            elif choice == "5":
                asyncio.run(self.quick_process())
            elif choice == "6":
                asyncio.run(self.statistics_menu())
            elif choice == "7":
                self.settings_menu()
            elif choice == "8":
                asyncio.run(self.testing_menu())
            elif choice == "9":
                print_success("До побачення!")
                break
            else:
                print_error("Невірний вибір. Спробуйте ще раз.")
                input("Натисніть Enter для продовження...")
    
    def accounts_menu(self):
        """Account management menu."""
        while True:
            clear_screen()
            print_header("👥 УПРАВЛІННЯ АКАУНТАМИ")
            
            print(f"{Colors.BOLD}📋 ОПЦІЇ АКАУНТІВ:{Colors.END}")
            print(f"{Colors.CYAN}1.{Colors.END} 📂 Завантажити акаунти з файлу")
            print(f"{Colors.CYAN}2.{Colors.END} ✅ Додати акаунти зі скрипта (вбудовані)")
            print(f"{Colors.CYAN}3.{Colors.END} ➕ Додати акаунт вручну")
            print(f"{Colors.CYAN}4.{Colors.END} 📊 Показати статус акаунтів")
            print(f"{Colors.CYAN}5.{Colors.END} 🔄 Залогінити всі акаунти")
            print(f"{Colors.CYAN}6.{Colors.END} 🔓 Скинути блокування")
            print(f"{Colors.CYAN}7.{Colors.END} 🗑️ Видалити неактивні акаунти")
            print(f"{Colors.CYAN}8.{Colors.END} 🔙 Назад до головного меню")
            
            choice = input(f"\n{Colors.YELLOW}Оберіть опцію (1-8): {Colors.END}").strip()
            
            if choice == "1":
                asyncio.run(self.load_accounts_from_file())
            elif choice == "2":
                asyncio.run(self.add_builtin_accounts())
            elif choice == "3":
                asyncio.run(self.add_account_manually())
            elif choice == "4":
                asyncio.run(self.show_accounts_status())
            elif choice == "5":
                asyncio.run(self.login_all_accounts())
            elif choice == "6":
                asyncio.run(self.reset_locks())
            elif choice == "7":
                asyncio.run(self.delete_inactive())
            elif choice == "8":
                break
            else:
                print_error("Невірний вибір.")
                input("Натисніть Enter для продовження...")
    
    async def load_accounts_from_file(self):
        """Load accounts from file."""
        print_header("📂 ЗАВАНТАЖЕННЯ АКАУНТІВ З ФАЙЛУ")
        
        print("Підтримувані формати файлів:")
        print("• TXT файл з форматом: username:password:email:auth_token:ct0:proxy")
        print("• JSON файл з масивом об'єктів")
        print("• CSV файл з заголовками")
        print()
        
        file_path = input("📁 Шлях до файлу з акаунтами: ").strip()
        
        if not os.path.exists(file_path):
            print_error("Файл не знайдено!")
            input("Натисніть Enter для продовження...")
            return
        
        try:
            if file_path.endswith('.txt'):
                await self.load_accounts_from_txt(file_path)
            elif file_path.endswith('.json'):
                await self.load_accounts_from_json(file_path)
            elif file_path.endswith('.csv'):
                await self.load_accounts_from_csv(file_path)
            else:
                print_error("Непідтримуваний формат файлу!")
        
        except Exception as e:
            print_error(f"Помилка завантаження: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def load_accounts_from_txt(self, file_path: str):
        """Load accounts from TXT file."""
        success_count = 0
        failed_count = 0
        
        print("📋 Формат TXT файлу:")
        print("username:password:email:auth_token:ct0:proxy")
        print("Проксі є опційним (можна залишити порожнім)")
        print()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(':')
                if len(parts) < 5:
                    print_error(f"Рядок {line_num}: Недостатньо даних")
                    failed_count += 1
                    continue
                
                username = parts[0].strip()
                password = parts[1].strip()
                email = parts[2].strip()
                auth_token = parts[3].strip()
                ct0 = parts[4].strip()
                proxy = parts[5].strip() if len(parts) > 5 else ""
                
                try:
                    # Build cookies
                    cookies = f"auth_token={auth_token}; ct0={ct0}"
                    
                    # Add account
                    await self.api.pool.add_account(
                        username=username,
                        password=password,
                        email=email,
                        email_password="dummy_pass",
                        cookies=cookies,
                        proxy=proxy if proxy else None
                    )
                    
                    # Assign proxy if provided
                    if proxy:
                        self.proxy_manager.assign_proxy(username, proxy)
                    
                    print_success(f"Додано: @{username}")
                    success_count += 1
                    
                except Exception as e:
                    print_error(f"Помилка додавання @{username}: {e}")
                    failed_count += 1
        
        print(f"\n📊 Результат:")
        print_success(f"Успішно додано: {success_count}")
        if failed_count > 0:
            print_error(f"Помилки: {failed_count}")
    
    async def load_accounts_from_json(self, file_path: str):
        """Load accounts from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            accounts_data = json.load(f)
        
        success_count = 0
        failed_count = 0
        
        for account in accounts_data:
            try:
                username = account.get('username') or account.get('login')
                password = account.get('password')
                email = account.get('email') or account.get('mail')
                auth_token = account.get('auth_token')
                ct0 = account.get('ct0')
                proxy = account.get('proxy', '')
                
                if not all([username, password, email, auth_token, ct0]):
                    print_error(f"Неповні дані для @{username}")
                    failed_count += 1
                    continue
                
                cookies = f"auth_token={auth_token}; ct0={ct0}"
                
                await self.api.pool.add_account(
                    username=username,
                    password=password,
                    email=email,
                    email_password="dummy_pass",
                    cookies=cookies,
                    proxy=proxy if proxy else None
                )
                
                if proxy:
                    self.proxy_manager.assign_proxy(username, proxy)
                
                print_success(f"Додано: @{username}")
                success_count += 1
                
            except Exception as e:
                print_error(f"Помилка: {e}")
                failed_count += 1
        
        print(f"\n📊 Результат:")
        print_success(f"Успішно додано: {success_count}")
        if failed_count > 0:
            print_error(f"Помилки: {failed_count}")
    
    async def add_builtin_accounts(self):
        """Add built-in accounts from the original script."""
        from setup_accounts_bulk import add_all_accounts
        await add_all_accounts()
        input("Натисніть Enter для продовження...")
    
    async def add_account_manually(self):
        """Add account manually."""
        print_header("➕ ДОДАВАННЯ АКАУНТА ВРУЧНУ")
        
        username = input("👤 Username (без @): ").strip()
        password = input("🔑 Password: ").strip()
        email = input("📧 Email: ").strip()
        auth_token = input("🔐 Auth Token: ").strip()
        ct0 = input("🍪 CT0 Token: ").strip()
        proxy = input("🌐 Proxy (опційно, формат http://user:pass@host:port): ").strip()
        
        if not all([username, password, email, auth_token, ct0]):
            print_error("Всі поля обов'язкові (крім проксі)!")
            input("Натисніть Enter для продовження...")
            return
        
        try:
            cookies = f"auth_token={auth_token}; ct0={ct0}"
            
            await self.api.pool.add_account(
                username=username,
                password=password,
                email=email,
                email_password="dummy_pass",
                cookies=cookies,
                proxy=proxy if proxy else None
            )
            
            if proxy:
                self.proxy_manager.assign_proxy(username, proxy)
            
            print_success(f"Акаунт @{username} додано успішно!")
            
        except Exception as e:
            print_error(f"Помилка додавання акаунта: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def show_accounts_status(self):
        """Show accounts status with proxy info."""
        print_header("📊 СТАТУС АКАУНТІВ")
        
        try:
            accounts_info = await self.api.pool.accounts_info()
            
            if not accounts_info:
                print_warning("Акаунти не знайдені.")
                input("Натисніть Enter для продовження...")
                return
            
            active_count = sum(1 for acc in accounts_info if acc["active"])
            
            print(f"📈 Загальна статистика:")
            print(f"• Всього акаунтів: {len(accounts_info)}")
            print(f"• 🟢 Активні: {active_count}")
            print(f"• 🔴 Неактивні: {len(accounts_info) - active_count}")
            print()
            
            print(f"{'Акаунт':<20} {'Статус':<12} {'Запити':<8} {'Проксі':<20} {'Останнє використання'}")
            print("-" * 80)
            
            for info in accounts_info:
                username = info["username"]
                status = "🟢 Активний" if info["active"] else "🔴 Неактивний"
                requests = info["total_req"]
                proxy = self.proxy_manager.get_proxy(username)
                proxy_display = proxy[:20] + "..." if proxy and len(proxy) > 20 else proxy or "Без проксі"
                last_used = info["last_used"].strftime("%Y-%m-%d %H:%M") if info["last_used"] else "Ніколи"
                
                print(f"@{username:<19} {status:<12} {requests:<8} {proxy_display:<20} {last_used}")
            
        except Exception as e:
            print_error(f"Помилка отримання статусу: {e}")
        
        input("\nНатисніть Enter для продовження...")
    
    async def login_all_accounts(self):
        """Login all accounts."""
        print_header("🔄 ЛОГІН ВСІХ АКАУНТІВ")
        
        try:
            print("⏳ Логінимо всі акаунти...")
            result = await self.api.pool.login_all()
            
            print_success(f"Успішно залогінено: {result['success']}")
            if result['failed'] > 0:
                print_error(f"Помилки логіну: {result['failed']}")
            
        except Exception as e:
            print_error(f"Помилка логіну: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def reset_locks(self):
        """Reset account locks."""
        print_header("🔓 СКИДАННЯ БЛОКУВАНЬ")
        
        try:
            await self.api.pool.reset_locks()
            print_success("Всі блокування акаунтів скинуто!")
        except Exception as e:
            print_error(f"Помилка скидання блокувань: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def delete_inactive(self):
        """Delete inactive accounts."""
        print_header("🗑️ ВИДАЛЕННЯ НЕАКТИВНИХ АКАУНТІВ")
        
        confirm = input("⚠️ Ви впевнені? Це видалить всі неактивні акаунти! (y/N): ").strip().lower()
        
        if confirm == 'y':
            try:
                await self.api.pool.delete_inactive()
                print_success("Неактивні акаунти видалено!")
            except Exception as e:
                print_error(f"Помилка видалення: {e}")
        else:
            print_info("Операцію скасовано.")
        
        input("Натисніть Enter для продовження...")
    
    def tasks_menu(self):
        """Tasks management menu."""
        while True:
            clear_screen()
            print_header("🎯 УПРАВЛІННЯ ЗАВДАННЯМИ (ПОСТАМИ)")
            
            pending_tasks = self.task_manager.get_pending_tasks()
            completed_tasks = [t for t in self.task_manager.tasks if t["status"] == "completed"]
            
            print(f"{Colors.BOLD}📊 Статистика завдань:{Colors.END}")
            print(f"• 📝 Очікують: {len(pending_tasks)}")
            print(f"• ✅ Виконано: {len(completed_tasks)}")
            print(f"• 📋 Всього: {len(self.task_manager.tasks)}")
            print()
            
            print(f"{Colors.BOLD}📋 ОПЦІЇ ЗАВДАНЬ:{Colors.END}")
            print(f"{Colors.CYAN}1.{Colors.END} ➕ Додати нове завдання")
            print(f"{Colors.CYAN}2.{Colors.END} 📊 Показати всі завдання")
            print(f"{Colors.CYAN}3.{Colors.END} 📝 Показати очікувані завдання")
            print(f"{Colors.CYAN}4.{Colors.END} ▶️ Виконати завдання")
            print(f"{Colors.CYAN}5.{Colors.END} ⚡ Виконати всі очікувані")
            print(f"{Colors.CYAN}6.{Colors.END} 🗑️ Видалити завдання")
            print(f"{Colors.CYAN}7.{Colors.END} 📂 Завантажити завдання з файлу")
            print(f"{Colors.CYAN}8.{Colors.END} 💾 Експортувати результати")
            print(f"{Colors.CYAN}9.{Colors.END} 🔙 Назад до головного меню")
            
            choice = input(f"\n{Colors.YELLOW}Оберіть опцію (1-9): {Colors.END}").strip()
            
            if choice == "1":
                self.add_task()
            elif choice == "2":
                self.show_all_tasks()
            elif choice == "3":
                self.show_pending_tasks()
            elif choice == "4":
                asyncio.run(self.execute_task())
            elif choice == "5":
                asyncio.run(self.execute_all_tasks())
            elif choice == "6":
                self.delete_task()
            elif choice == "7":
                self.load_tasks_from_file()
            elif choice == "8":
                self.export_results()
            elif choice == "9":
                break
            else:
                print_error("Невірний вибір.")
                input("Натисніть Enter для продовження...")
    
    def add_task(self):
        """Add new task."""
        print_header("➕ ДОДАВАННЯ НОВОГО ЗАВДАННЯ")
        
        url = input("🔗 URL посту (Twitter/X): ").strip()
        if not url:
            print_error("URL не може бути порожнім!")
            input("Натисніть Enter для продовження...")
            return
        
        print("\n🎛️ Налаштування взаємодії:")
        print("💡 Залишіть порожнім для автоматичного вибору")
        
        likes_input = input("❤️ Кількість лайків (auto): ").strip()
        retweets_input = input("🔄 Кількість ретвітів (auto): ").strip()
        views_input = input("👀 Кількість переглядів (auto): ").strip()
        
        likes = int(likes_input) if likes_input.isdigit() else 0
        retweets = int(retweets_input) if retweets_input.isdigit() else 0
        views = int(views_input) if views_input.isdigit() else 0
        
        print("\n⚡ Пріоритет завдання:")
        print("1. Низький")
        print("2. Нормальний") 
        print("3. Високий")
        print("4. Критичний")
        
        priority_choice = input("Оберіть пріоритет (1-4, default 2): ").strip()
        priority_map = {"1": "low", "2": "normal", "3": "high", "4": "critical"}
        priority = priority_map.get(priority_choice, "normal")
        
        task = self.task_manager.add_task(
            url=url,
            likes=likes,
            retweets=retweets,
            views=views,
            priority=priority
        )
        
        print_success(f"Завдання #{task['id']} додано успішно!")
        print(f"📝 URL: {url}")
        print(f"❤️ Лайки: {likes if likes > 0 else 'авто'}")
        print(f"🔄 Ретвіти: {retweets if retweets > 0 else 'авто'}")
        print(f"👀 Перегляди: {views if views > 0 else 'авто'}")
        print(f"⚡ Пріоритет: {priority}")
        
        input("Натисніть Enter для продовження...")
    
    def show_all_tasks(self):
        """Show all tasks."""
        print_header("📊 ВСІ ЗАВДАННЯ")
        
        if not self.task_manager.tasks:
            print_warning("Завдання не знайдені.")
            input("Натисніть Enter для продовження...")
            return
        
        print(f"{'ID':<4} {'Статус':<12} {'URL':<40} {'L/R/V':<12} {'Пріоритет':<10} {'Створено'}")
        print("-" * 100)
        
        for task in self.task_manager.tasks:
            url_short = task["url"][:37] + "..." if len(task["url"]) > 40 else task["url"]
            lrv = f"{task['likes']}/{task['retweets']}/{task['views']}"
            created = datetime.fromisoformat(task["created_at"]).strftime("%Y-%m-%d %H:%M")
            
            status_color = Colors.GREEN if task["status"] == "completed" else Colors.YELLOW if task["status"] == "pending" else Colors.RED
            status_display = f"{status_color}{task['status']}{Colors.END}"
            
            print(f"{task['id']:<4} {status_display:<12} {url_short:<40} {lrv:<12} {task['priority']:<10} {created}")
        
        input("\nНатисніть Enter для продовження...")
    
    def show_pending_tasks(self):
        """Show pending tasks."""
        pending_tasks = self.task_manager.get_pending_tasks()
        
        print_header("📝 ОЧІКУВАНІ ЗАВДАННЯ")
        
        if not pending_tasks:
            print_warning("Очікуваних завдань немає.")
            input("Натисніть Enter для продовження...")
            return
        
        for i, task in enumerate(pending_tasks, 1):
            print(f"{Colors.CYAN}{i}. Завдання #{task['id']}{Colors.END}")
            print(f"   🔗 URL: {task['url']}")
            print(f"   ❤️ Лайки: {task['likes'] if task['likes'] > 0 else 'авто'}")
            print(f"   🔄 Ретвіти: {task['retweets'] if task['retweets'] > 0 else 'авто'}")
            print(f"   👀 Перегляди: {task['views'] if task['views'] > 0 else 'авто'}")
            print(f"   ⚡ Пріоритет: {task['priority']}")
            print()
        
        input("Натисніть Enter для продовження...")
    
    async def execute_task(self):
        """Execute specific task."""
        pending_tasks = self.task_manager.get_pending_tasks()
        
        if not pending_tasks:
            print_warning("Немає очікуваних завдань для виконання.")
            input("Натисніть Enter для продовження...")
            return
        
        print_header("▶️ ВИКОНАННЯ ЗАВДАННЯ")
        
        print("Очікувані завдання:")
        for i, task in enumerate(pending_tasks, 1):
            print(f"{i}. #{task['id']} - {task['url'][:50]}...")
        
        try:
            choice = int(input(f"\nОберіть завдання (1-{len(pending_tasks)}): ").strip())
            if 1 <= choice <= len(pending_tasks):
                task = pending_tasks[choice - 1]
                await self._execute_single_task(task)
            else:
                print_error("Невірний номер завдання.")
        except ValueError:
            print_error("Введіть правильний номер.")
        
        input("Натисніть Enter для продовження...")
    
    async def _execute_single_task(self, task):
        """Execute single task."""
        print(f"\n🎯 Виконання завдання #{task['id']}")
        print(f"🔗 URL: {task['url']}")
        
        try:
            self.task_manager.update_task_status(task['id'], "processing")
            
            if task['likes'] == 0 and task['retweets'] == 0 and task['views'] == 0:
                # Auto mode
                result = await self.automation.auto_engage_tweet(task['url'])
            else:
                # Custom numbers
                result = await self.automation.process_tweet_url(
                    task['url'],
                    task['likes'],
                    task['retweets'], 
                    task['views']
                )
            
            if "error" in result:
                self.task_manager.update_task_status(task['id'], "failed", result)
                print_error(f"Помилка: {result['error']}")
            else:
                self.task_manager.update_task_status(task['id'], "completed", result)
                actions = result.get("actions", {})
                print_success("Завдання виконано успішно!")
                print(f"❤️ Лайки: {actions.get('likes', 0)}")
                print(f"🔄 Ретвіти: {actions.get('retweets', 0)}")
                print(f"👀 Перегляди: {actions.get('views', 0)}")
                
                if result.get("errors"):
                    print_warning(f"Деякі дії не вдалися: {len(result['errors'])} помилок")
        
        except Exception as e:
            self.task_manager.update_task_status(task['id'], "failed", {"error": str(e)})
            print_error(f"Помилка виконання: {e}")
    
    async def execute_all_tasks(self):
        """Execute all pending tasks."""
        pending_tasks = self.task_manager.get_pending_tasks()
        
        if not pending_tasks:
            print_warning("Немає очікуваних завдань.")
            input("Натисніть Enter для продовження...")
            return
        
        print_header("⚡ ВИКОНАННЯ ВСІХ ЗАВДАНЬ")
        
        print(f"Знайдено {len(pending_tasks)} очікуваних завдань.")
        confirm = input("Продовжити виконання всіх завдань? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print_info("Операцію скасовано.")
            input("Натисніть Enter для продовження...")
            return
        
        success_count = 0
        failed_count = 0
        
        for i, task in enumerate(pending_tasks, 1):
            print(f"\n📝 Виконання завдання {i}/{len(pending_tasks)}")
            try:
                await self._execute_single_task(task)
                success_count += 1
                
                # Delay between tasks
                if i < len(pending_tasks):
                    delay = 30  # 30 seconds between tasks
                    print(f"⏳ Очікування {delay} секунд перед наступним завданням...")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                print_error(f"Помилка виконання завдання #{task['id']}: {e}")
                failed_count += 1
        
        print(f"\n📊 Результат виконання:")
        print_success(f"Успішно виконано: {success_count}")
        if failed_count > 0:
            print_error(f"Помилки: {failed_count}")
        
        input("Натисніть Enter для продовження...")
    
    def proxy_menu(self):
        """Proxy management menu."""
        while True:
            clear_screen()
            print_header("🌐 УПРАВЛІННЯ ПРОКСІ")
            
            proxy_count = len(self.proxy_manager.proxies)
            
            print(f"{Colors.BOLD}📊 Статистика проксі:{Colors.END}")
            print(f"• 🌐 Налаштовано проксі: {proxy_count}")
            print()
            
            print(f"{Colors.BOLD}📋 ОПЦІЇ ПРОКСІ:{Colors.END}")
            print(f"{Colors.CYAN}1.{Colors.END} 📊 Показати налаштування проксі")
            print(f"{Colors.CYAN}2.{Colors.END} ➕ Призначити проксі акаунту")
            print(f"{Colors.CYAN}3.{Colors.END} 📂 Завантажити проксі з файлу")
            print(f"{Colors.CYAN}4.{Colors.END} 🔄 Автоматичне призначення проксі")
            print(f"{Colors.CYAN}5.{Colors.END} 🧪 Тестувати всі проксі")
            print(f"{Colors.CYAN}6.{Colors.END} 🔍 Тестувати один проксі")
            print(f"{Colors.CYAN}7.{Colors.END} 🗑️ Видалити проксі")
            print(f"{Colors.CYAN}8.{Colors.END} 🔙 Назад до головного меню")
            
            choice = input(f"\n{Colors.YELLOW}Оберіть опцію (1-8): {Colors.END}").strip()
            
            if choice == "1":
                self.show_proxy_settings()
            elif choice == "2":
                asyncio.run(self.assign_proxy_to_account())
            elif choice == "3":
                asyncio.run(self.load_proxies_from_file())
            elif choice == "4":
                asyncio.run(self.auto_assign_proxies())
            elif choice == "5":
                asyncio.run(self.test_proxies())
            elif choice == "6":
                asyncio.run(self.test_single_proxy())
            elif choice == "7":
                self.remove_proxy()
            elif choice == "8":
                break
            else:
                print_error("Невірний вибір.")
                input("Натисніть Enter для продовження...")
    
    async def quick_process(self):
        """Quick post processing."""
        print_header("⚡ ШВИДКА ОБРОБКА ПОСТУ")
        
        active_accounts = await self.automation.get_active_accounts()
        if not active_accounts:
            print_error("Немає активних акаунтів!")
            input("Натисніть Enter для продовження...")
            return
        
        print(f"👥 Доступно акаунтів: {len(active_accounts)}")
        
        url = input("🔗 URL посту для обробки: ").strip()
        if not url:
            print_error("URL не може бути порожнім!")
            input("Натисніть Enter для продовження...")
            return
        
        print("\n🎮 Режим обробки:")
        print("1. Автоматичний (реалістичні числа)")
        print("2. Кастомні числа")
        print("3. Високий engagement")
        print("4. Низький engagement")
        
        mode = input("Оберіть режим (1-4): ").strip()
        
        try:
            if mode == "1":
                result = await self.automation.auto_engage_tweet(url)
            elif mode == "2":
                likes = int(input("❤️ Лайки: ") or "0")
                retweets = int(input("🔄 Ретвіти: ") or "0")
                views = int(input("👀 Перегляди: ") or "0")
                result = await self.automation.process_tweet_url(url, likes, retweets, views)
            elif mode == "3":
                total = len(active_accounts)
                likes = min(total, int(total * 0.7))
                retweets = min(total, int(total * 0.4))
                views = min(total, int(total * 0.9))
                result = await self.automation.process_tweet_url(url, likes, retweets, views)
            elif mode == "4":
                total = len(active_accounts)
                likes = max(1, int(total * 0.1))
                retweets = max(0, int(total * 0.03))
                views = max(1, int(total * 0.3))
                result = await self.automation.process_tweet_url(url, likes, retweets, views)
            else:
                print_error("Невірний режим.")
                input("Натисніть Enter для продовження...")
                return
            
            if "error" in result:
                print_error(f"Помилка: {result['error']}")
            else:
                actions = result.get("actions", {})
                print_success("Обробку завершено!")
                print(f"❤️ Лайки: {actions.get('likes', 0)}")
                print(f"🔄 Ретвіти: {actions.get('retweets', 0)}")
                print(f"👀 Перегляди: {actions.get('views', 0)}")
                
                if result.get("errors"):
                    print_warning(f"Деякі дії не вдалися: {len(result['errors'])} помилок")
        
        except Exception as e:
            print_error(f"Помилка обробки: {e}")
        
        input("Натисніть Enter для продовження...")
    
    def show_proxy_settings(self):
        """Show proxy settings for all accounts."""
        print_header("📊 НАЛАШТУВАННЯ ПРОКСІ")
        
        if not self.proxy_manager.proxies:
            print_warning("Проксі не налаштовані.")
            input("Натисніть Enter для продовження...")
            return
        
        print(f"{'Акаунт':<20} {'Проксі'}")
        print("-" * 60)
        
        for username, proxy in self.proxy_manager.proxies.items():
            print(f"@{username:<19} {proxy}")
        
        input("\nНатисніть Enter для продовження...")
    
    async def assign_proxy_to_account(self):
        """Assign proxy to specific account."""
        print_header("➕ ПРИЗНАЧЕННЯ ПРОКСІ АКАУНТУ")
        
        try:
            accounts_info = await self.api.pool.accounts_info()
            if not accounts_info:
                print_warning("Акаунти не знайдені.")
                input("Натисніть Enter для продовження...")
                return
            
            print("Доступні акаунти:")
            for i, acc in enumerate(accounts_info, 1):
                current_proxy = self.proxy_manager.get_proxy(acc["username"]) or "Без проксі"
                print(f"{i}. @{acc['username']} (зараз: {current_proxy})")
            
            try:
                choice = int(input(f"\nОберіть акаунт (1-{len(accounts_info)}): ").strip())
                if 1 <= choice <= len(accounts_info):
                    account = accounts_info[choice - 1]
                    username = account["username"]
                    
                    print(f"\nФормати проксі:")
                    print("• http://user:pass@host:port")
                    print("• https://user:pass@host:port")
                    print("• socks5://user:pass@host:port")
                    
                    proxy = input(f"\nВведіть проксі для @{username}: ").strip()
                    
                    if proxy:
                        self.proxy_manager.assign_proxy(username, proxy)
                        print_success(f"Проксі призначено для @{username}")
                    else:
                        self.proxy_manager.remove_proxy(username)
                        print_success(f"Проксі видалено для @{username}")
                else:
                    print_error("Невірний номер акаунта.")
            except ValueError:
                print_error("Введіть правильний номер.")
                
        except Exception as e:
            print_error(f"Помилка: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def load_proxies_from_file(self):
        """Load proxies from file."""
        print_header("📂 ЗАВАНТАЖЕННЯ ПРОКСІ З ФАЙЛУ")
        
        print("Підтримувані формати:")
        print("• TXT файл: одна строка = один проксі")
        print("• Формат: username:proxy або просто proxy")
        print()
        
        file_path = input("📁 Шлях до файлу з проксі: ").strip()
        
        if not os.path.exists(file_path):
            print_error("Файл не знайдено!")
            input("Натисніть Enter для продовження...")
            return
        
        try:
            proxies_list = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line and line.count(':') >= 3:  # Contains proxy format
                            parts = line.split(':', 1)
                            if len(parts) == 2:
                                username, proxy = parts
                                self.proxy_manager.assign_proxy(username.strip(), proxy.strip())
                            else:
                                proxies_list.append(line)
                        else:
                            proxies_list.append(line)
            
            if proxies_list:
                print(f"\nЗнайдено {len(proxies_list)} проксі без прив'язки до акаунтів.")
                auto_assign = input("Хочете автоматично розподілити їх між акаунтами? (y/N): ").strip().lower()
                
                if auto_assign == 'y':
                    await self._auto_distribute_proxies(proxies_list)
                else:
                    print_info("Проксі завантажено, але не призначено.")
                    print_info("Використайте 'Автоматичне призначення проксі' для призначення.")
            
            print_success("Проксі завантажено!")
            
        except Exception as e:
            print_error(f"Помилка завантаження проксі: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def _auto_distribute_proxies(self, proxies_list):
        """Auto distribute proxies among accounts."""
        try:
            accounts_info = await self.api.pool.accounts_info()
            accounts_without_proxy = [acc for acc in accounts_info 
                                    if not self.proxy_manager.get_proxy(acc["username"])]
            
            for i, account in enumerate(accounts_without_proxy):
                if i < len(proxies_list):
                    proxy = proxies_list[i]
                    self.proxy_manager.assign_proxy(account["username"], proxy)
                    print_success(f"@{account['username']} -> {proxy}")
            
            if len(proxies_list) > len(accounts_without_proxy):
                print_warning(f"Залишилося {len(proxies_list) - len(accounts_without_proxy)} проксі")
            
        except Exception as e:
            print_error(f"Помилка розподілу проксі: {e}")
    
    def auto_assign_proxies(self):
        """Auto assign proxies to accounts without proxy."""
        print_header("🔄 АВТОМАТИЧНЕ ПРИЗНАЧЕННЯ ПРОКСІ")
        
        # Check if we have any free proxies in my_proxies.txt
        if os.path.exists("my_proxies.txt"):
            try:
                with open("my_proxies.txt", 'r', encoding='utf-8') as f:
                    all_proxies = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            all_proxies.append(line)
                
                if not all_proxies:
                    print_warning("Файл my_proxies.txt порожній!")
                    input("Натисніть Enter для продовження...")
                    return
                
                # Get accounts without proxies
                asyncio.run(self._perform_auto_proxy_assignment(all_proxies))
                
            except Exception as e:
                print_error(f"Помилка читання файлу проксі: {e}")
                input("Натисніть Enter для продовження...")
        else:
            print_warning("Файл my_proxies.txt не знайдено!")
            print_info("Створіть файл my_proxies.txt з проксі або завантажте через меню.")
            input("Натисніть Enter для продовження...")
    
    async def _perform_auto_proxy_assignment(self, proxies_list):
        """Perform automatic proxy assignment."""
        try:
            accounts_info = await self.api.pool.accounts_info()
            if not accounts_info:
                print_warning("Акаунти не знайдені.")
                input("Натисніть Enter для продовження...")
                return
            
            # Find accounts without proxies
            accounts_without_proxy = []
            for account in accounts_info:
                username = account["username"]
                if not self.proxy_manager.get_proxy(username):
                    accounts_without_proxy.append(username)
            
            if not accounts_without_proxy:
                print_success("Всі акаунти вже мають призначені проксі!")
                input("Натисніть Enter для продовження...")
                return
            
            print(f"📊 Статистика:")
            print(f"• Всього акаунтів: {len(accounts_info)}")
            print(f"• Без проксі: {len(accounts_without_proxy)}")
            print(f"• Доступно проксі: {len(proxies_list)}")
            print()
            
            if len(proxies_list) < len(accounts_without_proxy):
                print_warning(f"Проксі менше ніж акаунтів без проксі!")
                print(f"Буде призначено {len(proxies_list)} проксі")
            
            confirm = input("Продовжити автоматичне призначення? (y/N): ").strip().lower()
            if confirm != 'y':
                print_info("Операцію скасовано.")
                input("Натисніть Enter для продовження...")
                return
            
            # Assign proxies
            assigned_count = 0
            for i, username in enumerate(accounts_without_proxy):
                if i < len(proxies_list):
                    proxy = proxies_list[i]
                    self.proxy_manager.assign_proxy(username, proxy)
                    print_success(f"@{username} -> {proxy[:50]}{'...' if len(proxy) > 50 else ''}")
                    assigned_count += 1
            
            print(f"\n✅ Успішно призначено {assigned_count} проксі!")
            
            if len(proxies_list) > len(accounts_without_proxy):
                remaining = len(proxies_list) - len(accounts_without_proxy)
                print_info(f"Залишилося {remaining} невикористаних проксі")
            
        except Exception as e:
            print_error(f"Помилка призначення проксі: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def test_proxies(self):
        """Test proxy connections."""
        print_header("🧪 ТЕСТУВАННЯ ПРОКСІ")
        
        if not self.proxy_manager.proxies:
            print_warning("Проксі не налаштовані.")
            input("Натисніть Enter для продовження...")
            return
        
        print("⏳ Тестування проксі...")
        print(f"🔍 Всього проксі для тестування: {len(self.proxy_manager.proxies)}")
        print()
        
        working_count = 0
        failed_count = 0
        
        for username, proxy in self.proxy_manager.proxies.items():
            print(f"🔄 Тестуємо @{username}...", end=" ")
            
            result = await self.proxy_manager.test_proxy(proxy)
            
            if result["success"]:
                print_success(f"✅ IP: {result['ip']} ({result.get('response_time', 0):.2f}s)")
                working_count += 1
            else:
                print_error(f"❌ {result['error']}")
                failed_count += 1
        
        print(f"\n📊 Результат тестування:")
        print_success(f"✅ Працюють: {working_count}")
        if failed_count > 0:
            print_error(f"❌ Не працюють: {failed_count}")
        
        if working_count > 0:
            percentage = (working_count / (working_count + failed_count)) * 100
            print(f"📈 Відсоток працюючих: {percentage:.1f}%")
        
        input("Натисніть Enter для продовження...")
    
    async def test_single_proxy(self):
        """Test a single proxy connection."""
        print_header("🔍 ТЕСТУВАННЯ ОДНОГО ПРОКСІ")
        
        print("Введіть проксі в форматі:")
        print("• http://username:password@ip:port")
        print("• username:password@ip:port")
        print("• ip:port")
        print()
        
        proxy_input = input("🔗 Введіть проксі: ").strip()
        
        if not proxy_input:
            print_error("Проксі не введено!")
            input("Натисніть Enter для продовження...")
            return
        
        print(f"⏳ Тестуємо проксі: {proxy_input}")
        print()
        
        result = await self.proxy_manager.test_proxy(proxy_input)
        
        if result["success"]:
            print_success(f"✅ Проксі працює!")
            print(f"🌐 IP: {result['ip']}")
            print(f"🏆 Сервіс: {result.get('service', 'Unknown')}")
            if result.get('response_time'):
                print(f"⏱️ Час відповіді: {result['response_time']:.2f}s")
        else:
            print_error(f"❌ Проксі не працює: {result['error']}")
        
        input("Натисніть Enter для продовження...")
    
    def remove_proxy(self):
        """Remove proxy from account."""
        print_header("🗑️ ВИДАЛЕННЯ ПРОКСІ")
        
        if not self.proxy_manager.proxies:
            print_warning("Проксі не налаштовані.")
            input("Натисніть Enter для продовження...")
            return
        
        print("Акаунти з проксі:")
        usernames = list(self.proxy_manager.proxies.keys())
        for i, username in enumerate(usernames, 1):
            proxy = self.proxy_manager.proxies[username]
            print(f"{i}. @{username} -> {proxy}")
        
        try:
            choice = int(input(f"\nОберіть акаунт для видалення проксі (1-{len(usernames)}): ").strip())
            if 1 <= choice <= len(usernames):
                username = usernames[choice - 1]
                self.proxy_manager.remove_proxy(username)
                print_success(f"Проксі видалено для @{username}")
            else:
                print_error("Невірний номер.")
        except ValueError:
            print_error("Введіть правильний номер.")
        
        input("Натисніть Enter для продовження...")
    
    def telegram_menu(self):
        """Telegram bot menu."""
        print_header("🤖 TELEGRAM БОТ")
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        print(f"{Colors.BOLD}📊 Статус Telegram бота:{Colors.END}")
        print(f"• 🔑 Токен: {'✅ Налаштовано' if bot_token else '❌ Не налаштовано'}")
        print(f"• 🤖 Автоматичний режим: {'✅ Увімкнено' if os.getenv('AUTO_MODE', 'true').lower() == 'true' else '❌ Вимкнено'}")
        print()
        
        if not bot_token:
            print_error("Telegram бот не налаштовано!")
            print("Для налаштування:")
            print("1. Створіть бота через @BotFather")
            print("2. Отримайте токен бота")
            print("3. Встановіть TELEGRAM_BOT_TOKEN в config.env")
            input("\nНатисніть Enter для продовження...")
            return
        
        print(f"{Colors.BOLD}📋 ОПЦІЇ БОТА:{Colors.END}")
        print(f"{Colors.CYAN}1.{Colors.END} ▶️ Запустити Telegram бота")
        print(f"{Colors.CYAN}2.{Colors.END} ⚙️ Налаштування бота")
        print(f"{Colors.CYAN}3.{Colors.END} 📊 Статистика бота")
        print(f"{Colors.CYAN}4.{Colors.END} 🔙 Назад до головного меню")
        
        choice = input(f"\n{Colors.YELLOW}Оберіть опцію (1-4): {Colors.END}").strip()
        
        if choice == "1":
            self.run_telegram_bot()
        elif choice == "2":
            self.telegram_settings()
        elif choice == "3":
            self.telegram_stats()
        elif choice == "4":
            return
        else:
            print_error("Невірний вибір.")
            input("Натисніть Enter для продовження...")
    
    def run_telegram_bot(self):
        """Run Telegram bot."""
        print_header("▶️ ЗАПУСК TELEGRAM БОТА")
        
        try:
            config = TwitterBotConfig()
            bot = TwitterTelegramBot(config)
            
            print("🤖 Запуск Telegram бота...")
            print("💡 Для зупинки натисніть Ctrl+C")
            print()
            
            bot.run()
            
        except KeyboardInterrupt:
            print_success("Бот зупинено користувачем.")
        except Exception as e:
            print_error(f"Помилка запуску бота: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def statistics_menu(self):
        """Statistics and monitoring menu."""
        print_header("📊 СТАТИСТИКА ТА МОНІТОРИНГ")
        
        try:
            # Account stats
            accounts_info = await self.api.pool.accounts_info()
            stats = await self.api.pool.stats()
            
            active_count = sum(1 for acc in accounts_info if acc["active"])
            
            print(f"{Colors.BOLD}👥 Статистика акаунтів:{Colors.END}")
            print(f"• Всього: {len(accounts_info)}")
            print(f"• 🟢 Активні: {active_count}")
            print(f"• 🔴 Неактивні: {len(accounts_info) - active_count}")
            
            # Task stats
            completed_tasks = [t for t in self.task_manager.tasks if t["status"] == "completed"]
            pending_tasks = self.task_manager.get_pending_tasks()
            
            print(f"\n{Colors.BOLD}🎯 Статистика завдань:{Colors.END}")
            print(f"• Всього: {len(self.task_manager.tasks)}")
            print(f"• ✅ Виконано: {len(completed_tasks)}")
            print(f"• 📝 Очікують: {len(pending_tasks)}")
            
            # Proxy stats
            proxy_count = len(self.proxy_manager.proxies)
            accounts_with_proxy = sum(1 for acc in accounts_info 
                                    if self.proxy_manager.get_proxy(acc["username"]))
            
            print(f"\n{Colors.BOLD}🌐 Статистика проксі:{Colors.END}")
            print(f"• Налаштовано проксі: {proxy_count}")
            print(f"• Акаунтів з проксі: {accounts_with_proxy}")
            
            # Recent activity
            if completed_tasks:
                print(f"\n{Colors.BOLD}📈 Остання активність:{Colors.END}")
                recent_tasks = sorted(completed_tasks, 
                                    key=lambda x: x.get("processed_at", ""), 
                                    reverse=True)[:5]
                
                for task in recent_tasks:
                    processed_time = task.get("processed_at", "")
                    if processed_time:
                        time_str = datetime.fromisoformat(processed_time).strftime("%Y-%m-%d %H:%M")
                        url_short = task["url"][:40] + "..." if len(task["url"]) > 40 else task["url"]
                        print(f"• {time_str}: {url_short}")
            
        except Exception as e:
            print_error(f"Помилка отримання статистики: {e}")
        
        input("\nНатисніть Enter для продовження...")
    
    def settings_menu(self):
        """System settings menu."""
        print_header("⚙️ НАЛАШТУВАННЯ СИСТЕМИ")
        
        print(f"{Colors.BOLD}📋 НАЛАШТУВАННЯ:{Colors.END}")
        print(f"{Colors.CYAN}1.{Colors.END} 🔧 Редагувати конфігурацію")
        print(f"{Colors.CYAN}2.{Colors.END} 📊 Показати поточні налаштування")
        print(f"{Colors.CYAN}3.{Colors.END} 🔄 Перезавантажити конфігурацію")
        print(f"{Colors.CYAN}4.{Colors.END} 💾 Створити резервну копію")
        print(f"{Colors.CYAN}5.{Colors.END} ⚡ Режим швидкості (зараз: {'ШВИДКИЙ' if self.fast_mode else 'СТАНДАРТНИЙ'})")
        print(f"{Colors.CYAN}6.{Colors.END} 🔙 Назад до головного меню")
        
        choice = input(f"\n{Colors.YELLOW}Оберіть опцію (1-6): {Colors.END}").strip()
        
        if choice == "1":
            self.edit_config()
        elif choice == "2":
            self.show_current_settings()
        elif choice == "3":
            load_env_file()
            print_success("Конфігурацію перезавантажено!")
            input("Натисніть Enter для продовження...")
        elif choice == "4":
            self.create_backup()
        elif choice == "5":
            self.toggle_fast_mode()
        elif choice == "6":
            return
        else:
            print_error("Невірний вибір.")
            input("Натисніть Enter для продовження...")
    
    async def testing_menu(self):
        """Testing menu."""
        print_header("🧪 ТЕСТУВАННЯ СИСТЕМИ")
        
        active_accounts = await self.automation.get_active_accounts()
        
        print(f"{Colors.BOLD}📊 Статус системи:{Colors.END}")
        print(f"• 👥 Активні акаунти: {len(active_accounts)}")
        print(f"• 🌐 Проксі налаштовані: {len(self.proxy_manager.proxies)}")
        print()
        
        print(f"{Colors.BOLD}📋 ТЕСТИ:{Colors.END}")
        print(f"{Colors.CYAN}1.{Colors.END} 🧪 Тест підключення акаунтів")
        print(f"{Colors.CYAN}2.{Colors.END} 🌐 Тест проксі")
        print(f"{Colors.CYAN}3.{Colors.END} 🎯 Тест обробки посту")
        print(f"{Colors.CYAN}4.{Colors.END} 🤖 Тест API операцій")
        print(f"{Colors.CYAN}5.{Colors.END} 🔙 Назад до головного меню")
        
        choice = input(f"\n{Colors.YELLOW}Оберіть тест (1-5): {Colors.END}").strip()
        
        if choice == "1":
            await self.test_accounts_connection()
        elif choice == "2":
            await self.test_proxies()
        elif choice == "3":
            await self.test_post_processing()
        elif choice == "4":
            await self.test_api_operations()
        elif choice == "5":
            return
        else:
            print_error("Невірний вибір.")
            input("Натисніть Enter для продовження...")
    
    async def test_accounts_connection(self):
        """Test accounts connection."""
        print_header("🧪 ТЕСТ ПІДКЛЮЧЕННЯ АКАУНТІВ")
        
        try:
            accounts_info = await self.api.pool.accounts_info()
            
            if not accounts_info:
                print_warning("Акаунти не знайдені.")
                input("Натисніть Enter для продовження...")
                return
            
            print("⏳ Тестування підключення акаунтів...")
            
            for account in accounts_info:
                username = account["username"]
                try:
                    # Try to get account info
                    user_info = await self.api.user_by_login(username)
                    if user_info:
                        print_success(f"@{username}: Підключення OK")
                    else:
                        print_error(f"@{username}: Не вдалося отримати дані")
                except Exception as e:
                    print_error(f"@{username}: {str(e)[:50]}")
                
                await asyncio.sleep(1)  # Delay between tests
            
        except Exception as e:
            print_error(f"Помилка тестування: {e}")
        
        input("Натисніть Enter для продовження...")
    
    async def test_post_processing(self):
        """Test post processing."""
        print_header("🎯 ТЕСТ ОБРОБКИ ПОСТУ")
        
        test_url = input("🔗 URL для тестування (або Enter для демо): ").strip()
        if not test_url:
            test_url = "https://x.com/elonmusk/status/1234567890"
            print(f"Використовується демо URL: {test_url}")
        
        try:
            print("⏳ Тестування обробки посту...")
            result = await self.automation.auto_engage_tweet(test_url)
            
            if "error" in result:
                print_error(f"Помилка: {result['error']}")
            else:
                actions = result.get("actions", {})
                print_success("Тест пройшов успішно!")
                print(f"❤️ Лайки: {actions.get('likes', 0)}")
                print(f"🔄 Ретвіти: {actions.get('retweets', 0)}")
                print(f"👀 Перегляди: {actions.get('views', 0)}")
                
        except Exception as e:
            print_error(f"Помилка тестування: {e}")
        
        input("Натисніть Enter для продовження...")


    def toggle_fast_mode(self):
        """Toggle between fast and standard modes."""
        self.fast_mode = not self.fast_mode
        # Оновлюємо режим в automation об'єкті
        self.automation.fast_mode = self.fast_mode
        
        mode_name = "ШВИДКИЙ" if self.fast_mode else "СТАНДАРТНИЙ"
        
        print_success(f"Режим змінено на: {mode_name}")
        print(f"{Colors.CYAN}ℹ️ Інформація:{Colors.END}")
        if self.fast_mode:
            print("🟢 ШВИДКИЙ РЕЖИМ: Мінімальні затримки (3 сек замість 120 сек)")
            print("   └─ Швидка обробка, але вищий ризик обмежень")
        else:
            print("🟡 СТАНДАРТНИЙ РЕЖИМ: Стандартні затримки twscrape (120 сек)")
            print("   └─ Безпечніший, але повільніший")
        
        input("Натисніть Enter для продовження...")

    def toggle_fast_mode(self):
        """Toggle between fast and standard mode."""
        self.fast_mode = not self.fast_mode
        # Оновлюємо режим в automation об'єкті
        self.automation.fast_mode = self.fast_mode
        
        mode_text = "ШВИДКИЙ" if self.fast_mode else "СТАНДАРТНИЙ"
        print_success(f"Режим змінено на: {mode_text}")
        
        if self.fast_mode:
            print("🟢 ШВИДКИЙ РЕЖИМ: Мінімальні затримки (3 сек замість 120 сек)")
            print("   └─ Швидка обробка, але вищий ризик обмежень")
        else:
            print("🟡 СТАНДАРТНИЙ РЕЖИМ: Стандартні затримки twscrape (120 сек)")
            print("   └─ Безпечніший, але повільніший")
        
        input("Натисніть Enter для продовження...")

def main():
    """Main function."""
    try:
        manager = AdvancedTwitterManager()
        asyncio.run(manager.main_menu())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Програму зупинено користувачем.{Colors.END}")
    except Exception as e:
        print_error(f"Критична помилка: {e}")


if __name__ == "__main__":
    main()