from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="jixian-xiuxian",
    version="2.0.0",
    author="Your Name",
    author_email="1772305619@qq.com",
    description="极简修仙 - 一款基于Python和Pygame开发的修仙题材文字RPG游戏",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hhhh124hhhh/jixian-xiuxian",
    project_urls={
        "Bug Tracker": "https://github.com/hhhh124hhhh/jixian-xiuxian/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    package_dir={"": "versions/v2.0-enterprise"},
    packages=find_packages(where="versions/v2.0-enterprise"),
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "jixian-xiuxian=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md"],
    },
)