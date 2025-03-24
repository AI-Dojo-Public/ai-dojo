import importlib.metadata
import json
import os
import shutil
import subprocess

from dataclasses import dataclass
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from urllib.request import url2pathname
from urllib.parse import urlparse, urlunparse

from dojo.schemas.agents import AgentAddition, AgentRemoval


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
    editable: bool
    code_path: str
    git_repo: bool


@router.get("/list", status_code=status.HTTP_201_CREATED)
async def list_agents() -> List[PackageEntry]:
    result = []
    entry_points = importlib.metadata.entry_points(group='cyst.services')
    for entry_point in entry_points:
        module_name = entry_point.name
        module_package = entry_point.dist
        editable = False
        code_path = ""

        # pip, poetry does not work
        try:
            for f in module_package.files:
                if f.match("*direct_url.json"):
                    j = json.loads(f.read_text())
                    editable = j.get("dir_info", {}).get("editable", False)
                    code_url = urlparse(j.get("url")).path
                    code_path = url2pathname(code_url)
                    break
        except FileNotFoundError:
            pass

        version = module_package.version

        git_info = subprocess.run(['git', '-C', code_path, 'rev-parse'], capture_output=True, text=True)
        local_git_repo = git_info.returncode == 0

        result.append(PackageEntry(module_name, module_package.name, version, editable, code_path, local_git_repo))

    return result


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_agent(agent: AgentAddition) -> List[PackageEntry]:
    url_path = list(urlparse(agent.path))

    # If the path is url and if it is, try to clone it
    if url_path[1]:
        # If the credentials are not part of the url, attempt to add the provided ones
        if url_path[1].find("@") == -1:
            if agent.access_token:
                if not agent.user:
                    agent.user = "__user"
                url_path[1] = agent.user + ":" + agent.access_token + "@" + url_path[1]

        if not os.path.exists("agents"):
            try:
                os.mkdir("agents")
            except Exception as e:
                raise HTTPException(status_code=409, detail=f"Failed to create a directory for agent addition. Reason: {str(e)}")

        agent_path = os.path.basename(os.path.normpath(url_path[2]))

        final_url = urlunparse(url_path)
        git_info = subprocess.run(['git', 'clone', final_url, f"agents/{agent_path}"], capture_output=True, text=True)
        if git_info.returncode != 0:
            raise HTTPException(status_code=409, detail=f"Failed to clone the repository at address '{final_url}'. Reason: {git_info.stderr}")

        # Rewrite the path to point to the local code
        local_path = f"agents/{agent_path}"
    # It's a local path
    else:
        local_path = url2pathname(urlunparse(url_path))
        if not os.path.exists(local_path):
            raise HTTPException(status_code=409, detail=f"Required path does not exist '{local_path}'.")

    # At this point, agent's code should reside somewhere on the disk
    pip_command = ['pip', 'install']
    if agent.editable:
        pip_command.append('-e')
    pip_command.append(local_path)

    old_packages = await list_agents()

    pip_info = subprocess.run(pip_command, capture_output=True, text=True)
    if pip_info.returncode != 0:
        raise HTTPException(status_code=409, detail=f"Failed to install the required agent. Reason: '{pip_info.stderr}'.")

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


@router.post("/remove", status_code=status.HTTP_201_CREATED)
async def remove_agent(remove: AgentRemoval) -> Dict:
    result = {}
    by_package = {}
    module_to_remove = ""

    agents = await list_agents()

    # Gather modules by package for dependencies
    for agent in agents:
        if not agent.package_name in by_package:
            by_package[agent.package_name] = []

        if agent.module_name == remove.name:
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
    pip_command = ['pip', 'uninstall', '-y', module_to_remove.package_name]
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
