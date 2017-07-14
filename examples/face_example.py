# -*- coding: utf-8 -*-

import asyncio
import aiobaidu

loop = asyncio.get_event_loop()

face = aiobaidu.AipFace()

loop.run_until_complete()
loop.close()
