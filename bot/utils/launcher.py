import os
import glob
import asyncio
import argparse
from itertools import cycle
from typing import Tuple

from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions

import json


start_text = """
██████╗  ██████╗  ██████╗ ███████╗██╗  ██╗ ██████╗ ██╗   ██╗███████╗███████╗██████╗ ███████╗███████╗
██╔══██╗██╔═══██╗██╔════╝ ██╔════╝██║  ██║██╔═══██╗██║   ██║██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝
██║  ██║██║   ██║██║  ███╗███████╗███████║██║   ██║██║   ██║███████╗█████╗  ██████╔╝█████╗  █████╗  
██║  ██║██║   ██║██║   ██║╚════██║██╔══██║██║   ██║██║   ██║╚════██║██╔══╝  ██╔══██╗██╔══╝  ██╔══╝  
██████╔╝╚██████╔╝╚██████╔╝███████║██║  ██║╚██████╔╝╚██████╔╝███████║███████╗██║  ██║███████╗██║     
╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝     
                                                                                                    

Select an action:

    1. Run clicker
    2. Create session
"""

global tg_clients


def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies

def get_proxies_V2() -> json:
    proxies = None
    with open(file="proxies.json", encoding="utf-8-sig") as file:
        proxies = json.load(file)
        return proxies
    

async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    len_sessions = len(get_session_names())
    len_proxies = len(get_proxies_V2())
    logger.info(f"Detected {len_sessions} sessions | {len_proxies} proxies")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2"]:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break

    if action == 1:
        # Gets proxies from proxy.json file
        await run_tasks_V2()

    elif action == 2:
        await register_sessions()




async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)

async def run_tasks_V2():
    tg_clients = await get_tg_clients()
    proxies = get_proxies_V2()

    client_with_proxy = []

    for tg_client in tg_clients:
        proxy = proxies.get(tg_client.name)
        if proxy:
            proxy = Proxy.from_str(proxy=proxy.strip())

            proxy_client_pair = (proxy, tg_client)
            client_with_proxy.append(proxy_client_pair)
        else:
            logger.critical(f"Could not find proxy for session: {tg_client.name}")
            exit(1)
    
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=client_proxy[1],
                proxy=client_proxy[0].as_url,
            )
        )
        for client_proxy in client_with_proxy
    ]

    await asyncio.gather(*tasks)