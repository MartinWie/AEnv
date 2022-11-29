from setuptools import setup


def readme():
    with open('README.md', "r", encoding='utf-8') as f:
        return f.read()


setup(name='aenv',
      version='2.0.0',
      description='A Python 3 tool to fetch secure strings from the aws parameter store and injecting those into environment variables.',
      long_description=readme(),
      long_description_content_type='text/markdown',
      download_url='https://github.com/MartinWie/AEnv/archive/2.0.0.tar.gz',
      entry_points={
          'console_scripts': [
              'aenv=aenv.aenv:main'
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
      url='https://github.com/MartinWie/AEnv',
      author='MartinWiechmann',
      author_email='martin.wiechmann.office@gmail.com',
      keywords='aws credo security parameterstore ssm cloud password aenv',
      license='MIT',
      packages=['aenv'],
      install_requires=[
          'boto3'
      ],
      include_package_data=True,
      zip_safe=False)
