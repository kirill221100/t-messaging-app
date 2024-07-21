import asyncio
import json
import random
import logging
from typing import List, Dict, Optional
from redis import asyncio as aioredis
#import aioredis
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from config import config


class Redis:
    def __init__(self):
        self.psub = None
        self.url = f"redis://{config.REDIS_USER}:{config.REDIS_PASSWORD}@{config.REDIS_URL}"
        self.connection = None

    async def create_connections(self) -> None:
        self.connection = aioredis.from_url(self.url, db=0)
        self.psub = self.connection.pubsub()

    async def delete_connections(self) -> None:
        await self.connection.aclose()
        await self.psub.aclose()


    async def subscribe(self, channel: str) -> None:
        await self.psub.subscribe(channel)

    async def subscribe_on_many(self, channels: List[str]) -> None:
        await self.psub.subscribe(*channels)

    async def unsubscribe(self, channel: str) -> None:
        await self.psub.unsubscribe(channel)

    async def publish(self, channel: str, message):
        return await self.connection.publish(channel, message)


redis = Redis()


class MessageManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.users_websockets: Dict[int, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket, user_id: int, channels: List[str]):
        await ws.accept()
        nonexistent_rooms = []
        if ws_list := self.users_websockets.get(user_id):
            if ws not in ws_list:
                self.users_websockets[user_id].append(ws)
        else:
            self.users_websockets[user_id] = [ws]
        for channel in channels:
            if room := self.active_connections.get(channel):
                room.append(ws)
            else:
                self.active_connections[channel] = [ws]
                nonexistent_rooms.append(channel)
        if nonexistent_rooms:
            subscribe_and_listen_to_channel_task = asyncio.create_task(
                self._subscribe_and_listen_to_channels(nonexistent_rooms))
            waiting_task = asyncio.create_task(asyncio.sleep(1))
            await asyncio.wait([subscribe_and_listen_to_channel_task, waiting_task],
                               return_when=asyncio.FIRST_COMPLETED)

    async def connect_to_new_chat(self, users_ids: List[int], channel: str):
        room = []
        for user_id in users_ids:
            if (ws := self.users_websockets.get(user_id)) and ws != []:
                room.append(ws[-1])
        self.active_connections[channel] = room
        subscribe_and_listen_to_channel_task = asyncio.create_task(self._subscribe_and_listen_to_channel(channel))
        waiting_task = asyncio.create_task(asyncio.sleep(1))
        await asyncio.wait([subscribe_and_listen_to_channel_task, waiting_task], return_when=asyncio.FIRST_COMPLETED)

    # async def connect_added_users(self, users_ids: List[int], channel: str):
    #     if not (room := self.active_connections.get(channel)):
    #         room = []
    #     logging.warning(room)
    #     for user_id in users_ids:
    #         if ws := self.users_websockets.get(user_id):
    #             room.append(ws)
    #     if not self.active_connections.get(channel):
    #         self.active_connections[channel] = room
    #         subscribe_and_listen_to_channel_task = asyncio.create_task(self._subscribe_and_listen_to_channel(channel))
    #         waiting_task = asyncio.create_task(asyncio.sleep(1))
    #         await asyncio.wait([subscribe_and_listen_to_channel_task, waiting_task],
    #                            return_when=asyncio.FIRST_COMPLETED)
    async def connect_added_user(self, user_id: int, channel: str):
        if not (room := self.active_connections.get(channel)) and room is None:
            room = []
        if ws := self.users_websockets.get(user_id)[-1]:
            room.append(ws)
        if not self.active_connections.get(channel):
            self.active_connections[channel] = room
            subscribe_and_listen_to_channel_task = asyncio.create_task(self._subscribe_and_listen_to_channel(channel))
            waiting_task = asyncio.create_task(asyncio.sleep(1))
            await asyncio.wait([subscribe_and_listen_to_channel_task, waiting_task],
                               return_when=asyncio.FIRST_COMPLETED)

    async def disconnect_deleted_user(self, user_id: int, channel: str):
        if room := self.active_connections.get(channel):
            if ws_list := self.users_websockets.get(user_id):
                for ws in ws_list:
                    room.remove(ws)

    async def connect_added_users(self, ids: List[int], channel: str):
        for i in ids:
            await self.connect_added_user(i, channel)

    async def disconnect_deleted_users(self, ids: List[int], channel: str):
        for i in ids:
            await self.disconnect_deleted_user(i, channel)

    async def disconnect(self, ws: WebSocket, channel: str):
        if room := self.active_connections.get(channel):
            room.remove(ws)

    async def disconnect_from_many(self, ws: WebSocket, channels: List[str], user_id: int):
        #del self.users_websockets[user_id]
        self.users_websockets[user_id].remove(ws)
        for channel in channels:
            if room := self.active_connections.get(channel):
                room.remove(ws)

    async def _subscribe_and_listen_to_channels(self, channels: List[str]):
        # for i in channels:
        #     logging.warning([i, self.active_connections, 3333])
        #     if i in self.active_connections:
        #         return
        await redis.subscribe_on_many(channels)
        async for msg in redis.psub.listen():
            await self._consume_events(msg['channel'].decode('utf-8'), msg)

    async def _subscribe_and_listen_to_channel(self, channel: str):
        await redis.subscribe(channel)
        async for msg in redis.psub.listen():
            await self._consume_events(channel, msg)

    async def _consume_events(self, channel, message):
        if room_connections := self.active_connections.get(channel):
            message['channel'] = message['channel'].decode('utf-8')
            if message['type'] != 'subscribe':
                message['data'] = message['data'].decode('utf-8')
            for connection in room_connections:
                try:
                    if connection.application_state == WebSocketState.CONNECTED:
                        await connection.send_json(message)
                except (WebSocketDisconnect, RuntimeError) as e:
                    await self.disconnect(connection, channel)

    async def send_message_to_room(self, channel: str, message):
        if (ch := message_manager.active_connections.get(channel)) and ch != []:
            await redis.publish(channel, json.dumps(message))


message_manager = MessageManager()


async def create_email_code(email: str, username: Optional[str] = None):
    code = random.randint(100000, 999999)
    await redis.connection.set(email, json.dumps({"code": code, "username": username}), ex=600)
    return code


async def create_email_change_code(user_id: int, email: str):
    code = random.randint(100000, 999999)
    await redis.connection.set(user_id, json.dumps({"code": code, 'email': email}), ex=600)
    return code


async def verify_email_code(email: str, code: int):
    if res := await redis.connection.get(email):
        res_json = json.loads(str(res, encoding='utf-8'))
        if res_json['code'] == code:
            return res_json
    return False


async def verify_email_change_code(user_id: int, code: int):
    if res := await redis.connection.get(user_id):
        if json.loads(res)['code'] == code:
            return json.loads(res)['email']
    return False
