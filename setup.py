from setuptools import setup

setup(
    name='dashit_filter',
    version='2.0',
    description='Filter DASHit guides RNA sequences for quality and on/offtargets',
    author='David Dynerman',
    author_email='david.dynerman@czbiohub.org',
    packages=['dashit_filter'],
    entry_points={
        'console_scripts': [
            'dashit_filter=dashit_filter.dashit_filter:main',
        ],
    },    
)
