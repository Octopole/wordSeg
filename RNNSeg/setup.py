from distutils.core import setup
from setuptools import find_packages

setup(name='rnn', version='1.0', author='lle', packages = find_packages(), package_data = {'': ['cws.info'], '':['keras_model_weights'], '':['cws_keras_model']})