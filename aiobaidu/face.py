# -*- coding: utf-8 -*-

import aiohttp
import asyncio

import time
import hmac
import hashlib
import datetime

from urllib.parse import urlencode
from urllib.parse import quote
from urllib.parse import urlparse

from .bceutil import get_canonical_querystring

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
        self._authResponse, self._client_session = None, None

    def client_session(self):
        if self._client_session is None or self._client_session.closed:
            connector = aiohttp.TCPConnector(
                verify_ssl=False, loop=self._loop
            )
            self._client_session = aiohttp.ClientSession(
                connector=connector, loop=self._loop
            )

        return self._client_session

    def _getParams(self):
        return {
            'aipSdk': 'python',
            'aipVersion': '1_3_4',
            'access_token': self._authResponse['access_token']
        }

    def _getAuthHeaders(self, method, url, params=None):
        # UTC timestamp
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        urlResult = urlparse(url)
        host = urlResult.hostname
        path = urlResult.path
        version, expire, signatureHeaders = '1', '1800', 'host'

        # 1 Generate SigningKey
        val = "bce-auth-v%s/%s/%s/%s" % (version, self._apiKey, timestamp, expire)
        signingKey = hmac.new(self._secretKey.encode('utf-8'), val.encode('utf-8'),
                        hashlib.sha256
                    ).hexdigest()

        # 2 Generate CanonicalRequest
        # 2.1 Genrate CanonicalURI
        canonicalUri = quote(path)
        # 2.2 Generate CanonicalURI: not used here
        # 2.3 Generate CanonicalHeaders: only include host here
        canonicalHeaders = 'host:%s' % quote(host).strip()
        # 2.4 Generate CanonicalRequest
        canonicalRequest = '%s\n%s\n%s\n%s' % (
            method.upper(),
            canonicalUri,
            get_canonical_querystring(params),
            canonicalHeaders
        )

        # 3 Generate Final Signature
        signature = hmac.new(signingKey.encode('utf-8'), canonicalRequest.encode('utf-8'),
                        hashlib.sha256
                    ).hexdigest()
        authorization = 'bce-auth-v%s/%s/%s/%s/%s/%s' % (version, self._apiKey, timestamp,
                            expire, signatureHeaders, signature
                        )

        return {
            'Host': host,
            'x-bce-date': timestamp,
            'accept': '*/*',
            'authorization': authorization,
        }

    async def _request(self, url, data):
        await self._auth()
        session = self.client_session()

        # validate auth response
        if 'error' in self._authResponse:
            await session.close()
            return self._authResponse
        elif not self._authResponse:
            return {"error": "aiobaidu_internal_error"}

        params = self._getParams()
        authHeaders = self._getAuthHeaders("POST", url, params=params)

        try:
            resp = await asyncio.wait_for(
                session.post(
                    self._identifyUserUrl, compress=False,
                    data=data, params=params, headers=authHeaders
                ),
                self._timeout,
                loop=self._loop
            )

            result = await resp.json()
        except Exception as exc:
            return {'error': exc}
        finally:
            await resp.release()

        return result

    async def _auth(self, refresh=False):
        if not refresh and self._authResponse:
            # check if token not expired
            tm = self._authResponse.get('time', 0) +\
                int(self._authResponse.get('expires_in', 0)) - 30

            if tm > int(time.time()):
                return self._authResponse
            
        session = self.client_session()

        try:
            resp = await asyncio.wait_for(
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
            self._authResponse = await resp.json()
            self._authResponse['time'] = int(time.time())
        except Exception as exc:
            print(exc)
        finally:
            await resp.release()

        return self._authResponse

    async def identifyUser(self, groupId, image, options=None):
        data = {'group_id': groupId, 'image': image}

        if options:
            data.update(options)

        return await self._request(self._identifyUserUrl, data)
