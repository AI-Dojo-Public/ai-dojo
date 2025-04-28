import asyncio
import contextlib
import io
import os
import socket
import sys
import uuid
import time

from cyst.api.environment.environment import Environment
from cyst.api.environment.control import EnvironmentState
from cyst.api.environment.platform_specification import PlatformSpecification

from asyncio import to_thread
from dataclasses import dataclass, asdict
from fastapi import HTTPException
from multiprocessing import Process, Pipe, connection, Lock
from enum import StrEnum, auto
from typing import Any, Optional, Dict
from threading import Thread
from pathlib import Path
from dojo.api.endpoints.socket_manager import socket_manager


@contextlib.contextmanager
def pipe_redirector(pipe_conn):
    class PipeWriter:
        def __init__(self, original_stdout):
            self.original_stdout = original_stdout

        def write(self, msg):
            try:
                if msg.strip():  # Avoid sending pure newlines if you want
                    pipe_conn.send(msg)
                self.original_stdout.write(msg)  # Also print to the original stdout
            except Exception:
                pass

        def flush(self):
            try:
                self.original_stdout.flush()
            except Exception:
                pass

    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = PipeWriter(old_stdout)

    try:
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class EnvironmentAction(StrEnum):
    INIT = auto()
    CONFIGURE = auto()
    TERMINATE = auto()
    RUN = auto()
    COMMIT = auto()
    PAUSE = auto()
    RESET = auto()
    GET_STATE = auto()


@dataclass
class ActionResponse:
    id: str
    state: str
    success: bool
    message: str
    aux: Optional[str] = None


class EnvironmentWrapper:
    def __init__(self, platform: PlatformSpecification, id: str | None, configuration: str, parameters: Optional[Dict[str, Any]], agent_manager_port: int = 8282):
        if not id:
            self._id = str(uuid.uuid4())
        else:
            self._id = id

        self._platform = platform

        self._configuration = configuration
        self._parameters = parameters

        self._pipe_parent, self._pipe_child = Pipe()
        self._stdout_pipe_parent, self._stdout_pipe_child = Pipe()
        self._process = Process(target=self.loop, args=(self._id, self._platform, self._configuration, self._parameters, self._pipe_child, self._stdout_pipe_child))
        self._lock = Lock()
        self.agent_manager_port: int = agent_manager_port

    @property
    def id(self) -> str:
        return self._id

    @property
    def platform(self) -> PlatformSpecification:
        return self._platform

    @property
    def configuration(self) -> str:
        return self._configuration

    def start_stdout_listener(self):
        loop = asyncio.get_event_loop()

        def listen():
            while self._process.is_alive():
                if self._stdout_pipe_parent.poll():
                    msg = self._stdout_pipe_parent.recv()
                    asyncio.run_coroutine_threadsafe(socket_manager.send_personal_message(msg, self.id), loop)

        Thread(target=listen, daemon=True).start()

    async def start(self) -> ActionResponse:
        os.environ["CYST_AGENT_ENV_MANAGER_PORT"] = str(self.agent_manager_port)
        with self._lock:
            self._process.start()
            self.start_stdout_listener()
            response: ActionResponse = await to_thread(self._pipe_parent.recv)

        if response and not response.success:
            raise HTTPException(status_code=409, detail=asdict(response))
        return response

    async def perform_action(self, action: EnvironmentAction | None, param: Any = None) -> ActionResponse:
        if not self._process.is_alive():
            del environments[self._id]
            return ActionResponse(self._id, EnvironmentState.TERMINATED.name, False, f"The environment is already terminated.")

        with self._lock:
            self._pipe_parent.send((action, param))
            response: ActionResponse = await to_thread(self._pipe_parent.recv)

        if response and not response.success:
            raise HTTPException(status_code=409, detail=asdict(response))
        return response

    def loop(self, id: str, platform: PlatformSpecification, configuration: str, parameters: Optional[Dict[str, Any]], pipe: connection.Connection, stdout_pipe: connection.Connection):
        with pipe_redirector(stdout_pipe):
            environment_thread = None

            try:
                environment = Environment.create(platform)
                if configuration:
                    environment.configure(*environment.configuration.general.load_configuration(configuration), parameters=parameters)
                pipe.send(ActionResponse(id, EnvironmentState.CREATED.name, True, f"Environment successfully created.", environment.configuration.general.save_configuration(2)))
            except Exception as e:
                if configuration:
                    message = f"Failed to create and configure the environment. Reason: {e}"
                else:
                    message = f"Failed to create the environment. Reason: {e}"
                pipe.send(ActionResponse(id, EnvironmentState.TERMINATED.name, False, message))
                return


            while True:
                if not pipe.poll(1):  # Avoid blocking indefinitely
                    continue
                terminate = False
                try:
                    action: EnvironmentAction | None = None
                    param: Any = None
                    response = None

                    action, param = pipe.recv()

                    match action:
                        case EnvironmentAction.INIT:
                            e = environment.control.init()
                            response = ActionResponse(id, environment.control.state.name, e[0], "The environment was successfully initialized" if e[0] else "Failed to initialize the environment.")
                        case EnvironmentAction.CONFIGURE:
                            try:
                                environment.configure(*environment.configuration.general.load_configuration(self.configuration), parameters=param)
                                response = ActionResponse(id, environment.control.state.name, True, "The environment was successfully configured.")
                            except Exception as e:
                                response = ActionResponse(id, EnvironmentState.TERMINATED.name, False, "Failed to configure the environment.")
                        case EnvironmentAction.RUN:
                            # To make our life easier, we do a manual check if the thread is in init or paused state
                            if environment.control.state == EnvironmentState.INIT or environment.control.state == EnvironmentState.PAUSED:
                                environment_thread = Thread(target=environment.control.run)
                                environment_thread.start()

                                # give it a time to start (it should be fairly fast)
                                counter = 0
                                while counter < 20:
                                    if environment.control.state == EnvironmentState.INIT or environment.control.state == EnvironmentState.PAUSED:
                                        time.sleep(0.2)
                                    else:
                                        break

                                if environment.control.state == EnvironmentState.RUNNING:
                                    response = ActionResponse(id, EnvironmentState.RUNNING.name, True, "The environment is running.")
                                else:
                                    response = ActionResponse(id, environment.control.state.name, False, "Failed to run the environment.")
                            else:
                                response = ActionResponse(id, environment.control.state.name, False, "The environment is not in the state suitable for running.")
                        case EnvironmentAction.RESET:
                            e = environment.control.reset()
                            if e[0]:
                                response = ActionResponse(id, environment.control.state.name, True, "The environment was successfully reset.")
                            else:
                                response = ActionResponse(id, environment.control.state.name, False, "Failed to reset the environment.")
                        case EnvironmentAction.COMMIT:
                            if environment.control.state != EnvironmentState.FINISHED or environment.control.state != EnvironmentState.TERMINATED:
                                response = ActionResponse(id, environment.control.state.name, False, "The environment is not in a suitable state for commit.")
                            else:
                                environment.control.commit()
                                response = ActionResponse(id, environment.control.state.name, True, "The environment data was successfully committed.")
                        case EnvironmentAction.PAUSE:
                            e = environment.control.pause()
                            if e[0]:
                                response = ActionResponse(id, environment.control.state.name, True, "The environment was successfully paused.")
                            else:
                                if environment.control.state != EnvironmentState.RUNNING:
                                    response = ActionResponse(id, environment.control.state.name, False, "Failed to pause the environment, it is not in the running state.")
                                else:
                                    response = ActionResponse(id, environment.control.state.name, False, "Failed to pause the environment.")
                        case EnvironmentAction.TERMINATE:
                            environment.control.terminate()
                            if environment_thread:
                                # Environment has issues when terminating without running, so we just do our stuff and die
                                environment_thread.join()

                            response = ActionResponse(id, environment.control.state.name, True, "The environment was successfully terminated.")
                            terminate = True
                        case EnvironmentAction.GET_STATE:
                            response = ActionResponse(id, environment.control.state.name, True, "")

                    pipe.send(response)
                    if not response or terminate:
                        break

                except (KeyboardInterrupt, InterruptedError):
                    pass

                except BrokenPipeError:
                    environment.control.terminate()
                    break


environments: dict[str, EnvironmentWrapper] = dict()
