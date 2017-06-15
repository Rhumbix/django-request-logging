from setuptools import setup

setup(name='django-request-logging',
      version='0.5.0',
      description='Django middleware that logs http request body.',
      url='https://github.com/Rhumbix/django-request-logging.git',
      author='Kenneth Jiang',
      author_email='kenneth@rhumbix.com',
      license='MIT',
      packages=['request_logging'],
      install_requires=[
          'Django',
      ],
      zip_safe=False)
