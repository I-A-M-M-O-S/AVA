from setuptools import find_packages
from setuptools import setup

setup(
    name='avaj_car_control',
    version='0.1.0',
    packages=find_packages(
        include=('avaj_car_control', 'avaj_car_control.*')),
)
