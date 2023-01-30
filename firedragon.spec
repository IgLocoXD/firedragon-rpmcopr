Name: firedragon
Version: 109.0
Release: 1
Summary: 'Librewolf fork build using custom branding, settings & KDE patches by OpenSUSE'
License: MPL

BuildRequires:  zip
BuildRequires: jack-audio-connection-kit-devel
BuildRequires: alsa-lib-devel
BuildRequires:  bzip2-devel
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(gtk+-2.0)
BuildRequires:  pkgconfig(krb5)
BuildRequires:  pkgconfig(pango)
BuildRequires:  pkgconfig(freetype2) >= %{freetype_version}
BuildRequires:  pkgconfig(xt)
BuildRequires:  pkgconfig(xrender)
BuildRequires:  pkgconfig(libstartup-notification-1.0)
BuildRequires:  pkgconfig(libnotify) >= %{libnotify_version}
BuildRequires:  pkgconfig(dri)
BuildRequires:  pkgconfig(libcurl)
BuildRequires:  dbus-glib-devel
BuildRequires:  autoconf213
BuildRequires:  pkgconfig(libpulse)
BuildRequires:  yasm
BuildRequires:  llvm
BuildRequires:  llvm-devel
BuildRequires:  clang
BuildRequires:  clang-libs

BuildRequires:  pipewire-devel

BuildRequires:  nodejs
BuildRequires:  nasm >= 1.13
BuildRequires:  libappstream-glib


Requires:       mozilla-filesystem
Recommends:     mozilla-openh264 >= 2.1.1
Recommends:     libva
Requires:       p11-kit-trust
Requires:       pciutils-libs

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

BuildRequires:  desktop-file-utils

BuildRequires:  rust
BuildRequires:  cargo
BuildRequires:  clang-devel

BuildRequires:  perl-interpreter
BuildRequires:  fdk-aac-free-devel


BuildRequires:  google-droid-sans-fonts
BuildRequires:  google-noto-fonts-common
BuildRequires:  google-noto-cjk-fonts-common
BuildRequires:  google-noto-sans-cjk-ttc-fonts
BuildRequires:  google-noto-sans-gurmukhi-fonts
BuildRequires:  google-noto-sans-fonts
BuildRequires:  google-noto-emoji-color-fonts
BuildRequires:  google-noto-sans-sinhala-vf-fonts
# -----------------------------------
BuildRequires:  thai-scalable-fonts-common
BuildRequires:  thai-scalable-waree-fonts
BuildRequires:  khmeros-base-fonts
BuildRequires:  jomolhari-fonts
# ----------------------------------
BuildRequires:  lohit-tamil-fonts
BuildRequires:  lohit-telugu-fonts
# ----------------------------------
BuildRequires:  paktype-naskh-basic-fonts
# faild to build in Koji / f32

BuildRequires:  make
BuildRequires:  pciutils-libs
Source: https://gitlab.com/obsidian-development/lfs-for-firedragon/-/raw/main/firedragon-109.0.tar.gz
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

