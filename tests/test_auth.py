from httpx import AsyncClient
from config import config
import pytest
from schemes.auth import RegisterScheme



@pytest.mark.anyio
async def test_registration(ac: AsyncClient):
    reg1 = await ac.post(f'/auth/email-reg-send', json=RegisterScheme(email=config.MAIL_TEST, username='1').dict())
    assert reg1.status_code == 200
