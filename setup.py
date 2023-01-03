#!/usr/bin/env python

import glob
import os
import shutil
import sys

import numpy as np
from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

# Determine shared library suffix
if sys.platform == "darwin":
    suffix = "dylib"
else:
    suffix = "so"


class OpenMCExtension(Extension):
    def __init__(self, name, cmake_lists_dir=".", sources=[], **kwa):
        Extension.__init__(self, name, sources=sources, **kwa)
        self.cmake_lists_dir = os.path.abspath(cmake_lists_dir)


class OpenMCBuildExt(build_ext):
    def build_extension(self, ext):
        # fallback to default behaviour for e.g. cython extensions
        if isinstance(ext, OpenMCExtension):
            self.build_cmake(ext)
        else:
            super().build_extension(ext)

    def build_cmake(self, ext):

        self.announce("Preparing the build environment", level=3)

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        self.announce("Configuring cmake project", level=3)

        self.spawn(
            [
                "cmake",
                "-S" + ext.cmake_lists_dir,
                "-B" + self.build_temp,
                "-DCMAKE_BUILD_TYPE=Release",
            ]
        )

        self.announce("Building binaries", level=3)

        self.spawn(
            ["cmake", "--build", self.build_temp, "--config", "Release", "--parallel", "2" ]
        )

        # this various depending on the platform so the easiest is to
        # just check what convention was used
        if "lib64" in os.listdir(self.build_temp):
            lib_dir = self.build_temp + "/lib64"
        else:
            lib_dir = self.build_temp + "/lib"

        # This is the directory that will make up the final wheel
        extdir = os.path.dirname(os.path.abspath(self.get_ext_fullpath(ext.name)))

        # copy libopenmc shared library into the python sources
        # this is where the openmc/lib/__init__.py expects it.
        shutil.copy(lib_dir + f"/libopenmc.{suffix}", extdir + "/openmc/lib/")

        # copy the binary to a place where the launcher script can find it
        # and auditwheel is able to properly make it relocatable
        openmc_exe = self.build_temp + "/bin/openmc"
        # Note that we can't directly put the binary in the scripts folder,
        # as auditwheel doesn't handle that case correctly see:
        # https://github.com/pypa/auditwheel/issues/340
        shutil.copy(openmc_exe, extdir + "/openmc/openmc_binary")


# Get version information from __init__.py. This is ugly, but more reliable than
# using an import.
with open("openmc/__init__.py", "r") as f:
    version = f.readlines()[-1].split()[-1].strip("'")

kwargs = {
    "name": "openmc",
    "version": version,
    "packages": find_packages(exclude=["tests*"]),
    "scripts": glob.glob("scripts/openmc*"),
    # Data files and libraries
    "package_data": {
        "openmc.data": ["mass_1.mas20.txt", "BREMX.DAT", "half_life.json", "*.h5"],
        "openmc.data.effective_dose": ["*.txt"],
    },
    # Metadata
    "author": "The OpenMC Development Team",
    "author_email": "openmc@anl.gov",
    "description": "OpenMC",
    "url": "https://openmc.org",
    "download_url": "https://github.com/openmc-dev/openmc/releases",
    "project_urls": {
        "Issue Tracker": "https://github.com/openmc-dev/openmc/issues",
        "Documentation": "https://docs.openmc.org",
        "Source Code": "https://github.com/openmc-dev/openmc",
    },
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering" "Programming Language :: C++",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    # Dependencies
    "python_requires": ">=3.7",
    "install_requires": [
        "numpy>=1.9",
        "h5py",
        "scipy",
        "ipython",
        "matplotlib",
        "pandas",
        "lxml",
        "uncertainties",
    ],
    "extras_require": {
        "depletion-mpi": ["mpi4py"],
        "docs": [
            "sphinx",
            "sphinxcontrib-katex",
            "sphinx-numfig",
            "jupyter",
            "sphinxcontrib-svg2pdfconverter",
            "sphinx-rtd-theme",
        ],
        "test": ["pytest", "pytest-cov", "colorama"],
        "vtk": ["vtk"],
    },
    # Cython is used to add resonance reconstruction and fast float_endf
    "ext_modules": cythonize("openmc/data/*.pyx") + [OpenMCExtension("libopenmc")],
    "cmdclass": {
        "build_ext": OpenMCBuildExt,
    },
    "include_dirs": [np.get_include()],
}

setup(**kwargs)
