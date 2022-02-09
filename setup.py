import setuptools

with open("README.md", 'r', encoding='utf-8') as fh:
  long_description = fh.read()
  
 setuptools.setup(
   name='Operation_and_Control',
   version='0.0.1',
   author='Job Augustijn van der Werf',
   author_email = 'j.a.vanderwerf@tudelft.nl',
   description= 'Used for the ENVM1601 course at TU Delft',
   long_description = long_description,
   long_description_content_type = "text/markdown",
   url='https://github.com/jobvanderwerf/TUDelft_ENVM1601',
   license='MIT',
   packages=['Operation_and_Control'],
   install_requires=['requests'],
 )
