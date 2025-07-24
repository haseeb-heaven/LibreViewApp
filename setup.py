from setuptools import setup, find_packages

setup(
    name="libreapp",
    version="1.1.0",
    packages=find_packages(include=['libreapp', 'libreapp.*']),
    install_requires=[
        "requests>=2.32.4",
        "python-dotenv>=1.1.1"
    ],
    python_requires=">=3.7",
)
