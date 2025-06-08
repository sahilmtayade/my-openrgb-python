from setuptools import find_packages, setup

setup(
    name="rgb_startup_controller",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openrgb-python",
        "requests",
        "jsonschema",
        "python-dotenv",
        "numpy",
        "colour-science",
        "logger_tt",
    ],
    entry_points={
        "console_scripts": [
            "rgb-startup-controller = src.main:run",
        ],
    },
    python_requires=">=3.7",
)
