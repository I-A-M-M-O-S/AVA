"""Setuptools configuration for the AVAJ racing-path utilities."""

from pathlib import Path

from setuptools import find_packages, setup


package_name = 'avaj_racing'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/data',
         [str(path) for path in Path('data').glob('*.csv')]),
    ],
    install_requires=['setuptools'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='avaj',
    maintainer_email='avaj@example.com',
    description='Offline reference-path import and validation for AVAJ racing.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'reference_path_importer = avaj_racing.reference_path_importer:main',
        ],
    },
)
