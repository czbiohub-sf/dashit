from setuptools import setup

setup(
    name='dashit_seq',
    version='1.0',
    description='DASHit-seq',
    author='David Dynerman',
    author_email='david.dynerman@czbiohub.org',
    packages=['dashit_seq'],
    entry_points={
        'console_scripts': [
            'dashit-seq=dashit_seq:dashit_seq',
        ],
    },    
)
