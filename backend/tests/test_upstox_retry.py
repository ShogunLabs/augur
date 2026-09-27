import asyncio

import httpx
import pytest

from app.integrations import upstox


def _success_payload(ipo_id: str) -> dict:
    return {
        "status": "success",
        "data": {
            "id": ipo_id,
            "symbol": "FOO",
            "name": "Foo IPO",
            "status": "open",
            "issue_type": "regular",
        },
    }


def _handler_factory(codes):
    """Return a request handler that serves the next status code in `codes`.

    Each call pops the next code; once exhausted it serves 200.
    """

    iterator = iter(codes)

    def handler(request: httpx.Request) -> httpx.Response:
        try:
            code = next(iterator)
        except StopIteration:
            code = 200
        if code != 200:
            return httpx.Response(code, request=request)
        return httpx.Response(200, json=_success_payload(request.url.path), request=request)

    return handler


@pytest.mark.anyio
async def test_retry_succeeds_after_429(monkeypatch):
    # Force the backoff to be instant so the test doesn't sleep.
    monkeypatch.setattr(upstox, "_retry_delay", lambda attempt, exc=None: 0.0)
    monkeypatch.setattr(upstox.asyncio, "sleep", lambda *_a, **_k: _noop())

    transport = httpx.MockTransport(_handler_factory([429, 429, 200]))
    async with httpx.AsyncClient(transport=transport) as client:
        async def _get():
            res = await client.get("https://api.upstox.com/v2/ipos/x-ipo")
            res.raise_for_status()
            return res

        result = await upstox.with_retry_async(_get)

    assert result.status_code == 200
    assert result.json()["data"]["id"] == "/v2/ipos/x-ipo"


@pytest.mark.anyio
async def test_non_retryable_4xx_is_not_retried(monkeypatch):
    monkeypatch.setattr(upstox, "_retry_delay", lambda attempt, exc=None: 0.0)

    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(404, request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        async def _get():
            res = await client.get("https://api.upstox.com/v2/ipos/missing")
            res.raise_for_status()
            return res

        with pytest.raises(httpx.HTTPStatusError):
            await upstox.with_retry_async(_get)

    assert len(calls) == 1


async def _noop():
    return None