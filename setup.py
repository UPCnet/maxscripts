import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'setuptools',
    'maxclient',
    'maxcarrot',
    'prettytable',
    'sh',
    'haigha',
    'docopt',
    'pymongo',
    'utalk-python-client'
]

setup(name='maxscripts',
      version='4.0.3',
      description='maxscripts',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='UPCnet Plone Team',
      author_email='plone.team@upcnet.es',
      url='https://github.com/upcnet/maxscripts',
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
      max.rabbit = maxscripts.rabbitmq:main
      max.newinstance = maxscripts.newinstance:main
      max.mongoindexes = maxscripts.mongoindexes:main
      max.loadtest = maxscripts.loadtest:main
      """,
      )
