import asyncio
import logging
from httpx import AsyncClient
import pytest
from schemes.chat import GroupChatScheme, DirectChatScheme
import random
import datetime
from httpx_ws import aconnect_ws
from schemes.message import WSMessageTypes
from schemes.chat import EditGroupChatScheme, ChatTypes
from db.models.message import DefaultMessage, MessageTypes, InfoMessageTypes
from tests.conftest import tokens, test_session
from tests.test_chat import second_user_ws
from sqlalchemy import select
from config import config
from db.utils.chat import get_read_date
from db.utils.message import get_message_by_id_check


@pytest.mark.anyio
async def test_get_messages_by_chat_id(ac: AsyncClient):
    req1 = await ac.put(f'/chat/edit-group-chat/1', headers={"Authorization": f'Bearer {tokens[0]}'},
                        json=EditGroupChatScheme(add_users_ids=[6]).dict())
    assert req1.status_code == 200
    async with test_session() as s:
        message = DefaultMessage(type=MessageTypes.DEFAULT.value, text='1', user_id=6, chat_id=1)
        s.add(message)
        await s.commit()
    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    messages = req1.json()['messages']
    assert len(messages) == 2
    assert messages[0]['id'] == message.id
    assert messages[1]['id'] == message.id - 1
    assert messages[1]['info_type'] == InfoMessageTypes.ADD_USERS.value

    req1 = await ac.put(f'/chat/edit-group-chat/1', headers={"Authorization": f'Bearer {tokens[0]}'},
                        json=EditGroupChatScheme(delete_users_ids=[6]).dict())
    assert req1.status_code == 200
    async with test_session() as s:
        message = DefaultMessage(type=MessageTypes.DEFAULT.value, text='2', user_id=1, chat_id=1)
        s.add(message)
        await s.commit()
    req1 = await ac.put(f'/chat/edit-group-chat/1', headers={"Authorization": f'Bearer {tokens[0]}'},
                        json=EditGroupChatScheme(add_users_ids=[6]).dict())
    assert req1.status_code == 200
    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    messages = req1.json()['messages']
    assert len(messages) == 4
    assert messages[0]['info_type'] == InfoMessageTypes.ADD_USERS.value
    assert messages[1]['info_type'] == InfoMessageTypes.DELETE_USERS.value
    assert messages[0]['id'] - 2 == messages[1]['id']

    req1 = await ac.delete(f'/chat/delete-my-chat-history/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    assert req1.status_code == 200
    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    assert req1.json()['messages'] == []
    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[0]}'})
    assert req1.json()['messages'] != []

    async with test_session() as s:
        message = DefaultMessage(type=MessageTypes.DEFAULT.value, text='3', user_id=1, chat_id=1)
        s.add(message)
        await s.commit()
    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    assert len(req1.json()['messages']) == 1
    await ac.put(f'/chat/edit-group-chat/1', headers={"Authorization": f'Bearer {tokens[0]}'},
                        json=EditGroupChatScheme(delete_users_ids=[6]).dict())
    await ac.put(f'/chat/edit-group-chat/1', headers={"Authorization": f'Bearer {tokens[0]}'},
                        json=EditGroupChatScheme(add_users_ids=[6]).dict())
    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    messages = req1.json()['messages']
    assert len(messages) == 3
    assert messages[1]['id'] == messages[0]['id'] - 1
    assert messages[1]['id'] == messages[-1]['id'] + 1
    assert messages[0]['info_type'] == InfoMessageTypes.ADD_USERS.value
    assert messages[1]['info_type'] == InfoMessageTypes.DELETE_USERS.value
    assert messages[-1]['text'] == '3'

    await ac.put(f'/chat/edit-group-chat/1', headers={"Authorization": f'Bearer {tokens[0]}'},
                 json=EditGroupChatScheme(delete_users_ids=[6]).dict())
    async with test_session() as s:
        message = DefaultMessage(type=MessageTypes.DEFAULT.value, text='4', user_id=1, chat_id=1)
        s.add(message)
        await s.commit()
    await ac.put(f'/chat/edit-group-chat/1', headers={"Authorization": f'Bearer {tokens[0]}'},
                 json=EditGroupChatScheme(add_users_ids=[6]).dict())
    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    assert len(req1.json()['messages']) == 5
    assert messages == req1.json()['messages'][2:]
    messages = req1.json()['messages']
    assert messages[1]['id'] == messages[0]['id'] - 2

    req1 = await ac.patch(f'/chat/leave-group-chat/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    assert req1.status_code == 200
    async with test_session() as s:
        message = DefaultMessage(type=MessageTypes.DEFAULT.value, text='5', user_id=1, chat_id=1)
        s.add(message)
        await s.commit()
    req1 = await ac.patch(f'/chat/return-to-group-chat/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    assert req1.status_code == 200
    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'})
    assert len(req1.json()['messages']) == 7
    assert messages == req1.json()['messages'][2:]
    messages = req1.json()['messages']
    assert messages[0]['info_type'] == InfoMessageTypes.RETURN_TO_CHAT.value
    assert messages[1]['info_type'] == InfoMessageTypes.LEFT_CHAT.value
    assert messages[1]['id'] == messages[0]['id'] - 2

    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'}, params={"last_message_id": messages[1]['id'] + 1})
    assert req1.json()['messages'][0]['id'] == messages[1]['id']

    req1 = await ac.get(f'/message/get-messages-by-chat-id/1', headers={"Authorization": f'Bearer {tokens[5]}'},
                        params={"last_message_id": messages[1]['id'] + 1, "count": 1})
    assert len(req1.json()['messages']) == 1

    async with test_session() as s:
        message = DefaultMessage(type=MessageTypes.DEFAULT.value, text='6', user_id=1, chat_id=2)
        s.add(message)
        await s.commit()
    req1 = await ac.get(f'/message/get-messages-by-chat-id/2', headers={"Authorization": f'Bearer {tokens[0]}'})
    assert req1.json()['messages'][0]['text'] == '6'

    req1 = await ac.delete(f'/chat/delete-my-chat-history/2', headers={"Authorization": f'Bearer {tokens[0]}'})
    assert req1.status_code == 200
    req1 = await ac.get(f'/message/get-messages-by-chat-id/2', headers={"Authorization": f'Bearer {tokens[0]}'})
    assert req1.json()['messages'] == []
    async with test_session() as s:
        message = DefaultMessage(type=MessageTypes.DEFAULT.value, text='7', user_id=1, chat_id=2)
        s.add(message)
        await s.commit()
    req1 = await ac.get(f'/message/get-messages-by-chat-id/2', headers={"Authorization": f'Bearer {tokens[0]}'})
    assert len(req1.json()['messages']) == 1
    assert req1.json()['messages'][0]['text'] == '7'








