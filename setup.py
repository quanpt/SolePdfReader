from cx_Freeze import setup, Executable

excludes = []
includefiles = [('/usr/lib/libblas.so.3', 'libblas.so.3'), \
      ('/usr/lib/liblapack.so.3', 'liblapack.so.3'), 'pdf']
packages = ['scipy', 'numpy', 'PyQt4', 'PyPDF2']

executables = [
    Executable('main.py')
]

buildOptions = {'packages':['scipy', 'numpy', 'PyQt4', 'PyPDF2']}

setup(name='SoleGui',
      version = '0.17',
      description = '',
      options = {'build_exe': {'excludes':excludes,'packages':packages,'include_files':includefiles}}, 
      executables = executables)
