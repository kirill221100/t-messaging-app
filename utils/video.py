from ffmpeg.asyncio import FFmpeg
from ffmpeg import FFmpegError
import subprocess
from io import BytesIO
from pathlib import Path
import aiofiles, os
from uuid import uuid4
from config import config
import os
import asyncio
import logging

path = Path.cwd()


async def compress_video(vid: bytes):
    video = BytesIO(vid)
    async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as temp:
        await temp.write(video.read())
    video.close()
    video_path = path.absolute().joinpath(f'{config.VIDEO_PATH}/{uuid4()}.mp4')
    temp_path = path.absolute().joinpath(temp.name)
    pr = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-loglevel", "48", "-i", temp_path, "-vcodec", "libx264", "-crf", "27", "-preset", "veryfast", video_path, stdin=None,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tasks = [asyncio.create_task(asyncio.wait_for(pr.wait(), None))]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    #print(os.popen(f"ffmpeg -y -loglevel 48 -i {temp_path} -vcodec libx264 -crf 27 -preset veryfast {video_path}"))
    # process = (
    #     FFmpeg().option("y").option("loglevel", 48).input(temp_path).output(
    #         video_path, vcodec='libx264', crf='27', preset='veryfast')
    # )
    #
    # await process.execute()
    os.remove(temp_path)
    return video_path



