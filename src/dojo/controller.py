from cyst.api.environment.environment import Environment
from cyst.api.environment.control import EnvironmentState
from cyst.api.environment.platform_specification import PlatformSpecification

from asyncio import to_thread
from fastapi import HTTPException
from multiprocessing import Process, Pipe, connection, Lock
from enum import StrEnum, auto


class EnvironmentAction(StrEnum):
    INIT = auto()
    TERMINATE = auto()
    RUN = auto()
    COMMIT = auto()
    PAUSE = auto()
    RESET = auto()
    GET_STATE = auto()


class EnvironmentWrapper:
    def __init__(self, platform: PlatformSpecification, name: str, configuration: str):
        self.name = name
        self.platform = platform
        self.configuration = configuration

        self._pipe_parent, self._pipe_child = Pipe()
        self._process = Process(target=self.loop, args=(self.platform, self.configuration, self._pipe_child))
        self._lock = Lock()

    async def perform_action(self, action: EnvironmentAction | None):
        with self._lock:
            self._pipe_parent.send(action)
            response: tuple[bool, EnvironmentState] = await to_thread(self._pipe_parent.recv)

        if response and not response[0]:
            raise HTTPException(status_code=409, detail={"state": response[1].name})
        return response

    def start(self):
        self._process.start()

    @staticmethod
    def loop(platform: PlatformSpecification, configuration: str, pipe: connection.Connection):
        environment = Environment.create(platform)
        environment.configure(*environment.configuration.general.load_configuration(configuration))

        while True:  # TODO: env state could be used instead of manual shutdown
            action: EnvironmentAction | None = pipe.recv()
            match action:
                case EnvironmentAction.INIT:
                    response = environment.control.init()
                case EnvironmentAction.RUN:
                    response = environment.control.run()
                case EnvironmentAction.RESET:
                    response = environment.control.reset()
                case EnvironmentAction.COMMIT:
                    response = environment.control.commit()
                case EnvironmentAction.PAUSE:
                    response = environment.control.pause()
                case EnvironmentAction.TERMINATE:
                    response = environment.control.terminate()
                case EnvironmentAction.GET_STATE:
                    response = environment.control.state.name
                case _:
                    response = None

            pipe.send(response)
            if not response:
                break


environments: dict[str, EnvironmentWrapper] = dict()
