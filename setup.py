from setuptools import setup, find_packages, find_namespace_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='dojo',
    version='0.1.0',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Milan Boháček et al.',
    author_email='244656@muni.cz',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Security',
        'Typing :: Typed',

        # Pick your license as you wish
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent'
    ],
    packages=find_packages(
        exclude=['tests', 'scenarios']
    ) + find_namespace_packages(
        include=['cyst_models.*', 'cyst_services.*']
    ),
    python_requires='>=3.11, <4',
    install_requires=[
        'uvicorn >= 0.34.0',
        'fastapi >= 0.115.6',
        'httpx >= 0.28.1',
        'cyst-core',
        'cyst-models-dojo-cryton',
        'cyst-agents-netsecenv'
    ],
    entry_points={
    }
)
