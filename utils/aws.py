import os
import aiofiles
import aioboto3
from config import config
from utils.photo import compress_photo
from utils.video import compress_video
from typing import List
import base64


async def upload_photos(photos: List[bytes], chat_id: int, user_id: int, message_id: int):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        res = []
        for photo in photos:
            pic = await compress_photo(base64.b64decode(photo))
            obj = await s3.Object(config.AWS_BUCKET, f'chat/{chat_id}/photos/{message_id}_{user_id}_{len(res)}.jpg')
            r = await obj.put(Body=pic.getvalue())
            res.append(f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}")
            pic.close()
        return res


async def upload_videos(videos: List[bytes], chat_id: int, user_id: int, message_id: int):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        res = []
        for video in videos:
            vid_path = await compress_video(base64.b64decode(video))
            obj = await s3.Object(config.AWS_BUCKET, f'chat/{chat_id}/videos/{message_id}_{user_id}_{len(res)}.mp4')
            async with aiofiles.open(vid_path, 'rb') as v:
                r = await obj.put(Body=await v.read())
                res.append(f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}")
            os.remove(vid_path)
        return res


async def replace_photo(photo: bytes, photo_index: int, chat_id: int, user_id: int, message_id: int):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        pic = await compress_photo(base64.b64decode(photo))
        obj = await s3.Object(config.AWS_BUCKET, f'chat/{chat_id}/photos/{message_id}_{user_id}_{photo_index}.jpg')
        r = await obj.put(Body=pic.getvalue())
        pic.close()
        return f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}"


async def replace_video(video: bytes, video_index: int, chat_id: int, user_id: int, message_id: int):
    session = aioboto3.Session(aws_access_key_id=config.AWS_ACCESS_KEY,
                               aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
    async with session.resource("s3", endpoint_url=config.AWS_ENDPOINT_URL) as s3:
        vid_path = await compress_video(base64.b64decode(video))
        obj = await s3.Object(config.AWS_BUCKET, f'chat/{chat_id}/videos/{message_id}_{user_id}_{video_index}.mp4')
        async with aiofiles.open(vid_path, 'rb') as v:
            r = await obj.put(Body=await v.read())
        os.remove(vid_path)
        return f"https://ipfs.filebase.io/ipfs/{r['ResponseMetadata']['HTTPHeaders']['x-amz-meta-cid']}"



