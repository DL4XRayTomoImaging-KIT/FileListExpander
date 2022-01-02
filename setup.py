import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flexpand", # Replace with your own username
    version="0.0.2",
    author="Yaroslav Zharov",
    author_email="mart.slaaf@gmail.com",
    description="Utility to expand file names.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MartSlaaf/FileListExpander",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
