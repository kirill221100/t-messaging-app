from httpx import AsyncClient
import pytest
from schemes.user import EditUserScheme
import aiofiles, base64
from tests.conftest import tokens


@pytest.mark.anyio
async def test_my_profile(ac: AsyncClient):
    req1 = await ac.get(f'/user/my-profile', headers={"Authorization": f'Bearer {tokens[0]}'})
    assert req1.status_code == 200


@pytest.mark.anyio
async def test_edit_profile(ac: AsyncClient):
    username = '11'
    async with aiofiles.open('test_files/test_pic.jpg', 'rb') as f:
        avatar = base64.b64encode(await f.read()).decode('utf-8')
    description = 'description'
    req1 = await ac.put('/user/edit-profile', headers={"Authorization": f'Bearer {tokens[0]}'},
                        json=EditUserScheme(username=username, avatar=avatar, description=description).dict())
    assert req1.status_code == 200

    profile = req1.json()['profile']
    assert profile['username'] == username
    assert profile['avatar'] is not None
    assert profile['description'] == description

    req1 = await ac.put('/user/edit-profile', headers={"Authorization": f'Bearer {tokens[0]}'},
                        json=EditUserScheme(username=username).dict())
    assert req1.status_code == 409
    assert req1.json()['detail'] == "Username already exists"


@pytest.mark.anyio
async def test_edit_email(ac: AsyncClient):
    email = '11@example.com'
    req1 = await ac.patch('/user/edit-email', headers={"Authorization": f'Bearer {tokens[0]}'}, params={'email': email})
    assert req1.status_code == 200
    code = req1.json()

    req2 = await ac.get(f'/user/verify-email-change', headers={"Authorization": f'Bearer {tokens[0]}'},
                        params={'code': code})
    assert req2.status_code == 200
    user = await ac.get(f'/user/my-profile', headers={"Authorization": f'Bearer {tokens[0]}'})
    assert user.json()['email'] == email

    req2 = await ac.get(f'/user/verify-email-change', headers={"Authorization": f'Bearer {tokens[0]}'},
                        params={'code': 24234242424})
    assert req2.status_code == 400


