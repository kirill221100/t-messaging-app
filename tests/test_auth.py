from httpx import AsyncClient
import pytest
from schemes.auth import RegisterScheme

tokens = {}


@pytest.mark.anyio
async def test_registration(ac: AsyncClient):
    req1 = await ac.post(f'/auth/email-reg-send', json=RegisterScheme(email="1@example.com", username='1').dict())
    assert req1.status_code == 200
    req2 = await ac.get(f'/auth/email-reg', params={'email': "1@example.com", 'code': req1.json()})
    assert req2.status_code == 200
    req2 = await ac.get(f'/auth/email-reg', params={'email': "1@example.com", 'code': 2323424234534543563535})
    assert req2.status_code == 400
    req3 = await ac.post(f'/auth/email-reg-send', json=RegisterScheme(email="1@example.com", username='2').dict())
    assert req3.status_code == 409
    req4 = await ac.post(f'/auth/email-reg-send', json=RegisterScheme(email="2@example.com", username='1').dict())
    assert req4.status_code == 409
    req1 = await ac.post(f'/auth/email-reg-send', json=RegisterScheme(email="2@example.com", username='2').dict())
    assert req1.status_code == 200
    req2 = await ac.get(f'/auth/email-reg', params={'email': "2@example.com", 'code': req1.json()})
    assert req2.status_code == 200


@pytest.mark.anyio
async def test_login(ac: AsyncClient):
    req1 = await ac.post(f'/auth/login', params={'email': "1@example.com"})
    assert req1.status_code == 200
    req2 = await ac.get(f'/auth/email-login', params={'email': "1@example.com", 'code': req1.json()})
    assert req2.status_code == 200
    global tokens
    tokens = req2.json()
    req2 = await ac.get(f'/auth/email-login', params={'email': "1@example.com", 'code': 234242424234})
    assert req2.status_code == 400
    req1 = await ac.post(f'/auth/login', params={'email': "121212121212@example.com"})
    assert req1.status_code == 404


@pytest.mark.anyio
async def test_refresh_token(ac: AsyncClient):
    global tokens
    req1 = await ac.get(f'/auth/refresh-token', params={'token': tokens['refresh_token']})
    assert req1.status_code == 200
