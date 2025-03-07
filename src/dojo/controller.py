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
from typing import Any, Optional
from threading import Thread
from pathlib import Path


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
    def __init__(self, platform: PlatformSpecification, id: str | None, configuration: str):
        if not id:
            self._id = uuid.uuid4()
        else:
            self._id = id

        self._platform = platform

        self._configuration = configuration

        self._pipe_parent, self._pipe_child = Pipe()
        self._process = Process(target=self.loop, args=(self._id, self._platform, self._configuration, self._pipe_child))
        self._lock = Lock()

    @property
    def id(self) -> str:
        return self._id

    @property
    def platform(self) -> PlatformSpecification:
        return self._platform

    @property
    def configuration(self) -> str:
        return self._configuration

    async def start(self) -> ActionResponse:
        with self._lock:
            self._process.start()
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

    @staticmethod
    def loop(id: str, platform: PlatformSpecification, configuration: str, pipe: connection.Connection):
        environment_thread = None

        try:
            environment = Environment.create(platform)
            if configuration:
                environment.configure(*environment.configuration.general.load_configuration(configuration))
            pipe.send(ActionResponse(id, EnvironmentState.CREATED.name, True, f"Environment successfully created.", environment.configuration.general.save_configuration(2)))
        except:
            if configuration:
                message = "Failed to create and configure the environment."
            else:
                message = "Failed to create the environment."
            pipe.send(ActionResponse(id, EnvironmentState.TERMINATED.name, False, message))
            return

        while True:
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
                            environment.configure(*environment.configuration.general.load_configuration(param))
                            response = ActionResponse(id, environment.control.state.name, True, "The environment was successfully configured.")
                        except Exception as e:
                            print(e)
                            response = ActionResponse(id, EnvironmentState.TERMINATED.name, False, "Failed to configure the environment.")
                    case EnvironmentAction.RUN:
                        # To make our life easier, we do a manual check if the thread is in init or paused state
                        if environment.control.state == EnvironmentState.INIT or environment.control.state == EnvironmentState.PAUSED:
                            environment_thread = Thread(target=environment.control.run)
                            environment_thread.start()

                            # give it a time to start (it should be fairly fast)
                            counter = 0
                            while counter < 10:
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
                        if environment_thread:
                            environment.control.terminate()
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
