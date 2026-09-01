from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'avaj_sensor_processing'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='avaj',
    maintainer_email='avaj@example.com',
    description='Canonical LiDAR and IMU preprocessing for AVAJ.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'imu_preprocessor = '
            'avaj_sensor_processing.imu_preprocessor:main',
            'scan_preprocessor = '
            'avaj_sensor_processing.scan_preprocessor:main',
        ],
    },
)
