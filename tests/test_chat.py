import asyncio

from httpx import AsyncClient
import pytest
import json
from schemes.chat import GroupChatScheme, DirectChatScheme
from schemes.message import WSMessageTypes
from db.models.message import InfoMessageTypes, MessageTypes
from httpx_ws import aconnect_ws

tokens = []


async def second_user_ws(token, ac):
    async with aconnect_ws(f'ws://test/chat/connect/ws?token={token}', ac) as ws:
        while True:
            check2 = asyncio.all_tasks()
            check3 = asyncio.get_running_loop()
            json_ws = (await ws.receive_json())['data']
            if json_ws and type(json_ws) != int:
                data = json.loads(json_ws)
                print(data)
                await ws.close()
                return data


@pytest.mark.anyio
async def test_creating_group_chats(ac: AsyncClient):
    global tokens
    req1 = await ac.post(f'/auth/login', params={'email': "1@example.com"})
    req2 = await ac.get(f'/auth/email-login', params={'email': "1@example.com", 'code': req1.json()})
    tokens.append(req2.json())
    req1 = await ac.post(f'/auth/login', params={'email': "2@example.com"})
    req2 = await ac.get(f'/auth/email-login', params={'email': "2@example.com", 'code': req1.json()})
    tokens.append(req2.json())
    task = asyncio.create_task(second_user_ws(tokens[1]["access_token"], ac))
    async with aconnect_ws(f'ws://test/chat/connect/ws?token={tokens[0]["access_token"]}', ac) as ws:
        # async with aiofiles.open('test_files/test_pic.jpg', 'rb') as f:
        #     avatar = base64.b64encode(await f.read()).decode('utf-8')
        req1 = await ac.post(f'/chat/create-group-chat',
                             headers={"Authorization": f'Bearer {tokens[0]["access_token"]}'},
                             json=GroupChatScheme(users_ids=[2], name='1').dict())
        assert req1.status_code == 200
        while True:
            if (json_ws := (await ws.receive_json())['data']) and type(json_ws) != int:
                data = json.loads(json_ws)
                if 'msg' in data:
                    assert data['msg']['info_type'] == InfoMessageTypes.NEW_CHAT.value
                    res = await task
                    assert res['msg']['info_type'] == InfoMessageTypes.NEW_CHAT.value
                    break
        await ws.close()
        tokens = []
@pytest.mark.anyio
async def test_creating_direct_chats(ac: AsyncClient):
    global tokens
    req1 = await ac.post(f'/auth/login', params={'email': "1@example.com"})
    req2 = await ac.get(f'/auth/email-login', params={'email': "1@example.com", 'code': req1.json()})
    tokens.append(req2.json())
    req1 = await ac.post(f'/auth/login', params={'email': "2@example.com"})
    req2 = await ac.get(f'/auth/email-login', params={'email': "2@example.com", 'code': req1.json()})
    tokens.append(req2.json())
    task1 = asyncio.create_task(second_user_ws(tokens[1]["access_token"], ac))
    #task2 = asyncio.create_task(second_user_ws(tokens[1]["access_token"], ac))
    async with aconnect_ws(f'ws://test/chat/connect/ws?token={tokens[0]["access_token"]}', ac) as ws:
        req1 = await ac.post(f'/chat/create-direct-chat',
                             headers={"Authorization": f'Bearer {tokens[0]["access_token"]}'},
                             json=DirectChatScheme(user_id=2).dict())
        assert req1.status_code == 200


        req = await ws.send_json({"text": "hi", "chat_id": 2,  "message_type": WSMessageTypes.CREATE_MESSAGE.value})
        # # await asyncio.sleep(2)
        #res1 = await task1
        # res2 = await task2
        #
        # print(req)
        #
        # print(res1, res2)
        # assert res1['msg']['type'] == MessageTypes.DEFAULT.value
        # assert res2['msg']['type'] == MessageTypes.DEFAULT.value




        while True:
            check2 = asyncio.all_tasks()
            check3 = asyncio.get_running_loop()
            json_ws = await ws.receive_json()
            print(json_ws, tokens)
            if json_ws['data'] and type(json_ws['data']) != int:
                data = json.loads(json_ws['data'])
                if 'msg' in data:
                    print(data)

                    assert data['msg']['type'] == MessageTypes.DEFAULT.value
                    res1 = await task1
                    assert res1['msg']['type'] == MessageTypes.DEFAULT.value
                    break
        await ws.close()

    # res1 = await task1
    # res2 = await task2
    #
    #
    # print(res1, res2)
    # assert res1['msg']['type'] == MessageTypes.DEFAULT.value
    # assert res2['msg']['type'] == MessageTypes.DEFAULT.value