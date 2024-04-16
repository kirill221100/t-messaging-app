from ffmpeg.asyncio import FFmpeg
from io import BytesIO
from pathlib import Path
import aiofiles, os
from uuid import uuid4

path = Path.cwd()


async def compress_video(vid: bytes):
    with BytesIO(vid) as video:
        async with aiofiles.tempfile.NamedTemporaryFile('wb', delete=False) as temp:
            await temp.write(video.read())
    video_path = f'videos/{uuid4()}.mp4'
    temp_path = path.absolute().joinpath(temp.name)
    process = (
        FFmpeg().option("y").input(temp_path).output(video_path,  vcodec='libx264', crf='27', preset='veryfast')
    )
    await process.execute()
    os.remove(temp_path)
    return video_path



