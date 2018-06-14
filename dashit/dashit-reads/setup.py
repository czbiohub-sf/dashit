from setuptools import setup

setup(
    name='dashit_reads',
    version='1.0',
    description='DASHit-reads',
    author='David Dynerman',
    author_email='david.dynerman@czbiohub.org',
    packages=['dashit_reads'],
    entry_points={
        'console_scripts': [
            'dashit-reads-filter=dashit_reads.dashit_reads_filter:main',
        ],
    },    
)
