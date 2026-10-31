# -*- coding: utf-8 -*-

from distutils.core import setup
import setup_translate

pkg = 'Extensions.OpenWebif'
setup(name='enigma2-plugin-extensions-openwebif',
	description='Control your receiver with a browser',
	packages=[],
	cmdclass=setup_translate.cmdclass,
)
