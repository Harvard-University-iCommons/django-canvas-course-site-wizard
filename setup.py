import os
from setuptools import setup, find_packages

version_file = open(os.path.join(os.path.dirname(__file__), 'VERSION'))
version = version_file.read().strip()
README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-canvas-course-site-wizard',
    version=version,
    packages=find_packages(),
    include_package_data=True,
    license='TBD License',  # example license
    description='A Django app for managing the process of creating course sites for Canvas LMS.',
    long_description=README,
    url='http://icommons.harvard.edu/',
    author='Jaime Bermudez',
    author_email='jaime_bermudez@harvard.edu',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        "Django>=2.2,<3.0",
        "django-braces",
        "canvas-python-sdk>=1.0",
        "django-icommons-common[async_operations]>=2.0",
    ],
    tests_require=[
        'mock',
    ],
    zip_safe=False,
)
