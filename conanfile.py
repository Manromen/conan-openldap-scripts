from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment
from six import StringIO  # Python 2 and 3 compatible
import os

class OpenLDAPConan(ConanFile):
    name = "openldap"
    version = "2.4.46"
    author = "Ralph-Gordon Paul (gordon@rgpaul.com)"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "android_ndk": "ANY", "android_stl_type":["c++_static", "c++_shared"]}
    default_options = "shared=False", "android_ndk=None", "android_stl_type=c++_static"
    description = "OpenLDAP Software is an open source implementation of the Lightweight Directory Access Protocol."
    url = "https://github.com/Manromen/conan-openldap-scripts"
    license = "OLDAP-2.8"
    exports_sources = "cmake-modules/*", "patches-ios/*", "openldap-ios.sh"

    # download sources
    def source(self):
        url = "http://mirror.eu.oneandone.net/software/openldap/openldap-release/openldap-%s.tgz" % self.version
        tools.get(url)

    # compile using cmake
    def build(self):
        library_folder = "%s/openldap-%s" % (self.source_folder, self.version)
        # autotools = AutoToolsBuildEnvironment(self)
        # env_build_vars = autotools.vars
        # build_host = None

        if self.settings.os == "iOS":
            if self.version == "2.4.46":
                self.run("cd %s; patch -p1 < %s/patches-ios/2.4.46.patch" % (library_folder, self.build_folder))

            # define all architectures for ios fat library
            if "arm" in self.settings.arch:
                self.run("%s/openldap-ios.sh %s arm %s %s" % (self.build_folder, self.version, library_folder, self.settings.build_type))
            else:
                self.run("%s/openldap-ios.sh %s %s %s %s" % (self.build_folder, self.version, tools.to_apple_arch(self.settings.arch), library_folder, self.settings.build_type))

    def package(self):
        self.copy("*.h", dst="include", src='include')
        self.copy("*.hpp", dst="include", src='include')
        self.copy("*.lib", dst="lib", src='lib', keep_path=False)
        self.copy("*.dll", dst="bin", src='bin', keep_path=False)
        self.copy("*.so", dst="lib", src='lib', keep_path=False)
        self.copy("*.dylib*", dst="lib", src='lib', keep_path=False)
        self.copy("*.a", dst="lib", src='lib', keep_path=False)
        
    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs = ['include']

    def package_id(self):
        if "arm" in self.settings.arch and self.settings.os == "iOS":
            self.info.settings.arch = "AnyARM"

    def requirements(self):
        self.requires("libressl/2.9.2@%s/%s" % (self.user, self.channel))

        if self.options.shared:
            raise Exception("Shared library is not supported yet")

    def imports(self):
        if self.settings.os == "iOS":
            self.copy("*.dylib*", dst="ios/lib", src="lib")
            self.copy("*.a", dst="ios/lib", src="lib")
            self.copy("*", dst="ios/include", src="include")

    def config_options(self):
        # remove android specific option for all other platforms
        if self.settings.os != "Android":
            del self.options.android_ndk
            del self.options.android_stl_type
