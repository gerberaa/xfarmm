#!/usr/bin/env python3
"""
Main launcher script for Twitter/X Automation System

This script provides a unified interface to manage accounts and run the automation.
"""

import asyncio
import os
import sys
from typing import Optional

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API
from twitter_automation import TwitterAutomation
from telegram_bot import TwitterTelegramBot, TwitterBotConfig


def load_env_file(file_path: str = "config.env"):
    """Load environment variables from a file."""
    if not os.path.exists(file_path):
        print(f"⚠️ Config file {file_path} not found. Using default settings.")
        return
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


async def setup_accounts():
    """Setup and manage accounts."""
    print("🔧 Account Management")
    print("=" * 50)
    print()
    print("1. Add all accounts from script")
    print("2. Show account status")
    print("3. Login all accounts")
    print("4. Reset account locks")
    print("5. Delete inactive accounts")
    print("6. Back to main menu")
    print()
    
    choice = input("Enter your choice (1-6): ").strip()
    
    if choice == "1":
        # Import and run bulk account setup
        from setup_accounts_bulk import add_all_accounts
        await add_all_accounts()
    
    elif choice == "2":
        from setup_accounts_bulk import show_accounts_status
        await show_accounts_status()
    
    elif choice == "3":
        api = API()
        print("🔄 Logging in all accounts...")
        result = await api.pool.login_all()
        print(f"✅ Success: {result['success']}, ❌ Failed: {result['failed']}")
    
    elif choice == "4":
        api = API()
        await api.pool.reset_locks()
        print("✅ All account locks have been reset.")
    
    elif choice == "5":
        api = API()
        await api.pool.delete_inactive()
        print("✅ All inactive accounts have been deleted.")
    
    elif choice == "6":
        return
    
    else:
        print("❌ Invalid choice.")
    
    input("\nPress Enter to continue...")


async def test_automation():
    """Test the automation system."""
    print("🧪 Testing Automation System")
    print("=" * 50)
    print()
    
    api = API()
    automation = TwitterAutomation(api)
    
    # Get account status
    active_accounts = await automation.get_active_accounts()
    print(f"👥 Active accounts: {len(active_accounts)}")
    
    if not active_accounts:
        print("❌ No active accounts available. Please setup accounts first.")
        input("Press Enter to continue...")
        return
    
    # Get test URL
    test_url = input("🔗 Enter a Twitter/X URL to test (or press Enter for demo): ").strip()
    
    if not test_url:
        test_url = "https://x.com/elonmusk/status/1234567890"
        print(f"Using demo URL: {test_url}")
    
    print(f"\n🎯 Testing automation with: {test_url}")
    print("⏳ This may take a few minutes...")
    
    try:
        result = await automation.auto_engage_tweet(test_url)
        
        print("\n📊 Test Results:")
        print(f"Tweet ID: {result.get('tweet_id', 'N/A')}")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            actions = result.get("actions", {})
            print(f"❤️ Likes: {actions.get('likes', 0)}")
            print(f"🔄 Retweets: {actions.get('retweets', 0)}")
            print(f"👀 Views: {actions.get('views', 0)}")
            
            if result.get("errors"):
                print(f"⚠️ Errors: {len(result['errors'])}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    input("\nPress Enter to continue...")


def run_telegram_bot():
    """Run the Telegram bot."""
    print("🤖 Starting Telegram Bot")
    print("=" * 50)
    
    # Check if bot token is configured
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("❌ TELEGRAM_BOT_TOKEN not configured!")
        print()
        print("To setup the Telegram bot:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Get the bot token")
        print("3. Edit config.env and set TELEGRAM_BOT_TOKEN")
        print("4. Restart this script")
        input("\nPress Enter to continue...")
        return
    
    config = TwitterBotConfig()
    bot = TwitterTelegramBot(config)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped.")
    except Exception as e:
        print(f"❌ Bot error: {e}")


async def manual_process():
    """Manually process a tweet."""
    print("🎯 Manual Tweet Processing")
    print("=" * 50)
    print()
    
    api = API()
    automation = TwitterAutomation(api)
    
    # Get account status
    active_accounts = await automation.get_active_accounts()
    print(f"👥 Active accounts: {len(active_accounts)}")
    
    if not active_accounts:
        print("❌ No active accounts available. Please setup accounts first.")
        input("Press Enter to continue...")
        return
    
    # Get tweet URL
    tweet_url = input("🔗 Enter Twitter/X URL: ").strip()
    if not tweet_url:
        print("❌ No URL provided.")
        input("Press Enter to continue...")
        return
    
    print()
    print("📊 Engagement options:")
    print("1. Auto (realistic numbers)")
    print("2. Custom numbers")
    print("3. High engagement")
    print("4. Low engagement")
    
    mode = input("\nChoose mode (1-4): ").strip()
    
    try:
        if mode == "1":
            result = await automation.auto_engage_tweet(tweet_url)
        
        elif mode == "2":
            likes = int(input("❤️ Number of likes: ") or "0")
            retweets = int(input("🔄 Number of retweets: ") or "0") 
            views = int(input("👀 Number of views: ") or "0")
            result = await automation.process_tweet_url(tweet_url, likes, retweets, views)
        
        elif mode == "3":
            # High engagement - use more accounts
            total = len(active_accounts)
            likes = min(total, int(total * 0.6))
            retweets = min(total, int(total * 0.3))
            views = min(total, int(total * 0.9))
            result = await automation.process_tweet_url(tweet_url, likes, retweets, views)
        
        elif mode == "4":
            # Low engagement
            total = len(active_accounts)
            likes = min(total, max(1, int(total * 0.1)))
            retweets = min(total, max(0, int(total * 0.05)))
            views = min(total, max(1, int(total * 0.3)))
            result = await automation.process_tweet_url(tweet_url, likes, retweets, views)
        
        else:
            print("❌ Invalid mode.")
            input("Press Enter to continue...")
            return
        
        print("\n📊 Processing Results:")
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            actions = result.get("actions", {})
            print(f"✅ Successfully processed!")
            print(f"❤️ Likes: {actions.get('likes', 0)}")
            print(f"🔄 Retweets: {actions.get('retweets', 0)}")
            print(f"👀 Views: {actions.get('views', 0)}")
            
            if result.get("errors"):
                print(f"⚠️ Some actions failed: {len(result['errors'])} errors")
    
    except Exception as e:
        print(f"❌ Processing failed: {e}")
    
    input("\nPress Enter to continue...")


def main_menu():
    """Display main menu and handle user choices."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
        
        print("🚀 Twitter/X Automation System")
        print("=" * 50)
        print()
        print("1. 🔧 Account Management")
        print("2. 🤖 Run Telegram Bot")
        print("3. 🎯 Manual Tweet Processing")
        print("4. 🧪 Test Automation")
        print("5. 📊 System Status")
        print("6. ❌ Exit")
        print()
        
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == "1":
            asyncio.run(setup_accounts())
        
        elif choice == "2":
            run_telegram_bot()
        
        elif choice == "3":
            asyncio.run(manual_process())
        
        elif choice == "4":
            asyncio.run(test_automation())
        
        elif choice == "5":
            asyncio.run(show_system_status())
        
        elif choice == "6":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")
            input("Press Enter to continue...")


async def show_system_status():
    """Show system status."""
    print("📊 System Status")
    print("=" * 50)
    
    try:
        api = API()
        
        # Account statistics
        stats = await api.pool.stats()
        print(f"📈 Account Statistics:")
        print(f"• Total accounts: {stats.get('total', 0)}")
        print(f"• Active accounts: {stats.get('active', 0)}")
        print(f"• Inactive accounts: {stats.get('inactive', 0)}")
        
        # Show locked queues
        locked_queues = [k for k in stats.keys() if k.startswith('locked_')]
        if locked_queues:
            print(f"\n🔒 Locked Queues:")
            for queue in locked_queues:
                count = stats[queue]
                queue_name = queue.replace('locked_', '')
                print(f"• {queue_name}: {count} accounts locked")
        
        # Configuration status
        print(f"\n⚙️ Configuration:")
        print(f"• Telegram token: {'✅ Set' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Not set'}")
        print(f"• Auto mode: {'✅ Enabled' if os.getenv('AUTO_MODE', 'true').lower() == 'true' else '❌ Disabled'}")
        print(f"• Debug mode: {'✅ Enabled' if os.getenv('DEBUG_MODE', 'false').lower() == 'true' else '❌ Disabled'}")
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")
    
    input("\nPress Enter to continue...")


def main():
    """Main function."""
    # Load configuration
    load_env_file()
    
    # Show welcome message
    print("🚀 Welcome to Twitter/X Automation System!")
    print()
    print("This system allows you to:")
    print("• Manage multiple Twitter/X accounts")
    print("• Automatically like, retweet, and view posts")
    print("• Integrate with Telegram for easy automation")
    print("• Process tweets with realistic engagement patterns")
    print()
    
    # Check if we have any accounts
    try:
        api = API()
        accounts_info = asyncio.run(api.pool.accounts_info())
        
        if not accounts_info:
            print("ℹ️ No accounts found. Let's set them up first!")
            input("Press Enter to continue to account setup...")
            asyncio.run(setup_accounts())
        else:
            active_count = sum(1 for acc in accounts_info if acc["active"])
            print(f"✅ Found {len(accounts_info)} accounts ({active_count} active)")
    
    except Exception as e:
        print(f"⚠️ Could not check accounts: {e}")
    
    # Start main menu
    main_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 System stopped by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your configuration and try again.")