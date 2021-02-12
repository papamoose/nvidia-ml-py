from distutils.core import setup
from sys import version

# earlier versions don't support all classifiers
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

setup(name='nvidia-ml-py',
      version='3.295.02',
      description='Python Bindings for the NVIDIA Management Library',
      py_modules=['pynvml', 'nvidia_smi'],
      license="BSD",
      url="http://www.nvidia.com/",
      author="NVIDIA Corporation",
      author_email="nvml-bindings@nvidia.com",
      classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware',
        'Topic :: System :: Systems Administration',
        ],
      )
