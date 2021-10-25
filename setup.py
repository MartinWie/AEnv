from setuptools import setup


def readme():
    with open('README.md', "r", encoding='utf-8') as f:
        return f.read()


setup(name='credopy',
      version='1.1.3',
      description='A Python 3 tool to fetch secure strings from aws parameter store and injecting those into environment variables.',
      long_description=readme(),
      long_description_content_type='text/markdown',
      download_url='https://github.com/MartinWie/CredoPy/archive/1.1.3.tar.gz',
      entry_points={
          'console_scripts': [
              'pydo=credopy.credopy:main'
          ]
      },
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Topic :: Security',
          'Operating System :: OS Independent'
      ],
      url='https://github.com/MartinWie/CredoPy',
      author='MartinWiechmann',
      author_email='martin.wiechmann.office@gmail.com',
      keywords='aws credo security parameterstore ssm cloud password pydo credopy',
      license='MIT',
      packages=['credopy'],
      install_requires=[
          'boto3'
      ],
      include_package_data=True,
      zip_safe=False)
