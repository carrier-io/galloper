#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='Galloper',
    version='1.0.0',
    description='Core component',
    long_description='Galloper module for execution of stateless tasks',
    url='https://getcarrier.io',
    license='Apache License 2.0',
    author='arozumenko',
    author_email='artem_rozumenko@epam.com',
    packages=find_packages(),
    install_requires=required,
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'celery_app=galloper.celeryapp:main',
            'app=galloper.app:main',
            'superconf=galloper.utils.config_supervisor:main',
            'galloper_uwsgiconf=galloper.utils.config_uwsgi:main',
        ]
    },
)
