try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='rpi-dynamixel-ax12a',
    version='0.0.1',
    author='Kotochleb',
    author_email='krzy.wojciecho@gmail.com',
    license='MIT',
    description='Python library for Dynamixel AX12 servos with Raspberry Pi',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
    packages=['rpi_dynamixel_ax12a'],
    python_requires='>=3.6',
)
