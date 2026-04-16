import glob

from setuptools import find_packages, setup

package_name = "blue_sim"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob.glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ubuntu",
    maintainer_email="alanchoi.uni@gmail.com",
    description="Simulation launch and ArduSub interface nodes for BlueROV2",
    license="Apache-2.0",
    extras_require={},
    entry_points={
        "console_scripts": [
            "ardusub_bridge = blue_sim.ardusub_bridge:main",
            "ardusub_init = blue_sim.ardusub_init:main",
        ],
    },
)
