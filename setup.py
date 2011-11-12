
from distutils.core import setup, Extension

pkg = 'Extensions.SimpleUmount'
setup (name = 'enigma2-plugin-extensions-simpleumount',
       version = '0.04',
       description = 'Simple umounter mass storage device',
       package_dir = {pkg: 'plugin'},
       packages = [pkg]
       )

