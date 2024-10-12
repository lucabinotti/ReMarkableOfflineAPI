from setuptools import setup, find_packages

setup(
    name="remarkable_offline_api",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    author="Luca Binotti",
    description="An offline API for managing and downloading files directly from the reMarkable tablet.",
    url="https://github.com/lucabinotti/ReMarkableOfflineAPI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)