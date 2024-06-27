from httpx import AsyncClient
import pytest
import json
from schemes.chat import GroupChatScheme
from db.models.message import InfoMessageTypes
from httpx_ws import aconnect_ws

tokens = []


@pytest.mark.anyio
async def test_creating_chats(ac: AsyncClient):
    global tokens
    req1 = await ac.post(f'/auth/login', params={'email': "1@example.com"})
    req2 = await ac.get(f'/auth/email-login', params={'email': "1@example.com", 'code': req1.json()})
    tokens.append(req2.json())
    async with aconnect_ws(f'ws://test/chat/connect/ws?token={tokens[0]["access_token"]}', ac) as ws:
        # async with aiofiles.open('test_files/test_pic.jpg', 'rb') as f:
        #     avatar = base64.b64encode(await f.read()).decode('utf-8')
        req1 = await ac.post(f'/chat/create-group-chat',
                             headers={"Authorization": f'Bearer {tokens[0]["access_token"]}'},
                             json=GroupChatScheme(users_ids=[2], name='1').dict())
        assert req1.status_code == 200
        while True:
            data = await ws.receive_json()
            if data != {'type': 'subscribe', 'pattern': None, 'channel': 'chat_1', 'data': 1}:
                assert json.loads(data['data'])['msg']['info_type'] == InfoMessageTypes.NEW_CHAT.value
                break
