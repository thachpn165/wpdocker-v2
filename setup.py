from setuptools import setup, find_packages

setup(
    name="wpdocker",
    version="2.0.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        # Các thư viện dependency sẽ được đọc từ requirements.txt
    ],
)