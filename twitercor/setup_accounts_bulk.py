#!/usr/bin/env python3
"""
Bulk Account Setup - Add multiple accounts quickly

This script adds all your Twitter/X accounts from the provided data.
"""

import asyncio
from twscrape import API


# Your account data
ACCOUNTS_DATA = [
    {
        "login": "RogerReed531051",
        "password": "lxp4e8cUQ9",
        "mail": "rohrbaugh1945@outlook.jp",
        "ct0": "619164659e2567538068260f1d5bba782fa943ff1f85836b10f35e756afc236b8d8aa096dc2685a0eaa1c4bb2e9d8851e561aab1a05e284eb66275c0d8866c8e70d9b0022047496142ed32b4c9ac367f",
        "auth_token": "8d1f71e63cc5d066f816aad83286b3a751e14428"
    },
    {
        "login": "CarterTimo41180",
        "password": "HuyoDnxQa6",
        "mail": "islamovbadajos31468@outlook.jp",
        "ct0": "ae615472161433c604bab5989e5fd245fc5573760705968e0c9fab2ce02260c4cebb4ea6e1131813079f0193d4cdacc0688d73f7edac2fa08d87c8f20c1bc9faf253ac6d68e91fea012c6c00e99f99a0",
        "auth_token": "58f84788562fa3b51ea6d20805d9fda8f536548f"
    },
    {
        "login": "JosephJame38932",
        "password": "8jx1uV52t6",
        "mail": "harvalakirtman23732@outlook.jp",
        "ct0": "b74c3fd5a245bf827ffb40e46d719b7889829d980a78b7601519a7831769b09100d7fbb50805894cbd942fd61019992f5e714cf7fc9e9680dc3933f38e4f5df354a2b548d05b53745c926c4ff0bec35a",
        "auth_token": "ed8a783c02c67ad5381586633c8143ae944758d4"
    },
    {
        "login": "MorganW29933",
        "password": "gGTiPyOrDp",
        "mail": "hollendonner39621@outlook.jp",
        "ct0": "cd0b7ca73c26ac36da05cfebca8d4b656a7b74c73959e3736bdd8bb7ee588c5b75169f98fb052c05b98cb9c073546cfc613e0b846ce51959c290ff36e3bbf83c9849f946b1b1c510f368f7769d81e56a",
        "auth_token": "1f51e2ffd7ad79aa858da6e9df9eb7796076bc75"
    },
    {
        "login": "AndrewCook55281",
        "password": "vDQbP0LVsi",
        "mail": "gamagechovanec61632@outlook.jp",
        "ct0": "6258be02538a2ea9af5b72968750f3dbf2aba1ceddb2edf26b304ea51af79594dc26b8a5ea68d732df5eea4ea3db15bf56709598dcb777e428bedd7b54c52345b5600675c501dfbbc35d8755d3258471",
        "auth_token": "055085f4798255b32534b67465a20eaa34afb64f"
    },
    {
        "login": "MichaelSco76203",
        "password": "k95xFGZXRP",
        "mail": "lamasters5595@outlook.jp",
        "ct0": "41defc799226e4f7c710fb6d192174b64926de690d77526ac1770882e74ec4b65173eeb77c14c8bea916d690ecab486eb978f2e77246c75a0aa7c4e0b71c4936439a93a789529c565148793b7cdd65e6",
        "auth_token": "f210c4d406833baa55944e8a7d1d22e3e0253bb1"
    },
    {
        "login": "StevenR33986",
        "password": "Vz19mWoGJe",
        "mail": "mcgeoghegan39505@outlook.jp",
        "ct0": "49fad821f393e5513563fbaf4d90be6ac85ff0dab136ca9def58447f9de1474c811e68af9bfb53902bdfdf48627d26528eeee83894bdce6a3403f8778f58d7e1f4bb947828b1bab9b83dc1a9901c8a58",
        "auth_token": "8e285eabc662e2895d5f927e1b9644a9daca5c16"
    },
    {
        "login": "AndrewTurn19385",
        "password": "ca7t2lBXx9",
        "mail": "griffawquery30116@outlook.jp",
        "ct0": "d5b65f3a7dc3d5c471f3439bb6081555ea38996050064ba113c6bd71affec603a00742fcaa7bb11824ce6e8a9bcbece717b4b5b2a7d865292e1c4a7c8e8352ad468baf747965485102ddf183e4cbe278",
        "auth_token": "dd2c5701ad0b79e925c143850f90a06403c7cf89"
    },
    {
        "login": "AdamHughes30000",
        "password": "IAQVbfhadB",
        "mail": "sherenaholcom80069@outlook.jp",
        "ct0": "5ca3ed418a0e6a16d697efdc8697127d869bdedbd3bf6034b02a0f259974af5a37563fbf6a28de910cdeac09aaa9728aeaf4e064836a274692a32c1c2da957ca25f13c9c79a373d976c1767d627bf008",
        "auth_token": "124808b6b3f0bb58e7aacd1ec883c0d98aacc130"
    },
    {
        "login": "jenkins_jo33844",
        "password": "7Lfm0aeilc",
        "mail": "dijoseph16824@outlook.jp",
        "ct0": "ea44ae98829cee571c7e5a635539dae7925bcc96f583b60b9ff1d40df8d2c271c82d23c752da73cf61b6144ec4d1b73bffb356460069139def33dfb7b94752c3eb83b09a4a17667d4c98549ce3ca8f15",
        "auth_token": "1192e3c0c84732be18d7e906f5d45c45925baec0"
    }
]


async def add_all_accounts():
    """Add all accounts to the system."""
    print("🚀 Bulk Account Setup")
    print("=" * 50)
    print(f"Adding {len(ACCOUNTS_DATA)} accounts...")
    print()
    
    api = API()
    success_count = 0
    failed_count = 0
    
    for i, account_data in enumerate(ACCOUNTS_DATA, 1):
        username = account_data["login"]
        password = account_data["password"]
        email = account_data["mail"]
        ct0 = account_data["ct0"]
        auth_token = account_data["auth_token"]
        
        # Build cookies string
        cookies = f"auth_token={auth_token}; ct0={ct0}"
        
        print(f"[{i}/{len(ACCOUNTS_DATA)}] Adding account: @{username}")
        
        try:
            await api.pool.add_account(
                username=username,
                password=password,
                email=email,
                email_password="dummy_email_pass",  # Using dummy since we have tokens
                cookies=cookies
            )
            print(f"✅ Successfully added @{username}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed to add @{username}: {e}")
            failed_count += 1
        
        print()
    
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"✅ Successfully added: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📈 Total: {len(ACCOUNTS_DATA)}")
    
    if success_count > 0:
        print(f"\n🎉 Great! You have {success_count} accounts ready for automation!")
        
        # Show accounts status
        accounts_info = await api.pool.accounts_info()
        print(f"\n📋 Account Status:")
        for info in accounts_info:
            status = "🟢 Active" if info["active"] else "🔴 Inactive"
            print(f"  @{info['username']}: {status}")


async def show_accounts_status():
    """Show status of all accounts."""
    print("📋 Current Accounts Status")
    print("=" * 50)
    
    api = API()
    accounts_info = await api.pool.accounts_info()
    
    if not accounts_info:
        print("❌ No accounts found in the system.")
        return
    
    active_count = sum(1 for acc in accounts_info if acc["active"])
    inactive_count = len(accounts_info) - active_count
    
    print(f"Total accounts: {len(accounts_info)}")
    print(f"🟢 Active: {active_count}")
    print(f"🔴 Inactive: {inactive_count}")
    print()
    
    for info in accounts_info:
        status = "🟢 Active" if info["active"] else "🔴 Inactive"
        req_count = info["total_req"]
        last_used = info["last_used"].strftime("%Y-%m-%d %H:%M") if info["last_used"] else "Never"
        
        print(f"@{info['username']:<20} {status:<12} Requests: {req_count:<5} Last used: {last_used}")


async def main():
    """Main function."""
    print("Welcome to Bulk Account Setup!")
    print()
    print("Options:")
    print("1. Add all accounts to system")
    print("2. Show current accounts status")
    print()
    
    choice = input("Enter your choice (1-2): ").strip()
    print()
    
    if choice == "1":
        await add_all_accounts()
    elif choice == "2":
        await show_accounts_status()
    else:
        print("❌ Invalid choice. Please run again and select 1 or 2.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")