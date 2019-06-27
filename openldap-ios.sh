# ----------------------------------------------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2018-2019 Ralph-Gordon Paul. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the 
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the 
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ----------------------------------------------------------------------------------------------------------------------

#!/bin/bash
set -e

# Params:
# $1 Library Version
# $2 'arm' or 'x86_64'
# $3 Path to the source files
# $4 Build type (either 'Debug' or 'Release')

# ----------------------------------------------------------------------------------------------------------------------
# settings

declare LIBRARY_VERSION=$1
declare DEVICE_ARCH=$2
declare LIBRARY_FOLDER=$3
declare BUILD_TYPE=$4

declare IOS_MIN_VERSION="10.0"

# ----------------------------------------------------------------------------------------------------------------------
# globals

declare ABSOLUTE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
declare LIBRARY_INSTALL_FOLDER="${ABSOLUTE_DIR}/${LIBRARY_VERSION}"
declare IOS_SDK_VERSION=$(xcodebuild -showsdks | grep iphoneos | awk '{print $4}' | sed 's/[^0-9,\.]*//g')
declare PLATFORMPATH="/Applications/Xcode.app/Contents/Developer/Platforms"
declare LIPO_CMD=$(xcrun -sdk iphoneos -find lipo)

# ======================================================================================================================

function prepare()
{
    rm -rf "${ABSOLUTE_DIR}/build" "${ABSOLUTE_DIR}/install/" || true
}

# ======================================================================================================================

function build()
{
    target=$1
    hosttarget=$1
    platform=$2

    echo "============================================================="
    echo "= building for target $target platform $platform ...        ="
    echo "============================================================="

    rm -rf "${ABSOLUTE_DIR}/build" || true
    cp -r "${LIBRARY_FOLDER}" "${ABSOLUTE_DIR}/build"

    mkdir -p "${ABSOLUTE_DIR}/install/${target}"

    cd "${ABSOLUTE_DIR}/build"

    if [[ $hosttarget == "x86_64" ]]; then
        hosttarget="i386"
    elif [[ $hosttarget == "arm64" ]]; then
        hosttarget="arm"
    fi

    export CC="$(xcrun -sdk iphoneos -find clang)"
    export CPP="$CC -E"
    export CFLAGS="-arch ${target} -I${ABSOLUTE_DIR}/ios/include -isysroot $PLATFORMPATH/$platform.platform/Developer/SDKs/$platform$IOS_SDK_VERSION.sdk -miphoneos-version-min=$IOS_MIN_VERSION"
    export AR=$(xcrun -sdk iphoneos -find ar)
    export RANLIB=$(xcrun -sdk iphoneos -find ranlib)
    export CPPFLAGS="-arch ${target} -I${ABSOLUTE_DIR}/ios/include -isysroot $PLATFORMPATH/$platform.platform/Developer/SDKs/$platform$IOS_SDK_VERSION.sdk -miphoneos-version-min=$IOS_MIN_VERSION"
    export LDFLAGS="-arch ${target} -L${ABSOLUTE_DIR}/ios/lib -isysroot $PLATFORMPATH/$platform.platform/Developer/SDKs/$platform$IOS_SDK_VERSION.sdk"

    if [[ "$BUILD_TYPE" == "Release" ]]; then
        ./configure --disable-shared \
                    --host=$hosttarget-apple-darwin \
                    --disable-debug \
                    --with-yielding_select=no \
                    --with-tls=auto \
                    --disable-slapd \
                    --prefix="${ABSOLUTE_DIR}/install/common" \
                    --exec-prefix="${ABSOLUTE_DIR}/install/$target"
    else
        ./configure --disable-shared \
                    --host=$hosttarget-apple-darwin \
                    --with-yielding_select=no \
                    --with-tls=auto \
                    --disable-slapd \
                    --prefix="${ABSOLUTE_DIR}/install/common" \
                    --exec-prefix="${ABSOLUTE_DIR}/install/$target"
    fi

    make depend > log.txt
    # make clean
    make >> log.txt
    make install

    echo "============================================================="
    echo "= Success for target $target platform $platform ...         ="
    echo "============================================================="
}

# ======================================================================================================================
# create fat file of the libraries

function createFatFiles()
{
    mkdir -p "${ABSOLUTE_DIR}/lib"

    # copy header files
    cp -r "${ABSOLUTE_DIR}/install/common/include" "${ABSOLUTE_DIR}/"

    declare LIBRARY_FILES=${ABSOLUTE_DIR}/install/armv7/lib/*.a

    # iterate over all .a files
    for f in $LIBRARY_FILES
    do
        file=${f##*/}
        echo "Creating fat file $file ..."

        $LIPO_CMD -create ${ABSOLUTE_DIR}/install/armv7/lib/${file} \
                  ${ABSOLUTE_DIR}/install/armv7s/lib/${file} \
                  ${ABSOLUTE_DIR}/install/arm64/lib/${file} \
                  -output ${ABSOLUTE_DIR}/lib/${file}
    done

}

# ======================================================================================================================

echo "################################################################################"
echo "###                                 OpenLDAP                                 ###"
echo "################################################################################"

prepare

if [[ "$DEVICE_ARCH" == "arm" ]]; then
    build armv7 iPhoneOS
    build armv7s iPhoneOS
    build arm64 iPhoneOS
    createFatFiles
elif [[ "$DEVICE_ARCH" == "x86_64" ]]; then
    build x86_64 iPhoneSimulator
    cp -r "${ABSOLUTE_DIR}/install/common/include" "${ABSOLUTE_DIR}/"
    cp -r "${ABSOLUTE_DIR}/install/x86_64/lib" "${ABSOLUTE_DIR}/"
fi

# ======================================================================================================================


