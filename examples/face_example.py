# -*- coding: utf-8 -*-

import asyncio
import aiobaidu

loop = asyncio.get_event_loop()

BAIDU = {
    'APP_ID': '???',
    'API_KEY': '???',
    'SECRET_KEY': '???'
}

test_img = "base64-img"

async def main(loop):
    face = aiobaidu.AipFace(
        BAIDU['APP_ID'], BAIDU['API_KEY'], BAIDU['SECRET_KEY'],
        loop=loop
    )

    resp = await face.identifyUser("group3", test_img)
    print(resp)

loop.run_until_complete(main(loop))
loop.close()
