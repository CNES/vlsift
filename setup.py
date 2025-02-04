import os
import platform
import site

from setuptools import setup, find_packages, Extension

SYS_PLATFORM = platform.system().lower()
IS_LINUX = 'linux' in SYS_PLATFORM
IS_OSX = 'darwin' == SYS_PLATFORM
IS_WIN = 'windows' == SYS_PLATFORM

# Get Numpy include path without importing it
NUMPY_INC_PATHS = [os.path.join(r, 'numpy', 'core', 'include')
                   for r in site.getsitepackages() if
                   os.path.isdir(os.path.join(r, 'numpy', 'core', 'include'))]

if len(NUMPY_INC_PATHS) == 0:
    try:
        import numpy as np
    except ImportError:
        raise ValueError("Could not find numpy include dir and numpy not installed before build - "
                         "cannot proceed with compilation of cython modules.")
    else:
        # just ask numpy for it's include dir
        NUMPY_INC_PATHS = [np.get_include()]

elif len(NUMPY_INC_PATHS) > 1:
    print("Found {} numpy include dirs: "
          "{}".format(len(NUMPY_INC_PATHS), ', '.join(NUMPY_INC_PATHS)))
    print("Taking first (highest precedence on path): {}".format(
        NUMPY_INC_PATHS[0]))
NUMPY_INC_PATH = NUMPY_INC_PATHS[0]

# ---- C/C++ EXTENSIONS ---- #
# Stolen (and modified) from the Cython documentation:
#     http://cython.readthedocs.io/en/latest/src/reference/compilation.html
def no_cythonize(extensions, **_ignore):
    import os.path as op
    for extension in extensions:
        sources = []
        for sfile in extension.sources:
            path, ext = os.path.splitext(sfile)
            if ext in ('.pyx', '.py'):
                ext = '.c'
                sfile = path + ext
                if not op.exists(sfile):
                    raise ValueError('Cannot find pre-compiled source file '
                                     '({}) - please install Cython'.format(sfile))
            sources.append(sfile)
        extension.sources[:] = sources
    return extensions


def build_extension_from_pyx(pyx_path):
    include_dirs = [NUMPY_INC_PATH, "vlsift/sift/vl","vlsift"]

    extra_sources_paths = [pyx_path,"vlsift/sift/vl/generic.c","vlsift/sift/vl/getopt_long.c","vlsift/sift/vl/host.c","vlsift/sift/vl/imopv_sse2.c",
                               "vlsift/sift/vl/imopv.c","vlsift/sift/vl/mathop.c","vlsift/sift/vl/mathop_avx.c","vlsift/sift/vl/mathop_sse2.c",
                               "vlsift/sift/vl/mser.c","vlsift/sift/vl/pgm.c","vlsift/sift/vl/random.c",
                               "vlsift/sift/vl/sift.c","vlsift/sift/vl/stringop.c"]

    ext = Extension(name=pyx_path[:-4].replace('/', '.'),
                    sources=extra_sources_paths,
                    include_dirs=include_dirs,
                    define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
                    language='c')

    if IS_LINUX or IS_OSX:
        ext.extra_compile_args.append('-Wno-unused-function')
        ext.extra_compile_args.append('-pthread')
        ext.extra_compile_args.append('-lgomp')
        ext.extra_compile_args.append('-msse2')
        ext.extra_compile_args.append('-mavx')
    if IS_OSX:
        ext.extra_link_args.append('-headerpad_max_install_names')
    if IS_WIN:
        ext.extra_compile_args.append('/DVL_BUILD_DLL')
        ext.extra_compile_args.append('/DVL_DISABLE_SSE2')
        ext.extra_compile_args.append('/DVL_DISABLE_AVX')
    return ext

try:
    from Cython.Distutils.extension import Extension
except ImportError:
    from setuptools import Extension
    from setuptools.command.build_ext import build_ext
    import warnings
    USING_CYTHON = False
    cythonize = no_cythonize
    warnings.warn('Unable to import Cython - attempting to build using the '
                  'pre-compiled C files.')
else:
    from Cython.Distutils import build_ext
    from Cython.Build import cythonize
    USING_CYTHON = True

exts = cythonize([build_extension_from_pyx('vlsift/sift/cysift.pyx')], quiet=True, language_level="3")

setup(
    name='vlsift',
    version="0.1.2",
    cmdclass={"build_ext": build_ext},
    description='Cython wrapper of the VLFeat toolkit',
    ext_modules=exts,
    package_data={'vlsift': ['data/*.mat', 'data/ascent.descr', 'data/ascent.frame']},
    packages=find_packages()
)
