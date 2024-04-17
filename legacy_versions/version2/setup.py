from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as f:
    install_requires = f.read().splitlines()

setup(
    name='Shift Scheduler',
    version='0.1',
    author='Patipan Sitthiprawiat',
    author_email='patipan120897@gmail.com',
    description='[...]',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='[...https://github.com/yourusername/yourpackage...]',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Office/Business :: Scheduling'
    ],
    python_requires='>=3.9.15',
    install_requires=install_requires,
)
