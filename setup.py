import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'setuptools',
    'prettytable',
    'sh',
]

setup(name='maxscripts',
      version='1.1',
      description='maxscripts',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="maxscripts",
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      initialize_max_db = maxscripts.security:main
      max.devel = maxscripts.devel:main
      maxui.setup = maxscripts.maxui:main
      max.report = maxscripts.report:main
      max.cloudapis = maxscripts.cloudapis:main
      """,
      )
