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
      version='0.5.0',
      description=('A docassemble extension, to view stats from other interviews'),
      long_description="# docassemble.InterviewStats\r\n\r\nA docassemble interview that lets you view statistics from other saved interview responses. \r\n\r\n## Getting Started\r\n\r\n1. Pull this package into your [docassemble playground](https://docassemble.org/docs/playground.html), or install it on your [docassemble server](https://docassemble.org/docs/packages.html).\r\n1. To generate data that this interview can consume, use the [store_variables_snapshot()](https://docassemble.org/docs/functions.html#store_variables_snapshot) function in your interview, i.e.  `store_variables_snapshot(data={'zip': users[0].address.zip})`.\r\n1. Once you have reached the `store_variables_snapshot` point in your target interview, start the stats interview.\r\n  1. If you're in the playground, run the `stats.yml` interview.\r\n  1. If you installed the package, go to the `/start/InterviewStats/stats/` URL to start the interview.\r\n1. Select the target interview in the drop down. \r\n1. You can export the data in a Excel format by clicking the `Download` link on the stats page.\r\n\r\n## Anonymous stats\r\n\r\nIf you would like to provide login-less access to stats for an interview\r\nin your `dispatch` directive, you can do so as follows:\r\n\r\n1. Add a directive in your configuration file, like this: \r\n```yaml\r\nstats subscriptions:\r\n  - cdc_moratorium: 12345abcedfg17821309\r\n  - 209a: 4859123jkljsafdsf0913132\r\n```\r\n\r\nWhere the value on the left corresponds to the key of an entry in your\r\n`dispatch` directive, and the value on the right is an arbitrary password you\r\ncreate. I recommend using something like https://onlinehashtools.com/generate-random-md5-hash\r\nto create a random password to control access.\r\n\r\nYou can add as many unique passwords as you want for each entry you share.\r\nThis means you can distribute multiple links without sharing the password.\r\n\r\nThen, someone can access the link to a specific interview's stats by \r\nvisiting this url:\r\n\r\n/start/InterviewStats/subscribe/?link=cdc_moratorium&auth=12345abcedfg17821309\r\n\r\nThey will be directed immediately to download an XlSX file containing the\r\nstatistics.\r\n\r\n## Example\r\n\r\n![Example Pic](static/example_pic.png)\r\n\r\n\r\n## Roadmap\r\n\r\nCurrently, we can show simple grouping over all the data points in the interview stats. However, the\r\nspecial visualization are only shown on based on the `zip` attribute. We're working to expand the\r\nfeatures available here in conjunction with our [EFiling Integration](https://github.com/SuffolkLITLab/EfileProxyServer).\r\n\r\nIf you have specific feature requests, feel free to open an issue or make a PR!\r\n\r\n\r\n## Authors\r\n\r\n* Quinten Steenhuis\r\n* Bryce Willey\r\n\r\n",
      long_description_content_type='text/markdown',
      author='Bryce Willey, Quinten Steenhuis',
      author_email='bwilley@suffolk.com',
      license='The MIT License (MIT)',
      url='https://courtformsonline.org/about/',
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=['bokeh>=2.4.2', 'cenpy>=1.0.0.post4', 'geopandas>=0.1.0.dev-120828c', 'numpy>=1.0.4', 'pandas>=1.4.2', 'requests>=2.27.1'],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/InterviewStats/', package='docassemble.InterviewStats'),
     )

