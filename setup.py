from setuptools import setup

setup(name='teaser',
      version='0.2.4',
      description='Tool for Energy Analysis and Simulation for Efficient Retrofit ',
      url='https://github.com/RWTH-EBC/TEASER',
      author='TEASER Development Team',
      author_email='teaser@eonerc.rwth-aachen.de',
      license='MIT',
      packages=['teaser'],
      setup_requires = ['mako', 'PyXB', 'pytest'],
      install_requires = ['mako', 'PyXB', 'pytest'])