from httpx import AsyncClient
import pytest
from schemes.user import EditUserScheme
import aiofiles, base64, json

tokens = {}


@pytest.mark.anyio
async def test_my_profile(ac: AsyncClient):
    req1 = await ac.post(f'/auth/login', params={'email': "1@example.com"})
    assert req1.status_code == 200
    req2 = await ac.get(f'/auth/email-login', params={'email': "1@example.com", 'code': req1.json()})
    assert req2.status_code == 200
    global tokens
    tokens = req2.json()
    req1 = await ac.get(f'/user/my-profile', headers={"Authorization": f'Bearer {tokens["access_token"]}'})
    assert req1.status_code == 200


@pytest.mark.anyio
async def test_edit_profile(ac: AsyncClient):
    username = '11'
    email = '11@example.com'
    async with aiofiles.open('test_files/test_pic.jpg', 'rb') as f:
        avatar = base64.b64encode(await f.read()).decode('utf-8')
    description = 'description'
    req1 = await ac.put(f'/user/edit-profile', headers={"Authorization": f'Bearer {tokens["access_token"]}'},
                        json=EditUserScheme(username=username, email=email, avatar=avatar, description=description).dict())
    assert req1.status_code == 200
    profile = req1.json()['profile']
    code = req1.json()['code']
    assert profile['username'] == username
    assert profile['avatar'] != None
    assert profile['description'] == description
    req2 = await ac.get(f'/user/email-change', headers={"Authorization": f'Bearer {tokens["access_token"]}'},
                        params={'code': code})
    assert req2.status_code == 200
    user = await ac.get(f'/user/my-profile', headers={"Authorization": f'Bearer {tokens["access_token"]}'})
    assert user.json()['email'] == email
    req1 = await ac.put(f'/user/edit-profile', headers={"Authorization": f'Bearer {tokens["access_token"]}'},
                        json=EditUserScheme(username=username).dict())
    assert req1.status_code == 409
    req2 = await ac.get(f'/user/email-change', headers={"Authorization": f'Bearer {tokens["access_token"]}'},
                        params={'code': 2323232323323})
    assert req2.status_code == 400
