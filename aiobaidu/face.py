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
from urllib.parse import urljoin

from .bceutil import get_canonical_querystring


class AipFace:
    """ Baidu Face Recognition Api wrapper"""

    _accessTokenUrl = '/oauth/2.0/token'
    _scope = 'brain_all_scope'

    _identifyUserUrl = '/rest/2.0/face/v2/identify'
    _matchUrl = '/rest/2.0/face/v2/match'

    _detectUrl = '/rest/2.0/face/v1/detect'

    _verifyUrl = '/rest/2.0/face/v2/verify'

    _addUrl = '/rest/2.0/face/v2/faceset/user/add'

    _updateUrl = '/rest/2.0/face/v2/faceset/user/update'

    _deleteUrl = '/rest/2.0/face/v2/faceset/user/delete'

    _getUrl = '/rest/2.0/face/v2/faceset/user/get'

    _getlistUrl = '/rest/2.0/face/v2/faceset/group/getlist'

    _getusersUrl = '/rest/2.0/face/v2/faceset/group/getusers'

    _adduserUrl = '/rest/2.0/face/v2/faceset/group/adduser'

    _deleteuserUrl = '/rest/2.0/face/v2/faceset/group/deleteuser'


    def __init__(self, appId, apiKey, secretKey, loop=None, host='https://aip.baidubce.com'):
        self._appId = appId
        self._apiKey = apiKey
        self._secretKey = secretKey
        self._timeout = 60.0
        self._host = host

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
        url = urljoin(self._host, url)

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
                    url, compress=False,
                    data=data, params=params, headers=authHeaders
                ),
                self._timeout,
                loop=self._loop
            )

            result = await resp.json()
        except Exception as exc:
            resp = None
            return {'error': exc}
        finally:
            if resp:
                await resp.release()

        return result

    async def _auth(self, refresh=False):
        if not refresh and self._authResponse:
            # check if token not expired
            tm = self._authResponse.get('time', 0) + \
                 int(self._authResponse.get('expires_in', 0)) - 30

            if tm > int(time.time()):
                return self._authResponse

        session = self.client_session()

        try:
            resp = await asyncio.wait_for(
                session.get(urljoin(self._host, self._accessTokenUrl),
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



    async def match(self, images, options=None):
        data = {'images': ','.join(images)}
        if options:
            data.update(options)

        return await self._request(self._matchUrl, data)

    async def close_session(self):
        """
            get rid of unclosed client session warning
        """
        await self._client_session.close()


    # Colm's Additions 02/10/2017
    async def detect(self, image, options=None):
        data = {'image': image}

		#'max_face_num' : numOfFaces, # optional param
                #'face_fields' : fieldstring}
        if options:
            data.update(options)

        return await self._request(self._detectUrl, data)


    async def verify(self, uId, image, groupId, options=None):
        data = {'uid': uId,  'image': image, 'group_id' : groupId}

                #'top_num' : topNum, 'ext_fields': extFields} # optional param
        if options:
            data.update(options)

        return await self._request(self._verifyUrl, data)



    async def get(self, uId, options=None):
        data = {'uid': uId}
        if options:
            data.update(options)

        return await self._request(self._getUrl, data)




    async def getlist(self, options=None):
        data = {}

	# 'start': start, 'end': end  # optional param

        if options:
            data.update(options)

        return await self._request(self._getlistUrl, data)


    async def getusers(self, groupId, options=None):
        data = {'group_id': groupId}

	# 'start': start, 'end': end  # optional param

        if options:
            data.update(options)

        return await self._request(self._getusersUrl, data)



    async def add(self, uId, userInfo, groupId, image, options=None):
        data = {'uid': uId, 'user_info': userInfo,
                'group_id': groupId, 'image': image}

        if options:
            data.update(options)
        return await self._request(self._addUrl, data)



    async def update(self, uId, image, userInfo, groupId, options=None):
        data = {'uid': uId, 'user_info': userInfo,
                'group_id': groupId, 'image': image} #,
                #'action_type': actionType}

        if options:
            data.update(options)

        return await self._request(self._updateUrl, data)



    async def delete(self, uId, groupId, options=None):
        data = {'uid': uId, 'group_id': groupId} 

        if options:
            data.update(options)

        return await self._request(self._deleteUrl, data)



    async def adduser(self, groupId, uId, srcGroupId, options=None):
        data = {'uid': uId, 'group_id': groupId,
                'src_group_id': srcGroupId}

        if options:
            data.update(options)

        return await self._request(self._adduserUrl, data)



    async def deleteuser(self, groupId, uId, options=None):
        data = {'uid': uId, 'group_id': groupId}

        if options:
            data.update(options)

        return await self._request(self._deleteuserUrl, data)



