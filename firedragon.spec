Name: firedragon
Version: 109.0
Release: 1
Summary: 'Librewolf fork build using custom branding, settings & KDE patches by OpenSUSE'
License: MPL
Requires: gtk3
Requires: libxt
Requires: mime-types
Requires: dbus-glib
Requires: nss
Requires: ttf-font
Requires: libpulse
Requires: ffmpeg
Requires: xdg-desktop-portal
BuildRequires: unzip
BuildRequires: zip
BuildRequires: diffutils
BuildRequires: yasm
BuildRequires: mesa
BuildRequires: imake
BuildRequires: inetutils
BuildRequires: xorg-server-xvfb
BuildRequires: autoconf2.13
BuildRequires: rust
BuildRequires: clang
BuildRequires: llvm
BuildRequires: jack
BuildRequires: nodejs
BuildRequires: cbindgen
BuildRequires: nasm
BuildRequires: mold
BuildRequires: python-setuptools
BuildRequires: python-zstandard
BuildRequires: git
BuildRequires: binutils
BuildRequires: dump_syms
BuildRequires: lld
BuildRequires: wasi-compiler-rt>13
BuildRequires: wasi-libc
BuildRequires: wasi-libc++>13
BuildRequires: wasi-libc++abi>13
BuildRequires: pciutils
Source: firedragon-109.0.tar.gz
%define __brp_mangle_shebangs %{nil}
%define debug_package %{nil}
%define srcdir %{_builddir}/firedragon-109.0
%define pkgname firedragon
%define _pkgname FireDragon

%prep
%setup

%description
'Librewolf fork build using custom branding, settings & KDE patches by OpenSUSE'

%build
    export pkgdir="%{buildroot}"
    export srcdir="%{srcdir}"
    export pkgname="%{pkgname}"
    export _pkgname="%{_pkgname}"
    export _pkgfolder="%{_pkgfolder}"
    cd firefox-"$pkgver";
    export MOZ_NOSPAM=1;
    export MOZBUILD_STATE_PATH="$srcdir/mozbuild";
    export MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE=pip;
    export PIP_NETWORK_INSTALL_RESTRICTED_VIRTUALENVS=mach;
    ulimit -n 4096;
    echo "Building instrumented browser...";
    if [[ $CARCH == 'aarch64' ]]; then
        cat ../mozconfig - > .mozconfig <<END
ac_add_options --enable-profile-generate
END

    else
        cat ../mozconfig - > .mozconfig <<END
ac_add_options --enable-profile-generate
END

    fi
    ./mach build;
    echo "Profiling instrumented browser...";
    ./mach package;
    LLVM_PROFDATA=llvm-profdata JARLOG_FILE="$PWD/jarlog" xvfb-run -s "-screen 0 1920x1080x24 -nolisten local" ./mach python build/pgo/profileserver.py;
    stat -c "Profile data found (%s bytes)" merged.profdata;
    test -s merged.profdata;
    stat -c "Jar log found (%s bytes)" jarlog;
    test -s jarlog;
    echo "Removing instrumented browser...";
    ./mach clobber;
    echo "Building optimized browser...";
    if [[ $CARCH == 'aarch64' ]]; then
        cat ../mozconfig - > .mozconfig <<END
ac_add_options --enable-lto
ac_add_options --enable-profile-use
ac_add_options --with-pgo-profile-path=${PWD@Q}/merged.profdata
ac_add_options --with-pgo-jarlog=${PWD@Q}/jarlog
END

    else
        cat ../mozconfig - > .mozconfig <<END
ac_add_options --enable-lto
ac_add_options --enable-profile-use
ac_add_options --with-pgo-profile-path=${PWD@Q}/merged.profdata
ac_add_options --with-pgo-jarlog=${PWD@Q}/jarlog
END

    fi
    ./mach build;
    echo "Building symbol archive...";
    ./mach buildsymbols

%install
    export pkgdir="%{buildroot}"
    export srcdir="%{srcdir}"
    export pkgname="%{pkgname}"
    export _pkgname="%{_pkgname}"
    export _pkgfolder="%{_pkgfolder}"
    cd firefox-"$pkgver";
    DESTDIR="$pkgdir" ./mach install;
    rm "$pkgdir"/usr/lib/${pkgname}/pingsender;
    install -Dvm644 "$srcdir/settings/$pkgname.psd" "$pkgdir/usr/share/psd/browsers/$pkgname";
    local vendorjs;
    vendorjs="$pkgdir/usr/lib/$pkgname/browser/defaults/preferences/vendor.js";
    install -Dvm644 /dev/stdin "$vendorjs" <<END
// Use system-provided dictionaries
pref("spellchecker.dictionary_path", "/usr/share/hunspell");

// Don't disable extensions in the application directory
// done in firedragon.cfg
// pref("extensions.autoDisableScopes", 11);
END

    cd ${srcdir}/firefox-"$pkgver";
    cp -r ${srcdir}/settings/* ${pkgdir}/usr/lib/${pkgname}/;
    local distini="$pkgdir/usr/lib/$pkgname/distribution/distribution.ini";
    install -Dvm644 /dev/stdin "$distini" <<END

[Global]

[Preferences]
app.distributor=garudalinux
app.distributor.channel=$pkgname
app.partner.garudalinux=garudalinux
END

    for i in 16 32 48 64 128;
    do
        install -Dvm644 browser/branding/${pkgname}/default$i.png "$pkgdir/usr/share/icons/hicolor/${i}x${i}/apps/$pkgname.png";
    done;
    install -Dvm644 browser/branding/${pkgname}/content/about-logo.png "$pkgdir/usr/share/icons/hicolor/192x192/apps/$pkgname.png";
    install -Dvm644 browser/branding/${pkgname}/default16.png "$pkgdir/usr/share/icons/hicolor/symbolic/apps/$pkgname-symbolic.png";
    install -Dvm644 ../$pkgname.desktop "$pkgdir/usr/share/applications/$pkgname.desktop";
    install -Dvm755 /dev/stdin "$pkgdir/usr/bin/$pkgname" <<END
#!/bin/sh
exec /usr/lib/$pkgname/$pkgname "\$@"
END

    ln -srfv "$pkgdir/usr/bin/$pkgname" "$pkgdir/usr/lib/$pkgname/$pkgname-bin";
    local nssckbi="$pkgdir/usr/lib/$pkgname/libnssckbi.so";
    if [[ -e $nssckbi ]]; then
        ln -srfv "$pkgdir/usr/lib/libnssckbi.so" "$nssckbi";
    fi;
    ln -s "/usr/lib/mozilla/native-messaging-hosts" "$pkgdir/usr/lib/firedragon/native-messaging-hosts";
    rm "$pkgdir/usr/lib/firedragon/LICENSE.txt";
    rm "$pkgdir/usr/lib/firedragon/about.png";
    rm "$pkgdir/usr/lib/firedragon/firedragon.psd";
    rm "$pkgdir/usr/lib/firedragon/home.png";
    rm "$pkgdir/usr/lib/firedragon/package.json";
    rm "$pkgdir/usr/lib/firedragon/tabliss.json";
    rm "$pkgdir/usr/lib/firedragon/yarn.lock"

%files
/*
%exclude %dir /usr/bin
%exclude %dir /usr/lib

