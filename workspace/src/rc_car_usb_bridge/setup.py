from setuptools import find_packages, setup


package_name = 'rc_car_usb_bridge'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='avaj',
    maintainer_email='avaj@example.com',
    description='Validated ROS 2 DriveCommand to ESP32 USB serial bridge.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'usb_bridge = rc_car_usb_bridge.usb_bridge:main',
        ],
    },
)
