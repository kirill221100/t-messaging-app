from aioEasyPillow import Editor
from PIL import ImageFile
from io import BytesIO

ImageFile.LOAD_TRUNCATED_IMAGES = True


async def compress_photo(photo: bytes):
    async with BytesIO(photo) as p:
        pic = BytesIO()
        await Editor(p).save(pic, format='JPEG', quality=75, optimize=True)
        return pic
