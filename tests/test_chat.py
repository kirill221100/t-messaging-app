import asyncio
import aiofiles
from httpx import AsyncClient
import pytest
import json
import string
import base64
from schemes.chat import GroupChatScheme, DirectChatScheme
from redis_utils.redis import message_manager
import random
import datetime
from schemes.message import WSMessageTypes
from db.models.message import InfoMessageTypes, MessageTypes
from httpx_ws import aconnect_ws
from httpx_ws._exceptions import WebSocketDisconnect
from tests.conftest import tokens, test_session
from wsproto.frame_protocol import CloseReason
from sqlalchemy import select
from db.models.message import Message
from config import config


async def second_user_ws(token, ac):
    async with aconnect_ws(f'ws://test/chat/connect/ws?token={token}', ac) as ws:
        while True:
            json_ws = (await ws.receive_json())['data']
            if json_ws and type(json_ws) != int:
                data = json.loads(json_ws)
                await ws.close()
                return data


async def upload_test(filename, route, key, mimetype, token, ac, params=None):
    async with aiofiles.open(filename, 'rb') as f:
        file = await f.read()
        rand_name = ''.join(random.choices(string.ascii_letters, k=10))
        return await ac.post(route,
                             headers={"Authorization": f'Bearer {token}'},
                             files={key: (rand_name, file, mimetype)}, params=params)


async def exception_ws_request(route, data, ac: AsyncClient):
    async with aconnect_ws(route, ac) as ws:
        await ws.send_json(data)
        try:
            while True:
                await ws.receive_json()
        except WebSocketDisconnect as er:
            await ws.close()
            return er


@pytest.mark.anyio
async def test_creating_group_chats(ac: AsyncClient):
    print("!!!!test_creating_group_chats!!!!")
    task = asyncio.create_task(second_user_ws(tokens[1], ac))
    async with aconnect_ws(f'ws://test/chat/connect/ws?token={tokens[0]}', ac) as ws:
        async with aiofiles.open('test_files/test_pic.jpg', 'rb') as f:
            avatar = base64.b64encode(await f.read()).decode('utf-8')
        req1 = await ac.post(f'/chat/create-group-chat',
                             headers={"Authorization": f'Bearer {tokens[0]}'},
                             json=GroupChatScheme(users_ids=[2], name='1', avatar=avatar).dict())
        assert req1.status_code == 200
        assert req1.json()['avatar'] is not None
        while True:
            if (json_ws := (await ws.receive_json())['data']) and type(json_ws) != int:
                data = json.loads(json_ws)
                if 'msg' in data:
                    assert data['msg']['info_type'] == InfoMessageTypes.NEW_CHAT.value
                    res = await task
                    assert res['msg']['info_type'] == InfoMessageTypes.NEW_CHAT.value
                    break
        await ws.close()
        req1 = await ac.post(f'/chat/create-group-chat',
                             headers={"Authorization": f'Bearer {tokens[0]}'},
                             json=GroupChatScheme(users_ids=[121212], name='2').dict())
        assert req1.status_code == 404
        assert req1.json()['detail'] == "You are trying to add non-existent user"


@pytest.mark.anyio
async def test_creating_direct_chats(ac: AsyncClient):
    print("!!!!test_creating_direct_chats!!!!")
    task1 = asyncio.create_task(second_user_ws(tokens[1], ac))
    async with aconnect_ws(f'ws://test/chat/connect/ws?token={tokens[0]}', ac) as ws:
        req1 = await ac.post(f'/chat/create-direct-chat',
                             headers={"Authorization": f'Bearer {tokens[0]}'},
                             json=DirectChatScheme(user_id=2).dict())
        assert req1.status_code == 200
        await ws.send_json(
            {"text": "hi", "chat_id": req1.json()['id'], "message_type": WSMessageTypes.CREATE_MESSAGE.value})
        while True:
            json_ws = await ws.receive_json()
            if json_ws['data'] and type(json_ws['data']) != int:
                data = json.loads(json_ws['data'])
                if 'msg' in data:
                    assert data['msg']['type'] == MessageTypes.DEFAULT.value
                    res1 = await task1
                    assert res1['msg']['type'] == MessageTypes.DEFAULT.value
                    break
        await ws.close()
    req1 = await ac.post(f'/chat/create-direct-chat',
                         headers={"Authorization": f'Bearer {tokens[0]}'},
                         json=DirectChatScheme(user_id=2).dict())
    assert req1.status_code == 409
    assert req1.json()['detail'] == "Such direct chat already exists"


@pytest.mark.anyio
async def test_creating_messages(ac: AsyncClient):
    print("!!!!test_creating_messages!!!!")
    req2 = await upload_test('test_files/test_vid.mp4', '/message/upload-videos-for-message', "videos", "video/mp4",
                             tokens[0], ac, {"chat_id": 1})
    assert req2.status_code == 200

    req1 = await upload_test('test_files/test_pic.jpg', '/message/upload-images-for-message', "images", "image/jpeg",
                             tokens[0], ac, {"chat_id": 1})
    assert req1.status_code == 200


    async with aconnect_ws(f'ws://test/chat/connect/ws?token={tokens[0]}', ac) as ws:
        task1 = asyncio.create_task(second_user_ws(tokens[1], ac))
        await asyncio.sleep(2)
        await ws.send_json(
            {"text": "hi", "chat_id": 1, "message_type": WSMessageTypes.CREATE_MESSAGE.value, 'reply_on_id': 1,
             "photos": req1.json(), "videos": req2.json()})
        while True:
            json_ws = await ws.receive_json()
            if json_ws['data'] and type(json_ws['data']) != int:
                data = json.loads(json_ws['data'])
                if 'msg' in data:
                    assert data['msg']['type'] == MessageTypes.DEFAULT.value
                    assert data['msg']['reply_on']['id'] == 1
                    assert data['msg']['photos'] != []
                    assert data['msg']['videos'] != []
                    res1 = await task1
                    assert res1['msg']['type'] == MessageTypes.DEFAULT.value
                    assert res1['msg']['reply_on']['id'] == 1
                    assert res1['msg']['photos'] != []
                    assert res1['msg']['videos'] != []
                    break
        await ws.close()
    er = await exception_ws_request(f'ws://test/chat/connect/ws?token={tokens[0]}',
                                    {"text": "hi", "chat_id": 45, "message_type": WSMessageTypes.CREATE_MESSAGE.value},
                                    ac)
    assert er.code == CloseReason.POLICY_VIOLATION
    assert er.reason == "You are not a member of this chat"

    er = await exception_ws_request(f'ws://test/chat/connect/ws?token={tokens[0]}',
                                    {"message_type": WSMessageTypes.CREATE_MESSAGE.value, "chat_id": 1},
                                    ac)
    assert er.code == CloseReason.INVALID_FRAME_PAYLOAD_DATA
    assert er.reason == "Assertion failed, Nothing to create has been given"

    er = await exception_ws_request(f'ws://test/chat/connect/ws?token={tokens[0]}',
                                    {"text": "hi", "chat_id": 1},
                                    ac)
    assert er.code == CloseReason.INVALID_FRAME_PAYLOAD_DATA
    assert er.reason == "There is no message_type"

    er = await exception_ws_request(f'ws://test/chat/connect/ws?token={tokens[0]}',
                                    {"text": "hi", "message_type": WSMessageTypes.CREATE_MESSAGE.value},
                                    ac)
    assert er.code == CloseReason.INVALID_FRAME_PAYLOAD_DATA
    assert er.reason == "There is no chat_id"
    print(message_manager.active_connections)


@pytest.mark.anyio
async def test_editing_messages(ac: AsyncClient):
    print("!!!!test_editing_messages!!!!")
    req1 = await upload_test('test_files/test_pic.jpg', '/message/upload-images-for-message', "images", "image/jpeg",
                             tokens[0], ac, {"chat_id": 1})
    assert req1.status_code == 200
    req2 = await upload_test('test_files/test_vid.mp4', '/message/upload-videos-for-message', "videos", "video/mp4",
                             tokens[0], ac, {"chat_id": 1})
    assert req2.status_code == 200

    async with aconnect_ws(f'ws://test/chat/connect/ws?token={tokens[1]}', ac) as ws:
        await ws.send_json(
            {"text": "edit_begin", "chat_id": 1,
             "message_type": WSMessageTypes.CREATE_MESSAGE.value, "photos": req1.json(), "videos": req2.json()})

        while True:
            json_ws = await ws.receive_json()
            if json_ws['data'] and type(json_ws['data']) != int:
                data = json.loads(json_ws['data'])
                if 'msg' in data:
                    assert data['msg']['type'] == MessageTypes.DEFAULT.value
                    assert data['msg']['text'] == 'edit_begin'
                    break
        req3 = await upload_test('test_files/test_pic2.jpg', '/message/upload-image-for-message', "image", "image/jpeg",
                                 tokens[0], ac, {"chat_id": 1, "image_index": 0})
        assert req3.status_code == 200
        task1 = asyncio.create_task(second_user_ws(tokens[1], ac))
        await asyncio.sleep(1)
        await ws.send_json(
            {"text": "edit", "chat_id": 1, "message_id": data['msg']['id'],
             "message_type": WSMessageTypes.EDIT_MESSAGE.value, "photo": {0: req3.json()}})
        while True:
            json_ws = await ws.receive_json()
            if json_ws['data'] and type(json_ws['data']) != int:
                data1 = json.loads(json_ws['data'])
                if 'msg' in data1:
                    assert data1['ws_type'] == WSMessageTypes.EDIT_MESSAGE.value
                    assert data1['msg']['text'] == 'edit'
                    assert data1['msg']['photos'][0] != data['msg']['photos'][0]
                    res = await task1
                    assert res['ws_type'] == WSMessageTypes.EDIT_MESSAGE.value
                    assert res['msg']['text'] == 'edit'
                    assert res['msg']['photos'][0] != data['msg']['photos'][0]
                    break
        req4 = await upload_test('test_files/test_vid2.mp4', '/message/upload-video-for-message', "video", "video/mp4",
                                 tokens[0], ac, {"chat_id": 1, "video_index": 0})
        assert req4.status_code == 200
        task1 = asyncio.create_task(second_user_ws(tokens[1], ac))
        await asyncio.sleep(1)
        await ws.send_json(
            {"text": "edit", "chat_id": 1, "message_id": data['msg']['id'],
             "message_type": WSMessageTypes.EDIT_MESSAGE.value, "video": {0: req4.json()}})
        while True:
            json_ws = await ws.receive_json()
            if json_ws['data'] and type(json_ws['data']) != int:
                data1 = json.loads(json_ws['data'])
                if 'msg' in data1:
                    assert data1['ws_type'] == WSMessageTypes.EDIT_MESSAGE.value
                    assert data1['msg']['text'] == 'edit'
                    assert data1['msg']['videos'][0] != data['msg']['videos'][0]
                    res = await task1
                    assert res['ws_type'] == WSMessageTypes.EDIT_MESSAGE.value
                    assert res['msg']['text'] == 'edit'
                    assert res['msg']['videos'][0] != data['msg']['videos'][0]
                    break
        await ws.close()

    er = await exception_ws_request(f'ws://test/chat/connect/ws?token={tokens[0]}',
                                    {"text": "edit_begin", "chat_id": 1,
                                     "message_type": WSMessageTypes.EDIT_MESSAGE.value, "message_id": 2323},
                                    ac)
    assert er.code == CloseReason.INVALID_FRAME_PAYLOAD_DATA
    assert er.reason == "There is no message with such id"

    er = await exception_ws_request(f'ws://test/chat/connect/ws?token={tokens[1]}',
                                    {"text": "edit_begin", "chat_id": 1,
                                     "message_type": WSMessageTypes.EDIT_MESSAGE.value, "message_id": 1},
                                    ac)
    assert er.code == CloseReason.POLICY_VIOLATION
    assert er.reason == "You are not an author of this message"

    async with test_session() as session:
        msg = (await session.execute(select(Message).filter_by(id=1))).scalar_one_or_none()
        msg.date -= datetime.timedelta(minutes=config.EDIT_MESSAGE_INTERVAL_MINUTES + 1)
        await session.commit()
    er = await exception_ws_request(f'ws://test/chat/connect/ws?token={tokens[0]}',
                                    {"text": "edit_begin", "chat_id": 1,
                                     "message_type": WSMessageTypes.EDIT_MESSAGE.value, "message_id": 1},
                                    ac)
    assert er.code == CloseReason.POLICY_VIOLATION
    assert er.reason == f"{config.EDIT_MESSAGE_INTERVAL_MINUTES} minutes have already passed"

    async with test_session() as session:
        msg = (await session.execute(select(Message).filter_by(id=1))).scalar_one_or_none()
        msg.date += datetime.timedelta(minutes=config.EDIT_MESSAGE_INTERVAL_MINUTES + 1)
        await session.commit()
    er = await exception_ws_request(f'ws://test/chat/connect/ws?token={tokens[0]}',
                                    {"text": "edit_begin", "chat_id": 1,
                                     "message_type": WSMessageTypes.EDIT_MESSAGE.value, "message_id": 1,
                                     "photo": {0: req1.json()[0]}},
                                    ac)
    assert er.code == CloseReason.INVALID_FRAME_PAYLOAD_DATA
    assert er.reason == "No photo with such index"
    print(message_manager.active_connections)


@pytest.mark.anyio
async def test_deleting_messages(ac: AsyncClient):
    print("!!!!test_deleting_messages!!!!")
    async with aconnect_ws(f'ws://test/chat/connect/ws?token={tokens[0]}', ac) as ws:
        task1 = asyncio.create_task(second_user_ws(tokens[1], ac))
        await asyncio.sleep(0)
        await ws.send_json(
            {"chat_id": 1, "message_id": 1, "message_type": WSMessageTypes.DELETE_MESSAGE.value})
        while True:
            json_ws = await ws.receive_json()
            if json_ws['data'] and type(json_ws['data']) != int:
                data = json.loads(json_ws['data'])
                if 'msg' in data:
                    assert data['ws_type'] == WSMessageTypes.DELETE_MESSAGE.value
                    res1 = await task1
                    assert res1['ws_type'] == WSMessageTypes.DELETE_MESSAGE.value
                    break
        await ws.close()
