from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='django-request-logging',
    version='0.6.6',
    description='Django middleware that logs http request body.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Rhumbix/django-request-logging.git',
    author='Rhumbix',
    author_email='dev@rhumbix.com',
    license='MIT',
    packages=['request_logging'],
    install_requires=[
        'Django',
    ],
    zip_safe=False
)
