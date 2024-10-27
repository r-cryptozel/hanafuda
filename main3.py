import asyncio
import json
from datetime import datetime
from colorama import init, Fore, Style
import aiohttp

init(autoreset=True)
api_url = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"

with open("token.txt", "r") as file:
    access_tokens = [line.strip() for line in file if line.strip()]

headers = {
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

def log_with_time(message):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

async def colay(session, url, method, payload_data=None):
    async with session.request(method, url, headers=headers, json=payload_data) as response:
        if response.status != 200:
            raise Exception(f'HTTP error! Status: {response.status}')
        return await response.json()

async def refresh_access_token(session, refresh_token):
    api_key = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"
    async with session.post(
        f'https://securetoken.googleapis.com/v1/token?key={api_key}',
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f'grant_type=refresh_token&refresh_token={refresh_token}'
    ) as response:
        if response.status != 200:
            raise Exception("Failed to refresh access token")
        data = await response.json()
        return data.get('access_token')

async def handle_grow(session, refresh_token):
    new_access_token = await refresh_access_token(session, refresh_token)
    headers['authorization'] = f'Bearer {new_access_token}'

    info_query = {
        "query": "query CurrentUser { currentUser { id sub name iconPath depositCount totalPoint evmAddress { userId address } inviter { id name } } }",
        "operationName": "CurrentUser"
    }
    info = await colay(session, api_url, 'POST', info_query)

    balance = info['data']['currentUser']['totalPoint']
    log_with_time(f"{Fore.GREEN}Current Points: {balance}{Style.RESET_ALL}")

    grow_query = {
        "query": "query GetGardenForCurrentUser { getGardenForCurrentUser { gardenStatus { growActionCount } } }",
        "operationName": "GetGardenForCurrentUser"
    }
    profile = await colay(session, api_url, 'POST', grow_query)

    grow = profile['data']['getGardenForCurrentUser']['gardenStatus']['growActionCount']
    log_with_time(f"{Fore.GREEN}Grow actions left: {grow}{Style.RESET_ALL}")

    while grow > 0:
        action_query = {
            "query": "mutation issueGrowAction { issueGrowAction }",
            "operationName": "issueGrowAction"
        }
        mine = await colay(session, api_url, 'POST', action_query)
        reward = mine['data']['issueGrowAction']
        balance += reward
        grow -= 1
        log_with_time(f"{Fore.GREEN}Reward: {reward} | Updated Points: {balance} | Grow actions left: {grow}{Style.RESET_ALL}")
        await asyncio.sleep(1)

        commit_query = {
            "query": "mutation commitGrowAction { commitGrowAction }",
            "operationName": "commitGrowAction"
        }
        await colay(session, api_url, 'POST', commit_query)

async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            for refresh_token in access_tokens:
                await handle_grow(session, refresh_token)
            log_with_time(f"{Fore.RED}All accounts have been processed. Cooling down for 10 minutes...{Style.RESET_ALL}")
            await asyncio.sleep(600)

if __name__ == '__main__':
    log_with_time(Fore.YELLOW + "Starting in Grow mode only..." + Style.RESET_ALL)
    asyncio.run(main())
