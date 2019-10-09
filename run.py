import aiohttp
import asyncio
import logging

import clients.viacom as viacom

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


async def main():
    async with aiohttp.ClientSession() as session:
        client = viacom.ViacomClient(session)
        xml = await client.fetch_tickets()
        print(xml)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
