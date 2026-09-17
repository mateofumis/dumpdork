from setuptools import setup, find_packages

setup(
    name='dumpdork',
    version='2.0.0',
    packages=find_packages(),
    install_requires=[
        'colorama==0.4.6',
        'PyYAML==6.0.2',
        'requests==2.32.3',
    ],
    entry_points={
        'console_scripts': [
            'dumpdork=dumpdork:main',
        ],
    },
    description='A small, search-driven OSINT and reconnaissance command-line framework.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/mateofumis/dumpdork',
    author='Mateo Fumis',
    author_email='mateofumis@mfumis.com',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)
