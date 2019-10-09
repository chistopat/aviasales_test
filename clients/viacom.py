import asyncio
import logging
import typing

import aiohttp
import xml2py

import internal.models as models

DEFAULT_RETRY_TIMEOUT = 1
DEFAULT_RETRIES = 3

logger = logging.getLogger(__name__)
# todo: setup logs transfer to elk in production
logger.addHandler(logging.StreamHandler())


class BaseError(Exception):
    """Base exception class for all exceptions in this module."""


class RequestRetriesExceeded(BaseError):
    """Raises if _request failed and retried too many times"""


class BadRequestError(BaseError):
    """Raises when get 4XX and can not be processed"""


class ViacomClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.base_url = 'http://demo6010293.mockable.io'
        self.session = session

    async def _request(
            self,
            url,
            params=None,
            data=None,
            content_type=None,
            method=None,
            headers=None,
            timeout=DEFAULT_RETRY_TIMEOUT,
            retries=DEFAULT_RETRIES,
    ):
        headers = headers or {}
        headers['Content-Type'] = content_type or 'application/xml'
        retry_errors: typing.List[Exception] = []

        for attempt in range(retries + 1):
            if attempt > 0:
                await asyncio.sleep(timeout)
                logger.info(
                    'Retry #%d',
                    attempt,
                )

            try:
                response = await self._single_request(
                    method=method,
                    url=url,
                    data=data,
                    headers=headers,
                    params=params,
                )
            except aiohttp.ClientConnectionError as err:
                retry_errors.append(err)
                logger.warning(
                    'Cannot connect to viacom API: %s',
                    err,
                )
                continue

            if response.status >= 500:
                logger.warning(
                    'Internal error at viacom API, http code %s',
                    response.status,
                )
                continue
            elif 400 <= response.status < 500:
                logger.warning(
                    'Error at viacom API, code %s'
                    'response: %s',
                    response.status,
                    (await response.text()),
                )
                raise BadRequestError(
                    'Unexpected error while requesting {}'.format(url),
                )

            return await response.text()

        raise RequestRetriesExceeded(
            'Viacom API request failed: {}'.format(retry_errors),
        )

    async def _single_request(
            self,
            url,
            params=None,
            data=None,
            method=None,
            headers=None,
    ) -> aiohttp.ClientResponse:
        return await self.session.request(
            method=method,
            url=self.base_url + url,
            json=data,
            headers=headers,
            params=params,
        )

    async def fetch_tickets(self, round_trip: bool = False):
        url = '/viacom-oneway'
        if round_trip:
            url = '/viacom-roundtrips'
        xml = await self._request(url=url, method='GET')
        obj = xml2py.dict_loads(xml, attrib_prefix='', text_key='value')
        response = models.AirFareSearchResponse(obj['AirFareSearchResponse'])
        return response.prised_itineraries
