# -*- coding: utf-8 -*-

import aiohttp
import asyncio

class AipFace:
    """ Baidu Face Recognition Api wrapper"""
    
    _accessTokenUrl = 'https://aip.baidubce.com/oauth/2.0/token'
    _scope = 'brain_all_scope'

    _identifyUserUrl = 'https://aip.baidubce.com/rest/2.0/face/v2/identify'

    def __init__(self, appId, apiKey, secretKey, loop=None):
        self._appId = appId
        self._apiKey = apiKey
        self._secretKey = secretKey
        self._timeout = 60.0

        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._authResponse = None
        self._isCloudUser, self._client_session = None, None

    def client_session(self):
        if self._client_session is None or self._client_session.closed:
            connector = aiohttp.TCPConnector(
                verify_ssl=False, loop=self._loop
            )
            self._client_session = aiohttp.ClientSession(
                connector=connector, loop=self._loop
            )

        return self._client_session

    async def _auth(self, refresh=False):
        if not refresh and self._token:
            # check if token not expired
            tm = self._authResponse.get('time', 0) +\
                int(self._authResponse.get('expires_in', 0)) - 30

            if tm > int(time.time()):
                return self._authResponse
            
        self._authResponse = await asyncio.wait_for(
            session.get(self._accessTokenUrl,
                params={
                    'grant_type': 'client_credentials',
                    'client_id': self._apiKey,
                    'client_secret': self._secretKey,
                }
            ),
            self._timeout,
            loop=self._loop
        )
        return self._authResponse

    async def identifyUser(self, groupId, image, options=None):
        session = self.client_session()

        response = await asyncio.wait_for(
            session.post(self._identifyUserUrl, compress=False,
                data={
                    'group_id': groupId, 'image': image
                },
            ),
            self._timeout,
            loop=self._loop
        )


