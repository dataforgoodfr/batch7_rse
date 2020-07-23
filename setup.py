from setuptools import setup, find_packages

setup(
    name='rse-explorer',
    author='Charles Gaydon',
    author_email='charles.gaydon@gmail.com',

    packages=find_packages(),
    include_package_data=True,
    scripts=['webapp/manage.py'],
)