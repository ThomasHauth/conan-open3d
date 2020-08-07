from conans import ConanFile, CMake, tools
import os
from io import StringIO
import shutil


class Open3dConan(ConanFile):
    version = "0.10.0"

    name = "open3d"
    license = "https://github.com/intel-isl/Open3D/blob/master/LICENSE"
    description = "Open3D: A Modern Library for 3D Data Processing http://www.open3d.org"
    url = "https://github.com/intel-isl/Open3D.git"
    settings = "os", "compiler", "build_type", "arch"
    generators = "pkg_config", "cmake", "cmake_find_package"
    short_paths = True

    # make stuff optional which is only for the user interface (OpenGL esp.)
    requires = (
        "eigen/[>=3.3.7]",
        "glfw/[>=3.3.2]"
        #"pybind11/[>=2.5.0]"
        )

    options = {
        "shared": [True, False],
        "with_visualization": [True, False],
        "librealsense": [True, False]
        }

    default_options = (
        "shared=True",
        "with_visualization=False",
        "librealsense=False"
        )

    scm = {
        "type": "git",
        "subfolder": "open3d",
        "url": url,
        "revision": "125458ad2f0", # master on 2020/08/05 imgui integration is broken in the
        # last release tag 0.10.0
        # "master",# "v%s" % version,
        "submodule": "recursive",
     }

    exports_sources = ["CMakeLists.txt", "mathstub.c"]
    _cmake = None

    def requirements(self):
        if self.options.with_visualization:
            self.requires("glew/2.1.0")
    
    def configure(self):
        if self.options.with_visualization and self.options.shared:
            self.options['glew'].shared = True

    def source(self):
        ##self.run("git clone https://github.com/RainerKuemmerle/g2o.git " + self._source_subfolder)
        ##ConanFile.source()
        #self.run("cd " + self._source_subfolder + " && git checkout 9b41a4e")
        self._patch()

    def _patch(self):
        # don't be so strict on warnings
        print("replacing " + str(os.path.join(self.source_folder, "open3d/cpp/CMakeLists.txt")))
        tools.replace_in_file(os.path.join(self.source_folder, "open3d/cpp/CMakeLists.txt"),
            '-Wall -Werror',
            '-Wall')
        # temporary fix for undefined math functions on Ubuntu 20.04
        # https://github.com/google/filament/issues/2146
        shutil.copyfile("mathstub.c", "open3d/cpp/open3d/mathstub.c")
        tools.replace_in_file(os.path.join(self.source_folder, "open3d/cpp/open3d/CMakeLists.txt"),
            'Open3DConfig.cpp',
            '''Open3DConfig.cpp
               mathstub.c
            ''')        
        pass

    def _configure_cmake(self):
        if not self._cmake:
            self._cmake = CMake(self)
            self._cmake.definitions["BUILD_SHARED_LIBS"] = self.options.shared
            ##cmake.definitions["-fno-builtin"] = 

            self._cmake.definitions["BUILD_CPP_EXAMPLES"] = False
            self._cmake.definitions["BUILD_GOOGLETEST"] = False        
            self._cmake.definitions["BUILD_EIGEN3"] = False
            self._cmake.definitions["EIGEN3_FOUND"] = True

            self._cmake.definitions["BUILD_PYTHON_MODULE"] = False
            self._cmake.definitions["BUILD_PYBIND11"] = True

            self._cmake.definitions["BUILD_GLFW"] = False
            self._cmake.definitions["GLFW3_FOUND"] = True
            self._cmake.definitions["GLIBCXX_USE_CXX11_ABI"] = True

            # with_visualization currently only causes open3d to use it's bundled 3rd-party libs
            # the src/CMakeLists.txt file would need to be patched to disable the complete module.

            if self.options.with_visualization:
                self._cmake.definitions["BUILD_GLEW"] = False
                self._cmake.definitions["GLEW_FOUND"] = True

            self._cmake.definitions["BUILD_LIBREALSENSE"] = self.options.librealsense

            self._cmake.configure()
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        #base_dir = os.path.join(self.package_folder, "include", "open3d_conan")
        #print("base dir" + str(base_dir))
        #if os.path.exists(base_dir):
        #    for name in os.listdir(base_dir):
        #        shutil.move(os.path.join(base_dir, name), os.path.join(self.package_folder, "include"))
        #
        #self.copy(pattern="*", src="bin", dst="./bin")
        #cmake = self._configure_cmake()
        #cmake.install()
        cmake = CMake(self)
        cmake.install()
        pass

    def package_info(self):
        libs = tools.collect_libs(self)
        self.cpp_info.libs = libs
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
