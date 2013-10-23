try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import trc_me

packages = [
    'trc_me',
    'trc_me.accounts',
    'trc_me.api',
    'trc_me.api.auth',
    'trc_me.core',
    'trc_me.flagcomments',
    'trc_me.web',
]

requires = [
    'Django',
    'django-piston',
    'django-richcomments',
    'django-stdimage',
    'django-tagging',
    'httplib2',
    'python-Levenshtein',
    'subhub',
]

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name='trc_me',
    version=trc_me.__version__,
    description='trc.me is a tool for crowdsourcing the geolocation of objects.',
    long_description=long_description,
    author='Norman Hooper',
    author_email='norman@kaapstorm.com',
    url='http://trc.me/',
    license='GNU Affero General Public License',
    packages=packages,
    package_dir={'': 'src'},
    install_requires=requires,
    setup_requires=['sphinx'],
)
