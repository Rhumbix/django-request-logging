from setuptools import setup

setup(name='django-request-logging',
      version='0.6.2',
      description='Django middleware that logs http request body.',
      url='https://github.com/Rhumbix/django-request-logging.git',
      author='Rhumbix',
      author_email='devteam@rhumbix.com',
      license='MIT',
      packages=['request_logging'],
      install_requires=[
          'Django',
      ],
      zip_safe=False)
