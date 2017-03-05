""" Setup file """
import os

from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, "README.rst")) as f:
    README = f.read()

with open(os.path.join(HERE, "CHANGELOG.rst")) as f:
    CHANGES = f.read()


def get_version():
    with open(os.path.join(HERE, "pqs/__init__.py")) as f:
        for line in f:
            if line.startswith("__version__"):
                return eval(line.split("=")[-1])

REQUIREMENTS = [
    "bloop==1.0.0",
    "click==6.7",
    "flask==0.12",
    "pendulum==1.1.0"
]

if __name__ == "__main__":
    setup(
        name="pqs",
        version=get_version(),
        description="The lovable PQS is back!",
        long_description=README + "\n\n" + CHANGES,
        entry_points={
            "console_scripts": [
                "pqs-cli = pqs.scripts.cli:main",
                "pqs-website = pqs.scripts.website:main"
            ]
        },
        author="Joe Cross",
        author_email="joe.mcross@gmail.com",
        url="https://github.com/numberoverzero/people-queue-service",
        license="MIT",
        platforms="any",
        include_package_data=True,
        packages=find_packages(),
        install_requires=REQUIREMENTS,
    )
