# type: ignore
import setuptools

# read description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


data_files = []

setuptools.setup(
    name="chyp",
    version="0.4.1",
    author="Aleks Kissinger",
    author_email="aleks0@gmail.com",
    description="An interactive theorem prover for string diagrams",
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
    packages=["chyp", "chyp.gui"],
    package_data={'': ['*.svg']},
    data_files=data_files,
    install_requires=["PySide6>=6.4.3", "lark>=1.1.5", "cvxpy>=1.3.1"],
    python_requires=">=3.7",
    entry_points={'console_scripts': 'chyp=chyp.gui.app:main'},
)
