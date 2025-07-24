from setuptools import setup, find_packages

setup(
    name="libreapp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.32.4",
        "python-dotenv>=1.1.1"
    ],
)
