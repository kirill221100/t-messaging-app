import os
import aiofiles
import aioboto3
import random
import string
import logging
from config import config
from utils.photo import compress_photo
from utils.video import compress_video
from typing import List
import base64, uuid
from fastapi import UploadFile


async def upload_avatar(avatar: bytes, user_or_chat_id: int, user_or_chat: str):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        pic = await compress_photo(base64.b64decode(avatar))
        obj = await s3.Object(config.AWS_BUCKET, f'avatar/{user_or_chat}/{user_or_chat_id}/{uuid.uuid4()}.jpg')
        r = await obj.put(Body=pic.getvalue())
        pic.close()
        return f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}"


async def upload_photos(photos: List[UploadFile], chat_id: int, user_id: int):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        res = []
        for photo in photos:
            rand_name = ''.join(random.choices(string.ascii_letters, k=10))
            pic = await compress_photo(await photo.read())
            obj = await s3.Object(config.AWS_BUCKET, f'chat/{chat_id}/photos/{rand_name}_{user_id}_{len(res)}.jpg')
            r = await obj.put(Body=pic.getvalue())
            res.append(f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}")
            pic.close()
        return res


async def upload_videos(videos: List[UploadFile], chat_id: int, user_id: int):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    logging.warning(1)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        res = []
        for video in videos:
            rand_name = ''.join(random.choices(string.ascii_letters, k=10))
            logging.warning(2)
            vid_path = await compress_video(await video.read())
            logging.warning(6)
            obj = await s3.Object(config.AWS_BUCKET, f'chat/{chat_id}/videos/{rand_name}_{user_id}_{len(res)}.mp4')
            async with aiofiles.open(vid_path, 'rb') as v:
                r = await obj.put(Body=await v.read())
                res.append(f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}")
            logging.warning(7)
            os.remove(vid_path)
        return res


async def upload_photo(photo: UploadFile, photo_index: int, chat_id: int, user_id: int):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        rand_name = ''.join(random.choices(string.ascii_letters, k=10))
        pic = await compress_photo(await photo.read())
        obj = await s3.Object(config.AWS_BUCKET, f'chat/{chat_id}/photos/{rand_name}_{user_id}_{photo_index}.jpg')
        r = await obj.put(Body=pic.getvalue())
        pic.close()
        return f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}"


async def upload_video(video: UploadFile, video_index: int, chat_id: int, user_id: int):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        rand_name = ''.join(random.choices(string.ascii_letters, k=10))
        vid_path = await compress_video(await video.read())
        obj = await s3.Object(config.AWS_BUCKET, f'chat/{chat_id}/videos/{rand_name}_{user_id}_{video_index}.mp4')
        async with aiofiles.open(vid_path, 'rb') as v:
            r = await obj.put(Body=await v.read())
        os.remove(vid_path)
        return f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}"



