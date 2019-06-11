# Conan OpenLDAP
[![Build Status](https://travis-ci.com/Manromen/conan-openldap-scripts.svg?branch=master)](https://travis-ci.com/Manromen/conan-openldap-scripts)
This repository contains the conan receipe that is used to build the OpenLDAP packages at [rgpaul bintray](https://bintray.com/manromen/rgpaul).

For Infos about the OpenLDAP library please visit [openldap.org](https://www.openldap.org/).
The library is licensed under the [Open LDAP Public License v2.8](https://www.openldap.org/software/release/license.html).
This repository is licensed under the [MIT License](LICENSE).

## iOS

To create a package for iOS you can run the conan command like this:

`conan create . openldap/2.4.46@rgpaul/stable -s os=iOS -s os.version=12.2 -s arch=armv8 -s build_type=Release -o shared=False`

### Requirements

* [CMake](https://cmake.org/)
* [Conan](https://conan.io/)
* [Xcode](https://developer.apple.com/xcode/)
