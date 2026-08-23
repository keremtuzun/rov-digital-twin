from setuptools import find_packages, setup

package_name = "rov_dt_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ROV Digital Twin Team",
    maintainer_email="maintainer@example.com",
    description="Unity ROV telemetry and high-level command bridge",
    license="MIT",
    entry_points={
        "console_scripts": [
            "diagnostic_node = rov_dt_bridge.diagnostic_node:main",
            "unity_udp_bridge = rov_dt_bridge.unity_udp_bridge:main",
        ]
    },
)
