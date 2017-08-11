# -*- coding: utf-8 -*-

import asyncio
import aiobaidu

loop = asyncio.get_event_loop()

BAIDU = {
    'APP_ID': '???',
    'API_KEY': '???',
    'SECRET_KEY': '???'
}

# Important: images should be in base64 format
test_img1 = ""
test_img2 = ""
test_img3 = ""

async def main(loop):
    face = aiobaidu.AipFace(
        BAIDU['APP_ID'], BAIDU['API_KEY'], BAIDU['SECRET_KEY'],
        loop=loop
    )

    resp = await face.identifyUser("group3", test_img1)
    print("face.identifyUser Response =>")
    print(resp)

    resp = await face.match([test_img2, test_img1, test_img3])
    print("face.match Response =>")
    print(resp)
    await face.close_session()

loop.run_until_complete(main(loop))
loop.close()
