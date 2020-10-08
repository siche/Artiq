CONDA_ENV_NAME = "artiq"
# The conda packages to download and install.
CONDA_PACKAGES = [
    "artiq",
    "artiq-board-kc705-nist_clock",
    "artiq-board-kasli-tsinghua"
    
]
# Set to False if you have already set up conda channels
ADD_CHANNELS = True

# PROXY: If you are behind a web proxy, configure it in your .condarc (as per
# the conda manual).

# You should not need to modify the rest of the script below.

import os

def run(command):
    r = os.system(command)
    if r != 0:
        raise SystemExit("command '{}' returned non-zero exit status: {}".format(command, r))

if ADD_CHANNELS:
    run("conda config --prepend channels m-labs")
    run("conda config --prepend channels https://conda.m-labs.hk/artiq-beta")
    run("conda config --append channels conda-forge")

# Creating the environment first with python 3.5 hits fewer bugs in conda's broken dependency solver.
run("conda create -y -n {CONDA_ENV_NAME} python=3.5".format(CONDA_ENV_NAME=CONDA_ENV_NAME))
for package in CONDA_PACKAGES:
    # Do not activate the environment yet - otherwise "conda install" may not find the SSL module anymore on Windows.
    # Installing into the environment from the outside works around this conda bug.
    run("conda install -y -n {CONDA_ENV_NAME} -c https://conda.m-labs.hk/artiq-beta {package}"
        .format(CONDA_ENV_NAME=CONDA_ENV_NAME, package=package))