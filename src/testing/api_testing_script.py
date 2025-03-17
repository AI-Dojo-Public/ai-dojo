import json

import jsonpickle
import httpx
import asyncio


async def create(name: str, platform: dict):
    data = {"id": name, "platform": platform, "configuration": "demo"}

    print(f"Creating Environment: {name}")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/environment/create/", json=data)
    if response.status_code != 201:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(f"Environment created successfully: {name}")

async def execute_attack(port: int):
    data = {
        "action": "dojo:scan_network",
        "params": {
            "to_network": "192.168.0.2/28",
            "dst_ip": "192.168.0.1",
            "dst_service": ""
        }
    }

    print("Executing attack...")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"http://localhost:{port}/execute/attacker_node_2.attacker/", json=data)
    if response.status_code != 200:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(response.text)

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
    data = {"id": name}

    print(f"Initializing environment: {name}")
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/api/v1/environment/init/", params=data)
    if response.status_code != 200:
        raise RuntimeError(f"message: {response.text}, code: {response.status_code}")
    else:
        print(f"Environment initialized successfully: {name}")


async def run(name: str):
    data = {"id": name}

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
        tg.create_task(create("env3", {"type": 2, "provider": "docker+cryton"}))
        # tg.create_task(create("env2", {"type": 1, "provider": "CYST"}))
        # tg.create_task(create("env3", {"type": 1, "provider": "CYST"}))
        # tg.create_task(create("emu-env", {"type": 2, "provider": "docker+cryton"}))
        # tg.create_task(create("emu-env2", {"type": 2, "provider": "docker+cryton"}))


async def start_env(env: str):
    await init(env)
    await run(env)


async def terminate_env(env: str):
    await terminate(env)
    await close(env)


async def configure_env():
    await create_envs()

async def main():
    await configure_env()
    envs = json.loads(await list_envs())

    async with asyncio.TaskGroup() as tg:
        for env in envs:
            tg.create_task(start_env(env))

    await list_envs()

    # async with asyncio.TaskGroup() as tg:
    #     for env in envs:
    #         tg.create_task(terminate_env(env))
    #
    # await list_envs()

# asyncio.run(configure_env())
asyncio.run(main())
