import asyncio
from typing import Iterable, Union, Coroutine, Optional
from io import BytesIO
from cai import Client, LoginSliderNeeded, LoginCaptchaNeeded, LoginDeviceLocked
from loguru import logger


async def wait_fut(
    coros: Iterable[Union[Coroutine, asyncio.Task]],
    *,
    timeout: Optional[float] = None,
    return_when: str = asyncio.ALL_COMPLETED,
) -> None:
    tasks = []
    for c in coros:
        if asyncio.iscoroutine(c):
            tasks.append(asyncio.create_task(c))
        else:
            tasks.append(c)
    if tasks:
        await asyncio.wait(tasks, timeout=timeout, return_when=return_when)


async def _login_slider_need(client: Client, exc: LoginSliderNeeded):
    verify = (
        f"1. '{exc.verify_url}'\n"
        f"2. '{exc.verify_url.replace('ssl.captcha.qq.com', 'txhelper.glitch.me')}'"
    )
    logger.opt(colors=True).info(
        f"<magenta>\nVerify url: </>\n<yellow>{verify}</>\nPlease enter the ticket:",
        alt=f"[magenta]\nVerify url: [/]\n[dark_orange]{verify}[/]\nPlease enter the ticket:",
    )
    ticket = input().strip()
    try:
        await client.submit_slider_ticket(ticket)
        logger.success("Login Success!")
        await asyncio.sleep(3)
        return
    except Exception as e:
        return await login_resolver(client, e)


async def _login_captcha_needed(client: Client, exp: LoginCaptchaNeeded):
    try:
        from PIL import Image
    except ImportError:
        raise
    logger.opt(colors=True).info("<bold>\nCaptcha:</>", alt="[bold]\nCaptcha:[/]")
    image = Image.open(BytesIO(exp.captcha_image))
    image.show()
    logger.info("\nPlease enter the captcha: ")
    captcha = input().strip()
    try:
        await client.submit_captcha(captcha, exp.captcha_sign)
        logger.success("Login Success!")
        await asyncio.sleep(3)
        return
    except Exception as e:
        return await login_resolver(client, e)


async def _login_device_locked(client: Client, exc: LoginDeviceLocked):
    logger.critical("Device lock detected!")
    if not exc.sms_phone and not exc.verify_url:
        raise AssertionError("No way to verify device...")
    while True:
        logger.opt(colors=True).info(
            (
                "<cyan>\nChoose a method to verity: </>\n"
                f"{'<green>| enable  | </>' if exc.sms_phone else '<red>| disable | </>'}"
                f"1. Send sms message to {exc.sms_phone}.\n"
                f"{'<green>| enable  | </>' if exc.verify_url else '<red>| disable | </>'}"
                f"2. Verify device by url.\n"
                f"<yellow>Choose: </>"
            ),
            alt=(
                "[cyan3]\nChoose a method to verity: [/]\n"
                f"{'[green]| enable  | [/]' if exc.sms_phone else '[red]| disable | [/]'}"
                f"1. Send sms message to {exc.sms_phone}.\n"
                f"{'[green]| enable  | [/]' if exc.verify_url else '[red]| disable | [/]'}"
                f"2. Verify device by url.\n"
                f"[yellow]Choose: [/]"
            ),
        )
        choice = input()
        if "1" in choice and exc.sms_phone:
            way = "sms"
            break
        elif "2" in choice and exc.verify_url:
            way = "url"
            break
        logger.error(f"'{choice}' is invalid!", alt=f"[red] {choice!r} is invalid![/]")

    if way == "sms":
        await client.request_sms()
        logger.info(f"\nSMS was sent to {exc.sms_phone}!\nPlease enter the sms_code: ")
        sms_code = input().strip()
        try:
            await client.submit_sms(sms_code)
        except Exception as e:
            await login_resolver(client, e)
    elif way == "url":
        logger.info(
            f"\nGo to \n{exc.verify_url} \nto verify device!\n"
            f"Press ENTER after verification to continue login..."
        )
        input()
        try:
            return await client.login()
        except Exception as e:
            return await login_resolver(client, e)


async def login_resolver(client: Client, exception: Exception):
    if isinstance(exception, LoginSliderNeeded):
        return await _login_slider_need(client, exception)
    elif isinstance(exception, LoginCaptchaNeeded):
        return await _login_captcha_needed(client, exception)
    elif isinstance(exception, LoginDeviceLocked):
        return await _login_device_locked(client, exception)
    else:
        # LoginAccountFrozen, LoginException, ApiResponseError, etc...
        raise
