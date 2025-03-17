import pathlib

PATH_PROJECT_ROOT = pathlib.Path(__file__).absolute().parent.parent.parent
PATH_CONFIGURATIONS = PATH_PROJECT_ROOT.joinpath("dojo", "configurations")
