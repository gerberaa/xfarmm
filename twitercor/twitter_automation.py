#!/usr/bin/env python3
"""
Extended API for Twitter/X interactions (likes, retweets, views)

This module extends the basic twscrape API to include interaction functionality.
"""

import asyncio
import json
import re
import random
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from twscrape.api import API, GQL_URL, GQL_FEATURES
from twscrape.queue_client import QueueClient
from twscrape.utils import encode_params
from twitter_actions import TwitterActionsAPI
from fast_twitter_actions import FastTwitterActionsAPI


class TwitterInteractionAPI:
    def __init__(self, api: API):
        self.api = api
        self.pool = api.pool
        self.debug = api.debug
        self.proxy = api.proxy
        self.actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=self.proxy)
        # Завантажуємо проксі для акаунтів
        self.account_proxies = self._load_account_proxies()
    
    def _load_account_proxies(self) -> Dict[str, str]:
        """Load proxy assignments for accounts."""
        import os
        import json
        
        proxy_file = "proxies.json"
        if os.path.exists(proxy_file):
            try:
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def get_account_proxy(self, username: str) -> Optional[str]:
        """Get proxy for specific account."""
        return self.account_proxies.get(username, None)
    
    def create_actions_api_for_account(self, username: str) -> TwitterActionsAPI:
        """Create TwitterActionsAPI instance with account's proxy."""
        account_proxy = self.get_account_proxy(username)
        if self.debug and account_proxy:
            print(f"🌐 Using proxy for @{username}: {account_proxy}")
        return TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)

    def extract_tweet_id(self, url: str) -> Optional[str]:
        """Extract tweet ID from Twitter URL."""
        # Various Twitter URL formats:
        # https://x.com/username/status/1234567890
        # https://twitter.com/username/status/1234567890
        # https://x.com/i/status/1234567890
        patterns = [
            r'(?:twitter\.com|x\.com)/.+/status/(\d+)',
            r'(?:twitter\.com|x\.com)/i/status/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If it's just a number, assume it's already a tweet ID
        if url.isdigit():
            return url
            
        return None

    async def like_tweet(self, tweet_id: str, username: str = None) -> bool:
        """Like a tweet using a specific account or random account."""
        try:
            # Створюємо окремий екземпляр TwitterActionsAPI з проксі для конкретного акаунта
            if username:
                account_proxy = self.get_account_proxy(username)
                actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                actions = self.actions
                
            return await actions.like_tweet(tweet_id)
        except Exception as e:
            print(f"Error liking tweet {tweet_id}: {e}")
            return False

    async def unlike_tweet(self, tweet_id: str, username: str = None) -> bool:
        """Unlike a tweet using a specific account or random account."""
        try:
            if username:
                account_proxy = self.get_account_proxy(username)
                actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                actions = self.actions
                
            return await actions.unlike_tweet(tweet_id)
        except Exception as e:
            print(f"Error unliking tweet {tweet_id}: {e}")
            return False

    async def retweet(self, tweet_id: str, username: str = None) -> bool:
        """Retweet a tweet using a specific account or random account."""
        try:
            if username:
                account_proxy = self.get_account_proxy(username)
                actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                actions = self.actions
                
            return await actions.retweet(tweet_id)
        except Exception as e:
            print(f"Error retweeting tweet {tweet_id}: {e}")
            return False

    async def view_tweet(self, tweet_id: str, username: str = None) -> bool:
        """View a tweet using a specific account."""
        try:
            # Для перегляду достатньо просто отримати детальну інформацію про твіт
            if username:
                account_proxy = self.get_account_proxy(username)
                # Створюємо тимчасовий API з проксі акаунта
                api = API(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                api = self.api
                
            # Отримуємо твіт через TweetDetail API (це рахується як перегляд)
            try:
                # Використовуємо той самий метод що і get_tweet_stats
                tweet_data = await api._gql_item(
                    "_8aYOgEDz35BrBcBal1-_w/TweetDetail",
                    {"focalTweetId": str(tweet_id), "with_rux_injections": True,
                     "includePromotedContent": True, "withCommunity": True,
                     "withQuickPromoteEligibilityTweetFields": True,
                     "withBirdwatchNotes": True, "withVoice": True,
                     "withV2Timeline": True}
                )
                
                if tweet_data and tweet_data.status_code == 200:
                    return True
                else:
                    return False
                    
            except Exception:
                return False
                
        except Exception as e:
            if self.debug:
                print(f"Error viewing tweet {tweet_id}: {e}")
            return False
        """Unretweet a tweet using a specific account or random account."""
        try:
            if username:
                account_proxy = self.get_account_proxy(username)
                actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                actions = self.actions
                
            return await actions.unretweet(tweet_id)
        except Exception as e:
            print(f"Error unretweeting tweet {tweet_id}: {e}")
            return False

    async def view_tweet(self, tweet_id: str, username: str = None) -> bool:
        """View a tweet (increase view count) using a specific account or random account."""
        try:
            # Getting tweet details counts as a view
            tweet = await self.api.tweet_details(int(tweet_id))
            return tweet is not None
            
        except Exception as e:
            print(f"Error viewing tweet {tweet_id}: {e}")
            
        return False

    async def get_tweet_stats(self, tweet_id: str) -> Optional[Dict]:
        """Get current stats of a tweet."""
        try:
            tweet = await self.api.tweet_details(int(tweet_id))
            if tweet:
                return {
                    "likes": tweet.likeCount,
                    "retweets": tweet.retweetCount,
                    "replies": tweet.replyCount,
                    "views": tweet.viewCount if hasattr(tweet, 'viewCount') else 0,
                    "quotes": tweet.quoteCount if hasattr(tweet, 'quoteCount') else 0
                }
        except Exception as e:
            print(f"Error getting tweet stats {tweet_id}: {e}")
            
        return None


class TwitterAutomation:
    """Main automation class for managing multiple accounts and interactions."""
    
    def __init__(self, api: API, fast_mode: bool = True):
        self.api = api
        self.interaction_api = TwitterInteractionAPI(api)
        self.fast_mode = fast_mode
        
    def create_actions_api_for_account(self, username: str):
        """Create an API instance with the specific proxy for the account."""
        account_proxy = self.interaction_api.get_account_proxy(username)
        
        # Використовуємо стандартний TwitterActionsAPI який працював з проксі
        return TwitterActionsAPI(self.api.pool, debug=self.api.debug, proxy=account_proxy)
        
    async def get_active_accounts(self) -> List[str]:
        """Get list of active account usernames."""
        accounts_info = await self.api.pool.accounts_info()
        return [acc["username"] for acc in accounts_info if acc["active"]]

    async def process_tweet_url(self, tweet_url: str, likes_count: int = None, 
                               retweets_count: int = None, views_count: int = None) -> Dict:
        """Process a tweet URL with specified engagement numbers."""
        
        tweet_id = self.interaction_api.extract_tweet_id(tweet_url)
        if not tweet_id:
            return {"error": "Invalid tweet URL"}
        
        print(f"🎯 Processing tweet: {tweet_url}")
        print(f"📊 Tweet ID: {tweet_id}")
        
        # Get initial stats
        initial_stats = await self.interaction_api.get_tweet_stats(tweet_id)
        if initial_stats:
            print(f"📈 Initial stats: {initial_stats}")
        
        active_accounts = await self.get_active_accounts()
        if not active_accounts:
            return {"error": "No active accounts available"}
        
        print(f"👥 Available accounts: {len(active_accounts)}")
        
        results = {
            "tweet_id": tweet_id,
            "tweet_url": tweet_url,
            "initial_stats": initial_stats,
            "actions": {
                "likes": 0,
                "retweets": 0,
                "views": 0
            },
            "errors": []
        }
        
        # Shuffle accounts for more realistic behavior
        shuffled_accounts = active_accounts.copy()
        random.shuffle(shuffled_accounts)
        
        # Initialize account lists
        likes_accounts = []
        retweet_accounts = []
        
        # Process likes with parallel execution (max 5 concurrent)
        if likes_count and likes_count > 0:
            print(f"❤️ Adding {likes_count} likes (parallel processing with max 5 concurrent)...")
            likes_accounts = shuffled_accounts[:min(likes_count, len(shuffled_accounts))]
            
            # Виконуємо лайки паралельно групами по 5
            semaphore = asyncio.Semaphore(5)  # Максимум 5 одночасних операцій
            
            async def process_like(account, index):
                async with semaphore:
                    try:
                        # Додаємо затримку перед першою дією для реалістичності
                        if index > 0:
                            delay = random.randint(2, 8)
                            await asyncio.sleep(delay)
                        
                        # Створюємо окремий API з проксі для цього акаунта
                        actions_api = self.create_actions_api_for_account(account)
                        success = await actions_api.like_tweet(tweet_id)
                        
                        if success:
                            results["actions"]["likes"] += 1
                            print(f"✅ @{account} liked the tweet")
                            return True
                        else:
                            print(f"❌ @{account} failed to like the tweet")
                            results["errors"].append(f"Like failed for @{account}")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Error with @{account} liking: {e}")
                        results["errors"].append(f"Like error for @{account}: {e}")
                        return False
            
            # Запускаємо всі лайки паралельно
            like_tasks = [process_like(account, i) for i, account in enumerate(likes_accounts)]
            await asyncio.gather(*like_tasks, return_exceptions=True)
            
            # Додаємо затримку між групами операцій
            if retweets_count or views_count:
                delay = random.randint(5, 15)
                print(f"⏳ Waiting {delay} seconds before next operation group...")
                await asyncio.sleep(delay)
        
        # Process retweets with parallel execution (max 5 concurrent)
        if retweets_count and retweets_count > 0:
            print(f"🔄 Adding {retweets_count} retweets (parallel processing with max 5 concurrent)...")
            # Use different accounts for retweets
            used_accounts = likes_accounts if likes_count else []
            remaining_accounts = [acc for acc in shuffled_accounts if acc not in used_accounts]
            retweet_accounts = remaining_accounts[:min(retweets_count, len(remaining_accounts))]
            
            # Виконуємо ретвіти паралельно групами по 5
            semaphore = asyncio.Semaphore(5)
            
            async def process_retweet(account, index):
                async with semaphore:
                    try:
                        # Додаємо затримку для реалістичності
                        if index > 0:
                            delay = random.randint(3, 12)
                            await asyncio.sleep(delay)
                        
                        # Створюємо окремий API з проксі для цього акаунта
                        actions_api = self.create_actions_api_for_account(account)
                        success = await actions_api.retweet(tweet_id)
                        
                        if success:
                            results["actions"]["retweets"] += 1
                            print(f"✅ @{account} retweeted the tweet")
                            return True
                        else:
                            print(f"❌ @{account} failed to retweet the tweet")
                            results["errors"].append(f"Retweet failed for @{account}")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Error with @{account} retweeting: {e}")
                        results["errors"].append(f"Retweet error for @{account}: {e}")
                        return False
            
            # Запускаємо всі ретвіти паралельно
            retweet_tasks = [process_retweet(account, i) for i, account in enumerate(retweet_accounts)]
            await asyncio.gather(*retweet_tasks, return_exceptions=True)
            
            # Додаємо затримку перед переглядами
            if views_count:
                delay = random.randint(3, 10)
                print(f"⏳ Waiting {delay} seconds before views...")
                await asyncio.sleep(delay)
        
        # Process views with parallel execution (max 5 concurrent)
        if views_count and views_count > 0:
            print(f"👀 Adding {views_count} views (parallel processing with max 5 concurrent)...")
            # All accounts can view
            used_accounts_set = set(likes_accounts + retweet_accounts)
            view_accounts = [acc for acc in shuffled_accounts if acc not in used_accounts_set][:min(views_count, len(shuffled_accounts))]
            
            # Виконуємо перегляди паралельно групами по 5
            semaphore = asyncio.Semaphore(5)
            
            async def process_view(account, index):
                async with semaphore:
                    try:
                        # Додаємо мінімальну затримку для переглядів
                        if index > 0:
                            delay = random.randint(1, 5)
                            await asyncio.sleep(delay)
                        
                        # Створюємо окремий API з проксі для цього акаунта
                        actions_api = self.create_actions_api_for_account(account)
                        success = await actions_api.view_tweet(tweet_id)
                        
                        if success:
                            results["actions"]["views"] += 1
                            print(f"✅ @{account} viewed the tweet")
                            return True
                        else:
                            print(f"❌ @{account} failed to view the tweet")
                            results["errors"].append(f"View failed for @{account}")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Error with @{account} viewing: {e}")
                        results["errors"].append(f"View error for @{account}: {e}")
                        return False
                        return False
            
            # Запускаємо всі перегляди паралельно
            view_tasks = [process_view(account, i) for i, account in enumerate(view_accounts)]
            await asyncio.gather(*view_tasks, return_exceptions=True)
        
        # Get final stats
        final_stats = await self.interaction_api.get_tweet_stats(tweet_id)
        if final_stats:
            print(f"📊 Final stats: {final_stats}")
            results["final_stats"] = final_stats
        
        print(f"✅ Processing complete!")
        print(f"📈 Actions performed: {results['actions']}")
        
        # Додаткова статистика
        total_errors = len(results['errors'])
        total_attempts = likes_count + retweets_count + views_count
        success_rate = ((results['actions']['likes'] + results['actions']['retweets'] + results['actions']['views']) / total_attempts * 100) if total_attempts > 0 else 0
        
        print(f"📊 Success rate: {success_rate:.1f}%")
        if total_errors > 0:
            print(f"⚠️ Errors: {total_errors}")
        
        return results

    async def auto_engage_tweet(self, tweet_url: str) -> Dict:
        """Automatically engage with a tweet using realistic numbers."""
        
        active_accounts = await self.get_active_accounts()
        total_accounts = len(active_accounts)
        
        if total_accounts == 0:
            return {"error": "No active accounts available"}
        
        # Calculate realistic engagement numbers
        # Views: 60-80% of accounts
        views_count = random.randint(int(total_accounts * 0.6), int(total_accounts * 0.8))
        
        # Likes: 20-40% of accounts
        likes_count = random.randint(int(total_accounts * 0.2), int(total_accounts * 0.4))
        
        # Retweets: 5-15% of accounts
        retweets_count = random.randint(int(total_accounts * 0.05), int(total_accounts * 0.15))
        
        print(f"🤖 Auto-engaging with realistic numbers:")
        print(f"👥 Total accounts: {total_accounts}")
        print(f"👀 Views: {views_count}")
        print(f"❤️ Likes: {likes_count}")
        print(f"🔄 Retweets: {retweets_count}")
        
        return await self.process_tweet_url(tweet_url, likes_count, retweets_count, views_count)