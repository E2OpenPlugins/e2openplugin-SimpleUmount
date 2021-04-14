from distutils.core import setup
import setup_translate

pkg = 'Extensions.SimpleUmount'
setup(name='enigma2-plugin-extensions-simpleumount',
	version='0.10',
	description='Simple umounter mass storage device',
	packages=[pkg],
	package_dir={pkg: 'plugin'},
	package_data={pkg: ['locale/*/LC_MESSAGES/*.mo', 'simpleumount.png']},
	cmdclass=setup_translate.cmdclass, # for translation
	)

