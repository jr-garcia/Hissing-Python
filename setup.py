try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
      packages=['hissing'],
      name='Hissing Python',
      version='0.6',
      url='https://github.com/jr-garcia/Hissing-Python',
      license='MIT',
      author='Javier R. García',
      description='Simple sound system based on OpenAL.',
      install_requires=['pyal'])
