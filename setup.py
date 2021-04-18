
from setuptools import setup, find_packages

setup(name='scanSelect',
      version='1.0',
      description='Select specified scans and precursors in from mzML file.',
      author='Aaron Maurais',
      url='https://github.com/ajmaurais/scanSelect',
      classifiers=['Development Status :: 4 - Beta',
        'Intended Audience :: SCIENCE/RESEARCH',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        ],
      packages=find_packages(),
      package_dir={'scanSelect':'scanSelect'},
      python_requires='>=3.6.*',
      install_requires=['pandas>=1.0', 'pyopenms>=2.4.0'],
      entry_points={'console_scripts': ['scanSelect=scanSelect:main']},
)


