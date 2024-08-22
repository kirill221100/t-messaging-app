from httpx import AsyncClient
import pytest
from schemes.auth import RegisterScheme


@pytest.mark.anyio
async def test_registration(ac: AsyncClient):
    req1 = await ac.post('/auth/email-reg-send', json=RegisterScheme(email="7@example.com", username='7').dict())
    assert req1.status_code == 200
    req2 = await ac.get('/auth/email-reg', params={'email': "7@example.com", 'code': req1.json()})
    assert req2.status_code == 200

    req2 = await ac.get('/auth/email-reg', params={'email': "7@example.com", 'code': 2323424234534543563535})
    assert req2.status_code == 400
    assert req2.json()['detail'] == 'Incorrect code'

    req3 = await ac.post('/auth/email-reg-send', json=RegisterScheme(email="7@example.com", username='77').dict())
    assert req3.status_code == 409
    assert req3.json()['detail'] == 'Email already registered'

    req4 = await ac.post('/auth/email-reg-send', json=RegisterScheme(email="8@example.com", username='3').dict())
    assert req4.status_code == 409
    assert req4.json()['detail'] == 'Username already registered'


@pytest.mark.anyio
async def test_login(ac: AsyncClient):
    req1 = await ac.post('/auth/login', params={'email': "1@example.com"})
    assert req1.status_code == 200

    req2 = await ac.get('/auth/email-login', params={'email': "1@example.com", 'code': req1.json()})
    assert req2.status_code == 200

    req2 = await ac.get('/auth/email-login', params={'email': "1@example.com", 'code': 234242424234})
    assert req2.status_code == 400
    assert req2.json()['detail'] == 'Incorrect code'

    req1 = await ac.post('/auth/login', params={'email': "121212121212@example.com"})
    assert req1.status_code == 404
    assert req1.json()['detail'] == 'No such user'


@pytest.mark.anyio
async def test_refresh_token(ac: AsyncClient):
    req1 = await ac.post('/auth/login', params={'email': "1@example.com"})
    assert req1.status_code == 200

    req2 = await ac.get('/auth/email-login', params={'email': "1@example.com", 'code': req1.json()})
    assert req2.status_code == 200

    req1 = await ac.get('/auth/refresh-token', params={'token': req2.json()['refresh_token']})
    assert req1.status_code == 200

    req1 = await ac.get('/auth/refresh-token', params={'token': 'efefefefef'})
    assert req1.status_code == 401
    assert req1.json()['detail'] == 'Invalid refresh token'

