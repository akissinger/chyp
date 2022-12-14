# type: ignore
import setuptools

# read description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


data_files = []

setuptools.setup(
    name="chyp",
    version="0.1",
    author="Aleks Kissinger",
    author_email="aleks0@gmail.com",
    description="A compositional hypergraph library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akissinger/chyp",
    project_urls={
        "Bug Tracker": "https://github.com/akissinger/chyp/issues",
    },
    license="Apache2",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=["chyp"],
    package_data={'': ['*.svg']},
    data_files=data_files,
    install_requires=["PyQt6>=6.2"],
    python_requires=">=3.7",
    entry_points={'console_scripts': 'chyp=chyp.app:main'},
)
