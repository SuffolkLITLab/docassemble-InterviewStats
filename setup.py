import os
import sys
from setuptools import setup, find_packages
from fnmatch import fnmatchcase
from distutils.util import convert_path

standard_exclude = ('*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build', './dist', 'EGG-INFO', '*.egg-info')
def find_package_data(where='.', package='', exclude=standard_exclude, exclude_directories=standard_exclude_directories):
    out = {}
    stack = [(convert_path(where), '', package)]
    while stack:
        where, prefix, package = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                        stack.append((fn, '', new_package))
                else:
                    stack.append((fn, prefix + name + '/', package))
            else:
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out

setup(name='docassemble.InterviewStats',
      version='0.0.9',
      description=('A docassemble extension, to view stats from other interviews'),
      long_description='# docassemble.InterviewStats\r\n\r\nA docassemble interview that lets you view statistics from other saved interview responses. \r\n\r\n## Author\r\n\r\nQuinten Steenhuis\r\nBryce Willey\r\n\r\n',
      long_description_content_type='text/markdown',
      author='Bryce Willey, Quinten Steenhuis',
      author_email='bwilley@suffolk.com',
      license='The MIT License (MIT)',
      url='https://courtformsonline.org/about/',
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=[
        'bokeh==2.3.0',  # Needs an explicit version: otherwise JS and python will mismatch
        'cenpy>=1.0.0.post4', 'geopandas>=0.1.0.dev-120828c',
        'pandas>=1.1.4', 'numpy>=1.19.4', 'requests>=2.25.0'],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/InterviewStats/', package='docassemble.InterviewStats'),
     )

