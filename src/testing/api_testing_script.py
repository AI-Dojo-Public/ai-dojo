import json

import jsonpickle
import httpx
import asyncio


async def create(name: str, platform: dict):
    from cyst_infra import all_config_items
    import cyst.core.environment.serialization  # Register jsonpickle modifications

    config = jsonpickle.encode(all_config_items, make_refs=False, indent=1)
    data = {"name": name, "platform": platform, "configuration": config}

    print(f"Creating Environment: {name}")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/environment/create/", json=data)
    if response.status_code != 201:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(f"Environment created successfully: {name}")


async def configure(name: str):
    data = {"name": name}

    print(f"Configuring environment: {name}")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/environment/configure/", params=data, timeout=100000)
    if response.status_code != 200:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(f"Environment configured successfully: {name}")


async def init(name: str):
    data = {"name": name}

    print(f"Initializing environment: {name}")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/environment/init/", params=data)
    if response.status_code != 200:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(f"Environment initialized successfully: {name}")


async def run(name: str):
    data = {"name": name}

    print(f"Starting environment: {name}")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/environment/run/", params=data)
    if response.status_code != 200:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(f"Environment started: {name}")


async def list_envs():
    print("Listing environments")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8000/api/v1/environment/list/")
    if response.status_code != 200:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(response.text)
        return response.text


async def terminate(env: str):
    data = {"name": env}

    print(f"Terminating environment: {env}")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/environment/terminate/", params=data)
    if response.status_code != 200:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(f"Environment terminated: {env}")


async def close(env: str):
    data = {"name": env}

    print(f"Closing environment: {env}")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/environment/close/", params=data)
    if response.status_code != 200:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(f"Environment closed: {env}")


async def create_envs():
    async with asyncio.TaskGroup() as tg:
        # tg.create_task(create("env1", {"type": 1, "provider": "CYST"}))
        tg.create_task(create("emu-env", {"type": 2, "provider": "docker+cryton"}))
        # tg.create_task(create("emu-env2", {"type": 2, "provider": "docker+cryton"}))


async def start_env(env: str):
    await init(env)
    await run(env)


async def terminate_env(env: str):
    await terminate(env)
    await close(env)


async def main():
    await create_envs()
    envs = json.loads(await list_envs())

    for env in envs:
        await configure(env)

    # async with asyncio.TaskGroup() as tg:
    #     for env in envs:
    #         tg.create_task(start_env(env))
    #
    # await list_envs()

    # async with asyncio.TaskGroup() as tg:
    #     for env in envs:
    #         tg.create_task(terminate_env(env))
    #
    # await list_envs()

asyncio.run(main())
