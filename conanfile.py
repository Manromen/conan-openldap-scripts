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
        # autotools = AutoToolsBuildEnvironment(self)
        # env_build_vars = autotools.vars
        # build_host = None

        if self.settings.os == "iOS":
            if self.version == "2.4.46":
                self.run("cd %s; patch -p1 < %s/patches-ios/2.4.46.patch" % (library_folder, self.build_folder))

            # define all architectures for ios fat library
            if "arm" in self.settings.arch:
                self.variants = ["armv7", "armv7s", "armv8"]
                for arch in self.variants:
                    self.build_ios(library_folder=library_folder, arch=arch)
                self.create_ios_fat_files()
            else:
                self.variants = []


    def build_ios(self, library_folder=None, arch=None):

        if arch == None:
            raise Exception("build_ios called without a given arch")

        autotools = AutoToolsBuildEnvironment(self)
        env_build_vars = autotools.vars
        autotools_args = ["--with-yielding_select=no", "--with-tls=auto", "--disable-slapd"]

        build_host = "%s-apple-darwin" % tools.to_apple_arch(arch)
        if arch == "armv8":
            build_host = "arm-apple-darwin"

        platform_path = "/Applications/Xcode.app/Contents/Developer/Platforms"
        platform = "iPhoneOS"
        if self.settings.arch == "x86" or self.settings.arch == "x86_64":
            platform = "iPhoneSimulator"

        # CC
        cmd_output = StringIO()
        self.run("xcrun -sdk iphoneos -find clang", output=cmd_output)
        env_cc = cmd_output.getvalue().rstrip()
        env_build_vars['CC'] = env_cc
        cmd_output.close()
        print("CC", env_cc)
        #autotools_args.append("CC=%s" % env_cc)

        # CPP
        env_cpp = "%s -E" % env_cc
        env_build_vars['CPP'] = env_cpp
        print("CPP", env_cpp)
        #autotools_args.append("CPP=%s" % env_cpp)

        # CFLAGS
        env_cflags = "-arch %s -isysroot %s/%s.platform/Developer/SDKs/%s%s.sdk -miphoneos-version-min=10" % (tools.to_apple_arch(arch), platform_path, platform, platform, self.settings.os.version)
        env_build_vars['CFLAGS'] = env_cflags
        print("CFLAGS", env_cflags)
        #autotools_args.append("CFLAGS=%s" % env_cflags)

        # CPPFLAGS
        env_cppflags = "-arch %s -isysroot %s/%s.platform/Developer/SDKs/%s%s.sdk -miphoneos-version-min=10" % (tools.to_apple_arch(arch), platform_path, platform, platform, self.settings.os.version)
        env_build_vars['CPPFLAGS'] = env_cppflags
        print("CPPFLAGS", env_cppflags)
        #autotools_args.append("CPPFLAGS=%s" % env_cppflags)

        # LDFLAGS
        env_ldflags = "-arch %s -isysroot %s/%s.platform/Developer/SDKs/%s%s.sdk" % (tools.to_apple_arch(arch), platform_path, platform, platform, self.settings.os.version)
        env_build_vars['LDFLAGS'] = env_ldflags
        print("LDFLAGS", env_ldflags)
        #autotools_args.append("LDFLAGS=%s" % env_ldflags)

        # AR
        cmd_output = StringIO()
        self.run("xcrun -sdk iphoneos -find ar", output=cmd_output)
        env_ar = cmd_output.getvalue().rstrip()
        env_build_vars['AR'] = env_ar
        cmd_output.close()
        print("AR", env_ar)
        #autotools_args.append("AR=%s" % env_ar)
        
        # RANLIB
        cmd_output = StringIO()
        self.run("xcrun -sdk iphoneos -find ranlib", output=cmd_output)
        env_ranlib = cmd_output.getvalue().rstrip()
        env_build_vars['RANLIB'] = env_ranlib
        cmd_output.close()
        print("RANLIB", env_ranlib)
        #autotools_args.append("RANLIB=%s" % env_ranlib)
        
        prefix_folder = os.path.join(self.build_folder, "output")
        exec_prefix_folder = os.path.join(self.build_folder, "output", arch)
        autotools_args.append("--prefix=%s" % prefix_folder)
        autotools_args.append("--exec-prefix=%s" % exec_prefix_folder)
        #autotools_args.append("--target=%s-apple-darwin" % tools.to_apple_arch(arch))
        
        if self.settings.build_type == "Release":
            autotools_args.append("--disable-debug")
        if self.options.shared == False:
            autotools_args.append("--disable-shared")
            autotools_args.append("--enable-static")
      
        autotools.configure(configure_dir=library_folder, args=autotools_args, host=build_host, vars=env_build_vars, build=None, target=None)
        autotools.make()

    def create_ios_fat_files(self):
        # LIPO command
        cmd_output = StringIO()
        self.run("xcrun -sdk iphoneos -find lipo", output=cmd_output)
        lipo_cmd = cmd_output.getvalue().rstrip()
        cmd_output.close()

        lib_dir = os.path.join(self.build_folder,"output","armv8","lib")
        for f in os.listdir(lib_dir):
            lipo = lipo_cmd + " -create "
            if f.endswith(".a"):
                for arch in self.variants:
                    lipo += os.path.join(self.build_folder,"output",arch,"lib", f, " ")
                lipo += "-output " + os.path.join(self.package_folder, "lib", f)
                self.run(lipo)

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
