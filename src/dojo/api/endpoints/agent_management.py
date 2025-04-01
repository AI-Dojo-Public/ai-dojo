import importlib.metadata
import json
import os
import shutil
import subprocess
import sys

from dataclasses import dataclass
from fastapi import APIRouter, HTTPException, status
from urllib.request import url2pathname
from urllib.parse import urlparse, urlunparse

from dojo.schemas.agents import AgentAddition, AgentRemoval, AgentMethod

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={
        404: {"description": "Not found"},
    },
)

@dataclass
class PackageEntry:
    module_name: str
    package_name: str
    package_version: str
    code_path: str
    git_repo: bool


@router.get("/list", status_code=status.HTTP_200_OK)
async def list_agents() -> list[PackageEntry]:
    result = []
    entry_points = importlib.metadata.entry_points(group='cyst.services')
    for entry_point in entry_points:
        module_name = entry_point.name
        module_package = entry_point.dist
        code_path = ""

        # pip, poetry does not work
        try:
            for f in module_package.files:
                if f.match("*direct_url.json"):
                    j = json.loads(f.read_text())
                    code_url = urlparse(j.get("url")).path
                    code_path = url2pathname(code_url)
                    break
        except FileNotFoundError:
            pass

        version = module_package.version

        git_info = subprocess.run(['git', '-C', code_path, 'rev-parse'], capture_output=True, text=True)
        local_git_repo = git_info.returncode == 0

        result.append(PackageEntry(module_name, module_package.name, version, code_path, local_git_repo))

    return result


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_agent(agent: AgentAddition) -> list[PackageEntry]:
    if agent.method == AgentMethod.GIT:
        url_path = list(urlparse(agent.path))

        # If the credentials are not part of the url, attempt to add the provided ones
        if url_path[1].find("@") == -1:
            if agent.access_token:
                if not agent.user:
                    agent.user = "__user"
                url_path[1] = f"{agent.user}:{agent.access_token}@" + url_path[1]

        installable = f"git+{urlunparse(url_path)}"
    else: # PYPI package name
        installable = agent.path

    old_packages = await list_agents()

    # Install the agent directly from the Git repository using pip
    pip_command = [sys.executable, '-m', 'pip', 'install', installable]
    pip_info = subprocess.run(pip_command, capture_output=True, text=True)

    # Check for any errors during the pip install process
    if pip_info.returncode != 0:
        raise HTTPException(status_code=409,
                            detail=f"Failed to install the package from '{installable}'. Reason: {pip_info.stderr}")

    new_packages = await list_agents()

    result = []
    # This is not pretty...
    for new_pkg in new_packages:
        identical = False
        for index, old_pkg in enumerate(old_packages):
            if old_pkg is None:
                continue

            if new_pkg == old_pkg:
                identical = True
                old_packages[index] = None
                break

        if not identical:
            result.append(new_pkg)

    return result


@router.post("/remove", status_code=status.HTTP_200_OK)
async def remove_agent(remove: AgentRemoval) -> dict:
    result = {}
    by_package = {}
    module_to_remove = None

    agents = await list_agents()

    # Gather modules by package for dependencies
    for agent in agents:
        if not agent.package_name in by_package:
            by_package[agent.package_name] = []
        if agent.package_name == remove.name:
            module_to_remove = agent

        by_package[agent.package_name].append(agent.module_name)

    # If there is more than one module in the package, do not remove unless forced
    if len(by_package[module_to_remove.package_name]) > 1 and not remove.force:
        return {"success": False, "reason": f"More then one module in the package '{module_to_remove.package_name}', "
                                            f"parent package of module '{module_to_remove.module_name}'. "
                                            f"Use the 'force' parameter to proceed with removal."}

    # If we want to delete code, also require forcing
    if remove.delete_code and not remove.force:
        return {"success": False, "reason": f"Code deletion requires forcing."}

    # Remove pip entry
    pip_command = [sys.executable, '-m', 'pip', 'uninstall', '-y', module_to_remove.package_name]
    pip_info = subprocess.run(pip_command, capture_output=True, text=True)
    if pip_info.returncode != 0:
        raise HTTPException(status_code=409, detail=f"Failed to uninstall the required agent. Reason: '{pip_info.stderr}'.")

    if remove.delete_code and module_to_remove.code_path:
        shutil.rmtree(module_to_remove.code_path, ignore_errors=True)
        return {"success": True, "message": f"Module '{module_to_remove.module_name}' "
                                            f"in the package '{module_to_remove.package_name}' "
                                            f"was removed including the code at '{module_to_remove.code_path}'."}
    else:
        return {"success": True, "message": f"Module '{module_to_remove.module_name}' "
                                            f"in the package '{module_to_remove.package_name}' was removed."}
