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
    exports_sources = "cmake-modules/*", "patches-ios/*"

    # download sources
    def source(self):
        url = "http://mirror.eu.oneandone.net/software/openldap/openldap-release/openldap-%s.tgz" % self.version
        tools.get(url)

    # compile using cmake
    def build(self):
        library_folder = "%s/openldap-%s" % (self.source_folder, self.version)
        autotools = AutoToolsBuildEnvironment(self)
        env_build_vars = autotools.vars
        build_host = None

        autotools_args = []

        if self.settings.os == "iOS":
            if self.version == "2.4.46":
                self.run("cd %s; patch -p1 < %s/patches-ios/2.4.46.patch" % (library_folder, self.build_folder))

            build_host = "i386-apple-darwin"

            platform_path = "/Applications/Xcode.app/Contents/Developer/Platforms"
            platform = "iPhoneOS"
            if self.settings.arch == "x86" or self.settings.arch == "x86_64":
                platform = "iPhoneSimulator"

            # CC
            mybuf = StringIO()
            self.run("xcrun -sdk iphoneos -find clang", output=mybuf)
            env_cc = mybuf.getvalue()
            env_build_vars['CC'] = env_cc
            mybuf.close()
            print("CC", env_cc)

            # CPP
            env_cpp = "%s -E" % env_cc
            env_build_vars['CPP'] = env_cpp
            print("CPP", env_cpp)

            # CFLAGS
            env_cflags = "-arch armv7 -arch armv7s -arch arm64 -isysroot %s/%s.platform/Developer/SDKs/%s%s.sdk -miphoneos-version-min=10" % (platform_path, platform, platform, self.settings.os.version)
            env_build_vars['CFLAGS'] = env_cflags
            print("CFLAGS", env_cflags)

            # AR
            mybuf = StringIO()
            self.run("xcrun -sdk iphoneos -find ar", output=mybuf)
            env_ar = mybuf.getvalue()
            env_build_vars['AR'] = env_ar
            mybuf.close()
            print("AR", env_ar)
            
            # RANLIB
            mybuf = StringIO()
            self.run("xcrun -sdk iphoneos -find ranlib", output=mybuf)
            env_ranlib = mybuf.getvalue()
            env_build_vars['RANLIB'] = env_ranlib
            mybuf.close()
            print("RANLIB", env_ranlib)

            #self.output.warn(mybuf.getvalue())

            #export CPPFLAGS="-arch ${target} -isysroot $PLATFORMPATH/$platform.platform/Developer/SDKs/$platform$IOS_SDK_VERSION.sdk -miphoneos-version-min=$IOS_MIN_VERSION"
            #export LDFLAGS="-arch ${target} -isysroot $PLATFORMPATH/$platform.platform/Developer/SDKs/$platform$IOS_SDK_VERSION.sdk"

            #self.run("export IOS_SDK_VERSION=$(xcodebuild -showsdks | grep iphoneos | awk '{print $4}' | sed 's/[^0-9,\.]*//g'")

            #self.run("export LIPO_CMD=$(xcrun -sdk iphoneos -find lipo)")
            #self.run("export CC='$(xcrun -sdk iphoneos -find clang)'")
            #self.run("export CPP='$CC -E'")
            #self.run('export CFLAGS="-arch ${target} -I${ABSOLUTE_DIR}/ios/include -isysroot $PLATFORMPATH/$platform.platform/Developer/SDKs/$platform$IOS_SDK_VERSION.sdk -miphoneos-version-min=$IOS_MIN_VERSION"')
            #self.run("export AR=$(xcrun -sdk iphoneos -find ar)")
            #self.run("export RANLIB=$(xcrun -sdk iphoneos -find ranlib)")

            autotools_args = ["--disable-shared", "--with-yielding_select=no", "--with-tls=auto", "--disable-slapd"]

        if self.settings.build_type == "Release":
            autotools_args.append("--disable-debug")
        if self.options.shared == False:
            autotools_args.append("--disable-shared")
      
        autotools.configure(configure_dir=library_folder, args=autotools_args, host=build_host, vars=env_build_vars, build=False)
        autotools.make()

    def package(self):
        self.copy("*", dst="include", src='include')
        self.copy("*.lib", dst="lib", src='lib', keep_path=False)
        self.copy("*.dll", dst="bin", src='bin', keep_path=False)
        self.copy("*.so", dst="lib", src='lib', keep_path=False)
        self.copy("*.dylib", dst="lib", src='lib', keep_path=False)
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

    def config_options(self):
        # remove android specific option for all other platforms
        if self.settings.os != "Android":
            del self.options.android_ndk
            del self.options.android_stl_type
