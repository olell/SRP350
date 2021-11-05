from setuptools import setup

setup(
    name='srp350',
    version='0.1.0',    
    description='Bixolon SRP350 python driver',
    url='https://github.com/olell/SRP350',
    author='Ole Lange',
    author_email='srp350py@olel.de',
    license='Unlicense/Public Domain',
    packages=['srp350'],
    install_requires=['pillow'],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: The Unlicense (Unlicense)',  
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: System :: Hardware :: Universal Serial Bus (USB) :: Printer'
    ],
)
