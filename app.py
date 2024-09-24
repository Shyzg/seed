from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from faker import Faker
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    UnauthorizedError
)
from telethon.functions import messages, account
from telethon.sync import TelegramClient
from telethon.types import InputBotAppShortName, AppWebViewResultUrl
from requests import (
    JSONDecodeError,
    RequestException,
    Session
)
from urllib.parse import unquote
import asyncio
import json
import os
import sys

class Seed:
    def __init__(self) -> None:
        self.faker = Faker()
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'elb.seeddao.org',
            'Origin': 'https://cf.seeddao.org',
            'Pragma': 'no-cache',
            'Referer': 'https://cf.seeddao.org/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }
        self.api_id = 26326768
        self.api_hash = 'ff06b969a60cdb700f6e965de8e34e68'

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    async def generate_query(self, session: str):
        try:
            async with TelegramClient(session=f'sessions/{session}', api_id=self.api_id, api_hash=self.api_hash) as client:
                try:
                    await client.connect()
                    me = await client.get_me()
                    username = me.username if me.username else self.faker.user_name()
                    if me.last_name is None or not '🌱SEED' in me.last_name:
                        await client(account.UpdateProfileRequest(last_name='🌱SEED'))
                except (AuthKeyUnregisteredError, UnauthorizedError, UserDeactivatedBanError, UserDeactivatedError) as e:
                    raise e

                webapp_response: AppWebViewResultUrl = await client(messages.RequestAppWebViewRequest(
                    peer='seed_coin_bot',
                    app=InputBotAppShortName(bot_id=await client.get_input_entity('seed_coin_bot'), short_name='app'),
                    platform='ios',
                    write_allowed=True,
                    start_param='6094625904'
                ))
                query = unquote(string=webapp_response.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
                await client.disconnect()
                return (query, username)
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {session} Unexpected Error While Generating Query With Telethon: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def generate_queries(self, sessions):
        tasks = [self.generate_query(session) for session in sessions]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def profile(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/profile'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers) as response:
                response.raise_for_status()
                return True
        except (Exception, JSONDecodeError, RequestException):
            return False

    async def profile2(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/profile2'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                profile2 = response.json()['data']
                if not profile2['give_first_egg']:
                    return await self.give_first_egg(query=query)
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Profile: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Profile: {str(e)} ]{Style.RESET_ALL}")

    async def give_first_egg(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/give-first-egg'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers) as response:
                give_first_egg = response.json()['data']
                if give_first_egg['status'] == 'in-inventory':
                    self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {give_first_egg['type']} From Give First Egg ]{Style.RESET_ALL}")
                    return await self.complete_egg_hatch(query=query, egg_id=give_first_egg['id'])
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Already Received Give First Egg ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Give First Egg: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Give First Egg: {str(e)} ]{Style.RESET_ALL}")

    async def balance_profile(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/profile/balance'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                return response.json()['data']
        except (JSONDecodeError, RequestException) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Profile Balance: {str(e)} ]{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Profile Balance: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def upgrade_mining_seed(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/seed/mining-speed/upgrade'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers) as response:
                response.raise_for_status()
                return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade Mining Seed ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Not Enough Seed To Upgrade Mining Seed ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Upgrade Mining Seed: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Upgrade Mining Seed: {str(e)} ]{Style.RESET_ALL}")

    async def upgrade_storage_size(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/seed/storage-size/upgrade'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers) as response:
                response.raise_for_status()
                return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade Storage Size ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Not Enough Seed To Upgrade Storage Size ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Upgrade Storage Size: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Upgrade Storage Size: {str(e)} ]{Style.RESET_ALL}")

    async def me_worms(self, query: str, sell_price_legendary: int, sell_price_epic: int, sell_price_rare: int):
        url = 'https://elb.seeddao.org/api/v1/worms/me?page=1'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                me_worms = response.json()['data']
                if me_worms['items']:
                    for data in me_worms['items']:
                        if data['status'] == 'successful':
                            if not data['on_market']:
                                if data['type'] == 'legendary':
                                    await self.add_market_item(query=query, worm_id=data['id'], sell_price=sell_price_legendary)
                                elif data['type'] == 'epic':
                                    await self.add_market_item(query=query, worm_id=data['id'], sell_price=sell_price_epic)
                                elif data['type'] == 'rare':
                                    await self.add_market_item(query=query, worm_id=data['id'], sell_price=sell_price_rare)
                            else:
                                if data['type'] == 'legendary' and data['price'] != int(sell_price_legendary * 1000000000):
                                    await self.cancel_market_item(query=query, worm_id=data['id'], sell_price=sell_price_rare, market_id=data['market_id'], worm_type=data['type'])
                                elif data['type'] == 'epic' and data['price'] != int(sell_price_legendary * 1000000000):
                                    await self.cancel_market_item(query=query, worm_id=data['id'], sell_price=sell_price_rare, market_id=data['market_id'], worm_type=data['type'])
                                elif data['type'] == 'rare' and data['price'] != int(sell_price_legendary * 1000000000):
                                    await self.cancel_market_item(query=query, worm_id=data['id'], sell_price=sell_price_rare, market_id=data['market_id'], worm_type=data['type'])
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Me Worms: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Me Worms: {str(e)} ]{Style.RESET_ALL}")

    async def add_market_item(self, query: str, worm_id: str, sell_price: int):
        url = 'https://elb.seeddao.org/api/v1/market-item/add'
        data = json.dumps({'worm_id':worm_id,'price':sell_price * 1000000000})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                add_market_item = response.json()['data']
                if add_market_item['status'] == 'on-sale':
                    return self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ Successfully Add Worm {add_market_item['worm_type']} To Market ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Price Net {add_market_item['price_net'] / 1000000000} ]{Style.RESET_ALL}"
                    )
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Add Market Item: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Add Market Item: {str(e)} ]{Style.RESET_ALL}")

    async def cancel_market_item(self, query: str, worm_id: str, sell_price: int, market_id: str, worm_type: str):
        url = f'https://elb.seeddao.org/api/v1/market-item/{market_id}/cancel'
        data = json.dumps({'id':market_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Updating Price For Worm {worm_type} ]{Style.RESET_ALL}")
                await self.add_market_item(query=query, worm_id=worm_id, sell_price=sell_price)
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Add Market Item: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Add Market Item: {str(e)} ]{Style.RESET_ALL}")

    async def me_egg(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/egg/me?page=1'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                me_egg = response.json()['data']
                if not me_egg['items']: return
                for egg in me_egg['items']:
                    await self.complete_egg_hatch(query=query, egg_id=egg['id'])
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Me Egg: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Me Egg: {str(e)} ]{Style.RESET_ALL}")

    async def complete_egg_hatch(self, query: str, egg_id: str):
        url = 'https://elb.seeddao.org/api/v1/egg-hatch/complete'
        data = json.dumps({'egg_id':egg_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                complete_egg_hatch = response.json()['data']
                if complete_egg_hatch['status'] == 'in-inventory':
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {complete_egg_hatch['type']} From Egg Hatch ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 404:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Egg Not Existed ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Complete Egg Hatch: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Complete Egg Hatch: {str(e)} ]{Style.RESET_ALL}")

    async def login_bonuses(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/login-bonuses'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers) as response:
                response.raise_for_status()
                login_bonuses = response.json()['data']
                return self.print_timestamp(
                    f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {login_bonuses['amount'] / 1000000000} From Login Bonuses ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT}[ Day {login_bonuses['no']} ]{Style.RESET_ALL}"
                )
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ You\'ve Already Claim Login Bonuses ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Login Bonuses: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Login Bonuses: {str(e)} ]{Style.RESET_ALL}")

    async def get_streak_reward(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/streak-reward'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                streak_reward = response.json()['data']
                if not streak_reward: return
                for data in streak_reward:
                    if data['status'] == 'created':
                        await self.streak_reward(query=query, streak_reward_ids=data['id'])
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Streak Reward: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Streak Reward: {str(e)} ]{Style.RESET_ALL}")

    async def streak_reward(self, query: str, streak_reward_ids: str):
        url = 'https://elb.seeddao.org/api/v1/streak-reward'
        data = json.dumps({'streak_reward_ids':[streak_reward_ids]})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                streak_reward = response.json()['data']
                for data in streak_reward:
                    if data['status'] == 'received':
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Claimed Streak Reward ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 404:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Streak Reward Not Existed ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Streak Reward: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Streak Reward: {str(e)} ]{Style.RESET_ALL}")

    async def worms(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/worms'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                return response.json()['data']
        except (JSONDecodeError, RequestException) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Worms: {str(e)} ]{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Worms: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def catch_worms(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/worms/catch'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers) as response:
                response.raise_for_status()
                catch_worms = response.json()['data']
                if catch_worms['status'] == 'successful':
                    return self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {catch_worms['type']} From Catch Worms ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Reward {catch_worms['reward'] / 1000000000} ]{Style.RESET_ALL}"
                    )
                elif catch_worms['status'] == 'failed':
                    return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Failed To Catch {catch_worms['type']} Worms ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                error_catch_worms = e.response.json()
                if error_catch_worms['message'] == 'worm already caught':
                    return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Worm Already Caught ]{Style.RESET_ALL}")
            elif e.response.status_code == 404:
                error_catch_worms = e.response.json()
                if error_catch_worms['message'] == 'worm disappeared':
                    return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Worm Disappeared ]{Style.RESET_ALL}")
                elif error_catch_worms['message'] == 'worm not found':
                    return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Worm Not Found ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Catch Worms: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Catch Worms: {str(e)} ]{Style.RESET_ALL}")

    async def claim_seed(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/seed/claim'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers) as response:
                response.raise_for_status()
                claim_seed = response.json()['data']
                return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {claim_seed['amount'] / 1000000000} From Seeding ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Claim Seed Too Early ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Seed: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Seed: {str(e)} ]{Style.RESET_ALL}")

    async def is_leader_bird(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/bird/is-leader'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                is_leader_bird = response.json()['data']
                if is_leader_bird['status'] == 'hunting':
                    if datetime.now().astimezone() >= datetime.fromisoformat(is_leader_bird['hunt_end_at'].replace('Z', '+00:00')).astimezone():
                        await self.complete_bird_hunt(query=query, bird_id=is_leader_bird['id'], task_level=is_leader_bird['task_level'])
                    else:
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Bird Hunt Can Be Complete At {datetime.fromisoformat(is_leader_bird['hunt_end_at'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                elif is_leader_bird['status'] == 'in-inventory':
                    if is_leader_bird['happiness_level'] < 10000 or is_leader_bird['energy_level'] < is_leader_bird['energy_max']:
                        await self.bird_happiness(query=query, bird_id=is_leader_bird['id'])
                        await self.me_all_worms(query=query, bird_id=is_leader_bird['id'], task_level=is_leader_bird['task_level'])
                    elif is_leader_bird['happiness_level'] >= 10000 and is_leader_bird['energy_level'] >= is_leader_bird['energy_max']:
                        await self.start_bird_hunt(query=query, bird_id=is_leader_bird['id'], task_level=is_leader_bird['task_level'])
        except (JSONDecodeError, RequestException) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Is Leader Bird: {str(e)} ]{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Is Leader Bird: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def me_all_worms(self, query: str, bird_id: str, task_level: int):
        url = 'https://elb.seeddao.org/api/v1/worms/me-all'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                me_all_worms = response.json()['data']
                if not me_all_worms: return
                for data in me_all_worms:
                    if data['status'] == 'successful' and (data['type'] == 'common' or data['type'] == 'uncommon'):
                        await self.bird_feed(query=query, bird_id=bird_id, worm_ids=data['id'])
                return await self.start_bird_hunt(query=query, bird_id=bird_id, task_level=task_level)
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Me All Worms: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Me All Worms: {str(e)} ]{Style.RESET_ALL}")

    async def bird_happiness(self, query: str, bird_id):
        url = 'https://elb.seeddao.org/api/v1/bird-happiness'
        data = json.dumps({'bird_id':bird_id,'happiness_rate':10000})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                bird_happiness = response.json()['data']
                if bird_happiness['happiness_level'] >= 10000:
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Your Bird Is Happy ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Bird Happiness: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Bird Happiness: {str(e)} ]{Style.RESET_ALL}")

    async def bird_feed(self, query: str, bird_id: str, worm_ids: str):
        url = 'https://elb.seeddao.org/api/v1/bird-feed'
        data = json.dumps({'bird_id':bird_id,'worm_ids':[worm_ids]})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                bird_feed = response.json()
                if bird_feed['data']['energy_level'] <= bird_feed['data']['energy_max']:
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Feed Bird Successfully ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ The Bird Is Full And Cannot Eat Any More ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Bird Feed: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Bird Feed: {str(e)} ]{Style.RESET_ALL}")

    async def start_bird_hunt(self, query: str, bird_id: str, task_level: int):
        url = 'https://elb.seeddao.org/api/v1/bird-hunt/start'
        data = json.dumps({'bird_id':bird_id,'task_level':task_level})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                start_bird_hunt = response.json()['data']
                if start_bird_hunt['status'] == 'hunting':
                    self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Your Bird Is Hunting ]{Style.RESET_ALL}")
                    
                    if datetime.now().astimezone() >= datetime.fromisoformat(start_bird_hunt['hunt_end_at'].replace('Z', '+00:00')).astimezone():
                        return await self.complete_bird_hunt(query=query, bird_id=start_bird_hunt['id'], task_level=start_bird_hunt['task_level'])

                    return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Bird Hunt Can Be Complete At {datetime.fromisoformat(start_bird_hunt['hunt_end_at'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Start Hunting Time Is Not Over Yet ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Bird Hunt: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Bird Hunt: {str(e)} ]{Style.RESET_ALL}")

    async def complete_bird_hunt(self, query: str, bird_id: str, task_level: int):
        url = 'https://elb.seeddao.org/api/v1/bird-hunt/complete'
        data = json.dumps({'bird_id':bird_id,'task_level':task_level})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                complete_bird_hunt = response.json()['data']
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {complete_bird_hunt['seed_amount'] / 1000000000} From Bird Hunt ]{Style.RESET_ALL}")
                return await self.is_leader_bird(query=query)
        except (JSONDecodeError, RequestException) as e:
            if e.response.status_code == 400:
                return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Complete Hunting Time Is Not Over Yet ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Complete Bird Hunt: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Complete Bird Hunt: {str(e)} ]{Style.RESET_ALL}")

    async def progresses_tasks(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/tasks/progresses'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                progresses_tasks = response.json()['data']
                for task in progresses_tasks:
                    if task['task_user'] is None or not task['task_user']['completed']:
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task['name']} Isn\'t Complete ]{Style.RESET_ALL}")
                        await self.tasks(query=query, task_id=task['id'])
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Progresses Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Progresses Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def tasks(self, query: str, task_id: str):
        url = f'https://elb.seeddao.org/api/v1/tasks/{task_id}'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers) as response:
                response.raise_for_status()
                return True
        except (Exception, JSONDecodeError, RequestException):
            return False

    async def detail_member_guild(self, query: str):
        url = 'https://elb.seeddao.org/api/v1/guild/member/detail'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            with Session().get(url=url, headers=headers) as response:
                response.raise_for_status()
                detail_member_guild = response.json()
                if detail_member_guild['data'] is None or detail_member_guild['data']['guild_id'] is None:
                    return await self.join_guild(query=query, guild_id='b4480be6-0f4a-42d2-8f58-bc087daa33c3')
                elif detail_member_guild['data']['guild_id'] != 'b4480be6-0f4a-42d2-8f58-bc087daa33c3':
                    return await self.leave_guild(query=query, guild_id=detail_member_guild['data']['guild_id'])
        except (JSONDecodeError, RequestException) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Detail Member Guild: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Detail Member Guild: {str(e)} ]{Style.RESET_ALL}")

    async def join_guild(self, query: str, guild_id: str):
        url = 'https://elb.seeddao.org/api/v1/guild/join'
        data = json.dumps({'guild_id':guild_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                return True
        except (Exception, JSONDecodeError, RequestException):
            return False

    async def leave_guild(self, query: str, guild_id: str):
        url = 'https://elb.seeddao.org/api/v1/guild/leave'
        data = json.dumps({'guild_id':guild_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            with Session().post(url=url, headers=headers, data=data) as response:
                response.raise_for_status()
                return await self.join_guild(query=query, guild_id='b4480be6-0f4a-42d2-8f58-bc087daa33c3')
        except (Exception, JSONDecodeError, RequestException):
            return False

    async def perform_is_leader(self, query, name):
        self.print_timestamp(
            f"{Fore.WHITE + Style.BRIGHT}[ Home/Is Leader ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
        )
        await self.is_leader_bird(query=query)

    async def perform_boost(self, query, name):
        self.print_timestamp(
            f"{Fore.WHITE + Style.BRIGHT}[ Boost ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
        )
        await self.upgrade_mining_seed(query=query)
        await self.upgrade_storage_size(query=query)

    async def main(self):
        while True:
            try:
                sessions = [file.replace('.session', '') for file in os.listdir('sessions/') if file.endswith('.session')]
                if not sessions:
                    return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Session Files Found In The Folder! Please Make Sure There Are '*.session' Files In The Folder. ]{Style.RESET_ALL}")
                with open('config.json', 'r') as config_file:
                    config = json.load(config_file)
                accounts = await self.generate_queries(sessions)
                total_balance = 0.0
                restart_times = []

                for (query, name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.profile(query=query)
                    await self.profile2(query=query)
                    await self.claim_seed(query=query)
                    worms = await self.worms(query=query)
                    if worms is not None:
                        if datetime.now().astimezone() >= datetime.fromisoformat(worms['created_at'].replace('Z', '+00:00')).astimezone():
                            if not worms['is_caught']:
                                await self.catch_worms(query=query)
                                restart_times.append(datetime.fromisoformat(worms['next_worm'].replace('Z', '+00:00')).astimezone().timestamp())
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Next Worms Can Be Catch At {datetime.fromisoformat(worms['next_worm'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                            else:
                                restart_times.append(datetime.fromisoformat(worms['next_worm'].replace('Z', '+00:00')).astimezone().timestamp())
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Next Worms Can Be Catch At {datetime.fromisoformat(worms['next_worm'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                        else:
                            restart_times.append(datetime.fromisoformat(worms['created_at'].replace('Z', '+00:00')).astimezone().timestamp())
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Next Worms Can Be Catch At {datetime.fromisoformat(worms['created_at'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                    await self.me_worms(query=query, sell_price_legendary=config['sell_price_legendary'], sell_price_epic=config['sell_price_epic'], sell_price_rare=config['sell_price_rare'])
                    await self.me_egg(query=query)

                tasks = [self.perform_is_leader(query, name) for (query, name) in accounts]
                await asyncio.gather(*tasks)

                for (query, name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Earn ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.login_bonuses(query=query)
                    await self.get_streak_reward(query=query)
                    await self.progresses_tasks(query=query)

                tasks = [self.perform_boost(query, name) for (query, name) in accounts]
                await asyncio.gather(*tasks)

                for (query, name) in accounts:
                    await self.detail_member_guild(query=query)
                    balance_profile = await self.balance_profile(query=query)
                    total_balance += float(balance_profile / 1000000000) if balance_profile else 0.0

                if restart_times:
                    wait_times = [catch_worms - datetime.now().astimezone().timestamp() for catch_worms in restart_times if catch_worms > datetime.now().astimezone().timestamp()]
                    if wait_times:
                        sleep_time = min(wait_times)
                    else:
                        sleep_time = 15 * 60
                else:
                    sleep_time = 15 * 60

                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ Total Account {len(accounts)} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Balance {total_balance} ]{Style.RESET_ALL}"
                )
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=sleep_time)).strftime('%x %X %Z')} ]{Style.RESET_ALL}")

                await asyncio.sleep(sleep_time)
                self.clear_terminal()
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        init(autoreset=True)
        seed = Seed()
        asyncio.run(seed.main())
    except (ValueError, IndexError, FileNotFoundError) as e:
        seed.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)