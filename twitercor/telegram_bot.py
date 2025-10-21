#!/usr/bin/env python3
"""
Telegram Bot for Twitter/X Automation

This bot listens to messages in Telegram groups and automatically
processes Twitter/X links with likes, retweets, and views.
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Optional

from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

from twscrape import API
from twitter_automation import TwitterAutomation


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TwitterBotConfig:
    """Configuration for the Twitter automation bot."""
    
    def __init__(self):
        # Telegram settings
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.allowed_groups = os.getenv("ALLOWED_GROUPS", "").split(",")
        self.allowed_users = os.getenv("ALLOWED_USERS", "").split(",")
        
        # Automation settings
        self.auto_mode = os.getenv("AUTO_MODE", "true").lower() == "true"
        self.min_delay = int(os.getenv("MIN_DELAY", "60"))  # Minimum delay between processing tweets
        self.max_delay = int(os.getenv("MAX_DELAY", "300"))  # Maximum delay
        
        # Engagement settings
        self.default_likes_min = int(os.getenv("DEFAULT_LIKES_MIN", "5"))
        self.default_likes_max = int(os.getenv("DEFAULT_LIKES_MAX", "15"))
        self.default_retweets_min = int(os.getenv("DEFAULT_RETWEETS_MIN", "2"))
        self.default_retweets_max = int(os.getenv("DEFAULT_RETWEETS_MAX", "8"))
        self.default_views_min = int(os.getenv("DEFAULT_VIEWS_MIN", "20"))
        self.default_views_max = int(os.getenv("DEFAULT_VIEWS_MAX", "50"))


class TwitterTelegramBot:
    """Main Telegram bot class for Twitter automation."""
    
    def __init__(self, config: TwitterBotConfig):
        self.config = config
        self.api = API()
        self.automation = TwitterAutomation(self.api)
        self.processed_tweets = set()  # Track processed tweets to avoid duplicates
        self.last_processing_time = 0
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        welcome_text = """
🤖 **Twitter/X Automation Bot**

I automatically process Twitter/X links posted in this group!

**Commands:**
• `/start` - Show this message
• `/status` - Show bot and accounts status
• `/stats` - Show processing statistics
• `/process <url>` - Manually process a tweet
• `/auto on/off` - Toggle auto-processing mode

**Auto Mode:** {}

When auto mode is ON, I'll automatically process any Twitter/X links posted in the group with realistic engagement numbers.

Drop a Twitter/X link and watch the magic happen! ✨
        """.format("🟢 ON" if self.config.auto_mode else "🔴 OFF")
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        # Get account status
        active_accounts = await self.automation.get_active_accounts()
        accounts_info = await self.api.pool.accounts_info()
        
        total_accounts = len(accounts_info)
        active_count = len(active_accounts)
        inactive_count = total_accounts - active_count
        
        status_text = f"""
📊 **Bot Status**

**Accounts:**
• Total: {total_accounts}
• 🟢 Active: {active_count}
• 🔴 Inactive: {inactive_count}

**Settings:**
• Auto Mode: {"🟢 ON" if self.config.auto_mode else "🔴 OFF"}
• Processed Tweets: {len(self.processed_tweets)}

**Active Accounts:**
        """
        
        if active_accounts:
            for account in active_accounts[:10]:  # Show first 10
                status_text += f"• @{account}\n"
            if len(active_accounts) > 10:
                status_text += f"• ... and {len(active_accounts) - 10} more\n"
        else:
            status_text += "• None\n"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        stats_text = f"""
📈 **Processing Statistics**

• Processed Tweets: {len(self.processed_tweets)}
• Auto Mode: {"🟢 ON" if self.config.auto_mode else "🔴 OFF"}

**Recent Tweets:**
        """
        
        recent_tweets = list(self.processed_tweets)[-5:]  # Last 5
        if recent_tweets:
            for tweet_id in recent_tweets:
                stats_text += f"• {tweet_id}\n"
        else:
            stats_text += "• None processed yet\n"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /process command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a Twitter/X URL. Usage: `/process <url>`", parse_mode='Markdown')
            return
        
        tweet_url = context.args[0]
        await self.process_tweet_from_message(update, tweet_url, manual=True)

    async def auto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /auto command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        if not context.args or context.args[0].lower() not in ['on', 'off']:
            await update.message.reply_text("❌ Usage: `/auto on` or `/auto off`", parse_mode='Markdown')
            return
        
        new_mode = context.args[0].lower() == 'on'
        self.config.auto_mode = new_mode
        
        mode_text = "🟢 ON" if new_mode else "🔴 OFF"
        await update.message.reply_text(f"✅ Auto mode set to: {mode_text}")

    def is_authorized(self, user_id: int, chat_id: int) -> bool:
        """Check if user/group is authorized to use the bot."""
        # Check if it's an allowed group
        if str(chat_id) in self.config.allowed_groups:
            return True
        
        # Check if it's an allowed user
        if str(user_id) in self.config.allowed_users:
            return True
        
        # If no restrictions are set, allow all
        if not self.config.allowed_groups and not self.config.allowed_users:
            return True
        
        return False

    def extract_twitter_urls(self, text: str) -> List[str]:
        """Extract Twitter/X URLs from text."""
        patterns = [
            r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/\d+',
            r'https?://(?:www\.)?(?:twitter\.com|x\.com)/i/status/\d+',
        ]
        
        urls = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urls.extend(matches)
        
        return list(set(urls))  # Remove duplicates

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages and process Twitter links."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            return
        
        if not self.config.auto_mode:
            return
        
        message_text = update.message.text or ""
        twitter_urls = self.extract_twitter_urls(message_text)
        
        if not twitter_urls:
            return
        
        for url in twitter_urls:
            await self.process_tweet_from_message(update, url, manual=False)

    async def process_tweet_from_message(self, update: Update, tweet_url: str, manual: bool = False):
        """Process a tweet URL from a message."""
        try:
            # Extract tweet ID
            tweet_id = self.automation.interaction_api.extract_tweet_id(tweet_url)
            if not tweet_id:
                if manual:
                    await update.message.reply_text("❌ Invalid Twitter/X URL")
                return
            
            # Check if already processed
            if tweet_id in self.processed_tweets:
                if manual:
                    await update.message.reply_text("ℹ️ This tweet has already been processed")
                return
            
            # Add random delay for natural behavior (only for auto mode)
            if not manual and len(self.processed_tweets) > 0:
                import random
                delay = random.randint(self.config.min_delay, self.config.max_delay)
                logger.info(f"Waiting {delay} seconds before processing tweet {tweet_id}")
                await asyncio.sleep(delay)
            
            # Send processing message
            processing_msg = await update.message.reply_text(f"🔄 Processing tweet: {tweet_url}")
            
            # Process the tweet
            if manual:
                # For manual processing, use auto-engage (realistic numbers)
                result = await self.automation.auto_engage_tweet(tweet_url)
            else:
                # For auto mode, use custom ranges
                import random
                likes = random.randint(self.config.default_likes_min, self.config.default_likes_max)
                retweets = random.randint(self.config.default_retweets_min, self.config.default_retweets_max)
                views = random.randint(self.config.default_views_min, self.config.default_views_max)
                
                result = await self.automation.process_tweet_url(tweet_url, likes, retweets, views)
            
            # Add to processed list
            self.processed_tweets.add(tweet_id)
            
            # Send result message
            if "error" in result:
                await processing_msg.edit_text(f"❌ Error: {result['error']}")
            else:
                actions = result.get("actions", {})
                success_text = f"""
✅ **Tweet Processed Successfully!**

🎯 **Tweet:** {tweet_url}

📊 **Actions Performed:**
• ❤️ Likes: {actions.get('likes', 0)}
• 🔄 Retweets: {actions.get('retweets', 0)}
• 👀 Views: {actions.get('views', 0)}

                """
                
                if result.get("final_stats"):
                    stats = result["final_stats"]
                    success_text += f"""
**Current Stats:**
• ❤️ Total Likes: {stats.get('likes', 0)}
• 🔄 Total Retweets: {stats.get('retweets', 0)}
• 💬 Replies: {stats.get('replies', 0)}
• 👀 Views: {stats.get('views', 0)}
                    """
                
                if result.get("errors"):
                    success_text += f"\n⚠️ Some actions failed: {len(result['errors'])} errors"
                
                await processing_msg.edit_text(success_text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error processing tweet {tweet_url}: {e}")
            if 'processing_msg' in locals():
                await processing_msg.edit_text(f"❌ Error processing tweet: {str(e)}")
            else:
                await update.message.reply_text(f"❌ Error processing tweet: {str(e)}")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")

    def run(self):
        """Run the Telegram bot."""
        if not self.config.telegram_bot_token:
            print("❌ TELEGRAM_BOT_TOKEN environment variable is required!")
            print("Set it with: export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
            return
        
        print("🚀 Starting Twitter/X Automation Telegram Bot...")
        print(f"🤖 Auto mode: {'ON' if self.config.auto_mode else 'OFF'}")
        print(f"🔧 Allowed groups: {self.config.allowed_groups if self.config.allowed_groups != [''] else 'All'}")
        print(f"👥 Allowed users: {self.config.allowed_users if self.config.allowed_users != [''] else 'All'}")
        
        # Create application
        application = Application.builder().token(self.config.telegram_bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("process", self.process_command))
        application.add_handler(CommandHandler("auto", self.auto_command))
        
        # Message handler for auto-processing
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        application.add_error_handler(self.error_handler)
        
        # Run the bot
        print("✅ Bot is running! Send /start to begin.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


async def test_automation():
    """Test function for automation without Telegram."""
    print("🧪 Testing Twitter automation...")
    
    api = API()
    automation = TwitterAutomation(api)
    
    # Test URL (replace with actual tweet URL)
    test_url = "https://x.com/elonmusk/status/1234567890"
    
    print(f"Testing with URL: {test_url}")
    result = await automation.auto_engage_tweet(test_url)
    
    print("Test result:")
    print(json.dumps(result, indent=2, default=str))


def main():
    """Main function."""
    config = TwitterBotConfig()
    bot = TwitterTelegramBot(config)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user.")
    except Exception as e:
        print(f"❌ Bot error: {e}")


if __name__ == "__main__":
    # Check if we want to run tests
    import sys
    if "--test" in sys.argv:
        asyncio.run(test_automation())
    else:
        main()