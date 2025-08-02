from setuptools import setup, find_packages

setup(
    name='vllm-top',
    version='0.1.0',
    author='Yeok Tatt Cheah',
    author_email='yeokch@gmail.com',
    description='A monitoring tool for vLLM metrics',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yeok-c/vllm-top',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        'requests',
        'prometheus_client',
    ],
)