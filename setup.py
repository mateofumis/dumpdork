from setuptools import setup, find_packages

setup(
    name='dumpdork',
    version='0.1.4.post1',
    packages=find_packages(),
    install_requires=[
        'colorama==0.4.6',
        'PyYAML==6.0.1',
        'requests==2.32.3',
    ],
    entry_points={
        'console_scripts': [
            'dumpdork=dumpdork:main',
        ],
    },
    description='A powerful command-line tool for Google dorking, enabling users to uncover hidden information and vulnerabilities with advanced search queries.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mateofumis/dumpdork',
    author='Mateo Fumis',
    author_email='mateofumis1@gmail.com',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
