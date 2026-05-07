#!/bin/bash
# If the py venv exists then activate it, otherwise create it and then activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment. Use 'deactivate' to exit."
    source venv/bin/activate
else
    echo "Creating python virtual environment and installing dependencies..."
    python3 -m venv venv
    source venv/bin/activate

    # Install the required packages
    pip install numpy scipy matplotlib ipython pandas pyarrow cmsstyle

    # Install pytimber
    pip install git+https://gitlab.cern.ch/acc-co/devops/python/acc-py-pip-config.git
    pip install pytimber
    pip uninstall acc-py-pip-config

    echo "Python virtual environment setup complete. Use 'deactivate' to exit."
fi