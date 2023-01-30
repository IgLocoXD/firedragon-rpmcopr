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
%define _patches_dir %{_builddir}/firedragon-109.0/common/patches
%define _librewolf_patches_dir %{_builddir}/firedragon-109.0/librewolf-source/patches
%define _cachyos_patches_dir %{_builddir}/firedragon-109.0/cachyos-source/patches
%define pkgname firedragon
%define _pkgname FireDragon

%prep
%setup

%description
'Librewolf fork build using custom branding, settings & KDE patches by OpenSUSE'

%build
    mkdir -p mozbuild
  cd firefox-109.0




echo "ac_add_options --enable-application=browser" >> .mozconfig
echo "mk_add_options MOZ_OBJDIR=%{PWD@Q}/obj" >> .mozconfig

# This supposedly speeds up compilation (We test through dogfooding anyway)
echo "ac_add_options --disable-debug" >> .mozconfig
echo "ac_add_options --disable-tests" >> .mozconfig

# TODO: use source/assets/moczonfig in the future
# NOTE: let us use it for one last build, otherwise, there might be some conflicts
echo "mk_add_options MOZ_CRASHREPORTER=0" >> .mozconfig
echo "mk_add_options MOZ_DATA_REPORTING=0" >> .mozconfig
echo "mk_add_options MOZ_SERVICES_HEALTHREPORT=0" >> .mozconfig
echo "mk_add_options MOZ_TELEMETRY_REPORTING=0" >> .mozconfig

echo "ac_add_options --disable-bootstrap" >> .mozconfig
echo "ac_add_options --enable-default-toolkit=cairo-gtk3-wayland" >> .mozconfig
echo "ac_add_options --enable-hardening" >> .mozconfig
echo "ac_add_options --enable-linker=mold" >> .mozconfig
echo "ac_add_options --enable-release" >> .mozconfig
echo "ac_add_options --enable-rust-simd" >> .mozconfig
echo "ac_add_options --prefix=/usr" >> .mozconfig

export AR=llvm-ar
export CC='clang'
export CXX='clang++'
export NM=llvm-nm
export RANLIB=llvm-ranlib

# Branding
echo "ac_add_options --allow-addon-sideload" >> .mozconfig
echo " ac_add_options --enable-update-channel=release"  >> .mozconfig
echo " ac_add_options --with-app-name=%{pkgname}" >> .mozconfig
echo " ac_add_options --with-branding=browser/branding/%{pkgname }" >> .mozconfig
echo "ac_add_options --with-distribution-id=org.garudalinux"  >> .mozconfig
echo "ac_add_options --with-unsigned-addon-scopes=app,system"  >> .mozconfig
export MOZ_REQUIRE_SIGNING=1

# System libraries
echo " ac_add_options --with-system-nspr" >> .mozconfig
echo "ac_add_options --with-system-nss">> .mozconfig

# Features
echo "ac_add_options --enable-alsa">> .mozconfig
echo "ac_add_options --enable-jack">> .mozconfig
echo " ac_add_options --disable-crashreporter">> .mozconfig
echo "ac_add_options --disable-updater">> .mozconfig
# probably not needed, enabled by default?
echo "ac_add_options --enable-optimize">> .mozconfig

# Arch upstream has it in their PKGBUILD, ALARM does not for aarch64:
echo " ac_add_options --disable-elf-hack">> .mozconfig

# might help with failing x86_64 builds?
export LDFLAGS+=" -Wl,--no-keep-memory"
# Upstream patches from gentoo
  # PGO improvements
  patch -Np1 -i "%{_cachyos_patches_dir}"/gentoo/0016-bmo-1516081-Disable-watchdog-during-PGO-builds.patch

  # Remove some pre-installed addons that might be questionable
  patch -Np1 -i "%{_librewolf_patches_dir}"/remove_addons.patch

  # KDE menu and unity menubar
  patch -Np1 -i "%{_librewolf_patches_dir}"/unity_kde/mozilla-kde.patch
  patch -Np1 -i "%{_librewolf_patches_dir}"/unity_kde/firefox-kde.patch
  patch -Np1 -i "%{_librewolf_patches_dir}"/unity_kde/unity-menubar.patch

  # Disabling Pocket
  patch -Np1 -i "%{_librewolf_patches_dir}"/sed-patches/disable-pocket.patch

  # Allow SearchEngines option in non-ESR builds
  patch -Np1 -i "%{_librewolf_patches_dir}"/sed-patches/allow-searchengines-non-esr.patch

  # Stop some undesired requests (https://gitlab.com/librewolf-community/browser/common/-/issues/10)
  patch -Np1 -i "%{_librewolf_patches_dir}"/sed-patches/stop-undesired-requests.patch

  # Assorted patches
  patch -Np1 -i "%{_librewolf_patches_dir}"/urlbarprovider-interventions.patch

  # Allow uBlockOrigin to run in private mode by default, without user intervention.
  patch -Np1 -i "%{_librewolf_patches_dir}"/allow-ubo-private-mode.patch

  # Add custom uBO assets (on first launch only)
  patch -Np1 -i "%{_librewolf_patches_dir}"/custom-ubo-assets-bootstrap-location.patch

  # UI patches
  # Remove references to firefox from the settings UI, change text in some of the links,
  # explain that we force en-US and suggest enabling history near the session restore checkbox.
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/pref-naming.patch

  # Remap help links
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/remap-links.patch

  # Don't nag to set default browser
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/hide-default-browser.patch

  # Add LibreWolf logo to Debugging Page
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/lw-logo-devtools.patch

  # Update privacy preferences
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/privacy-preferences.patch

  # Remove firefox references in the urlbar, when suggesting opened tabs.
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/remove-branding-urlbar.patch

  # Remove cfr UI elements, as they are disabled and locked already.
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/remove-cfrprefs.patch

  # Do not display your browser is being managed by your organization in the settings.
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/remove-organization-policy-banner.patch

  # Hide "snippets" section from the home page settings, as it was already locked.
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/remove-snippets-from-home.patch

  # Add patch to hide website appearance settings
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/website-appearance-ui-rfp.patch

  # Update handler links
  patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/handlers.patch

  # Hide the annoying Firefox view feature introduced in 106
  # patch -Np1 -i "%{_librewolf_patches_dir}"/ui-patches/firefox-view.patch

  # Fix telemetry removal, see https://gitlab.com/librewolf-community/browser/linux/-/merge_requests/17, for example
  patch -Np1 -i "%{_librewolf_patches_dir}"/disable-data-reporting-at-compile-time.patch

  # Allows hiding the password manager (from the lw pref pane) / via a pref
  patch -Np1 -i "%{_librewolf_patches_dir}"/hide-passwordmgr.patch

  # Faster multilocate
  patch -Np1 -i "%{_librewolf_patches_dir}"/faster-package-multi-locale.patch

  # https://bugzilla.mozilla.org/show_bug.cgi?id=1804973
  patch -Np1 -i "%{_patches_dir}"/arch/0002-Bug-1804973-Wayland-Check-size-for-valid-EGLWindows-.patch

  # Pref pane - custom FireDragon svg
  patch -Np1 -i "%{_patches_dir}"/custom/librewolf-pref-pane.patch
  patch -Np1 -i "%{_patches_dir}"/custom/add_firedragon_svg.patch
  rebrand() {
    find ./* -type f -exec sed -i "s/$1/$2/g" {} +
  }

  rebrand "\/io\/gitlab\/" "\/org\/garudalinux\/"
 rebrand "io.gitlab." "org.garudalinux."
rebrand LibreWolf FireDragon
rebrand Librewolf FireDragon
rebrand librewolf firedragon
rebrand "fredragon\.net" "librewolf.net"
rebrand "#why-is-firedragon-forcing-light-theme" "#why-is-librewolf-forcing-light-theme"
rebrand kmozillahelper kfiredragonhelper
rm -f "${srcdir}"/common/source_files/mozconfig
  cp -r "${srcdir}"/common/source_files/* ./
  export pkgdir="%{buildroot}"
    export srcdir="%{srcdir}"
    export pkgname="%{pkgname}"
    export _pkgname="%{_pkgname}"
    export _pkgfolder="%{_pkgfolder}"
    cd firefox-109.0;
    export MOZ_NOSPAM=1;
    export MOZBUILD_STATE_PATH="$srcdir/mozbuild";
    export MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE=pip;
    export PIP_NETWORK_INSTALL_RESTRICTED_VIRTUALENVS=mach;
    ulimit -n 4096;
    echo "Building instrumented browser...";
        cat ../mozconfig - > .mozconfig <<END
ac_add_options --enable-profile-generate
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

echo "ac_add_options --enable-lto" >> .mozconfig
echo "ac_add_options --enable-profile-use">> .mozconfig
echo "ac_add_options --with-pgo-profile-path=${PWD@Q}/merged.profdata">> .mozconfig
echo "ac_add_options --with-pgo-jarlog=${PWD@Q}/jarlog">> .mozconfig
echo "ac_add_options --enable-lto">> .mozconfig
echo "ac_add_options --enable-profile-use">> .mozconfig
echo "ac_add_options --with-pgo-profile-path=${PWD@Q}/merged.profdata">> .mozconfig
echo "ac_add_options --with-pgo-jarlog=${PWD@Q}/jarlog">> .mozconfig
echo "ac_add_options --without-wasm-sandboxed-libraries">> .mozconfig
cat ../mozconfig - > .mozconfig <<END
export pkgdir="%{buildroot}"
    export srcdir="%{srcdir}"
    export pkgname="%{pkgname}"
    export _pkgname="%{_pkgname}"
    export _pkgfolder="%{_pkgfolder}"
    env CARGO_HOME=.cargo cargo install cbindgen
    export PATH=`pwd`/.cargo/bin:$PATH

    cd firefox-109.0;

     DESTDIR="%pkgdir"  ./mach build  ;
    echo "Building symbol archive...";
     DESTDIR="%pkgdir" ./mach buildsymbols
    DESTDIR="%pkgdir" ./mach install;

%install
    export pkgdir="%{buildroot}"
    export srcdir="%{srcdir}"
    export pkgname="%{pkgname}"
    export _pkgname="%{_pkgname}"
    export _pkgfolder="%{_pkgfolder}"
    env CARGO_HOME=.cargo cargo install cbindgen
    export PATH=`pwd`/.cargo/bin:$PATH

    cd firefox-109.0;

     DESTDIR="%pkgdir"  ./mach build  ;
    echo "Building symbol archive...";
     DESTDIR="%pkgdir" ./mach buildsymbols
    DESTDIR="%pkgdir" ./mach install;
    rm "%pkgdir"/usr/lib/%{pkgname}/pingsender;
    install -Dvm644 "%srcdir/settings/%pkgname.psd" "%pkgdir/usr/share/psd/browsers/%pkgname";
    local vendorjs;
    vendorjs="%pkgdir/usr/lib/%pkgname/browser/defaults/preferences/vendor.js";
    install -Dvm644 /dev/stdin "%vendorjs" <<END


    cd %{srcdir}/firefox-109.0;
    cp -r%{srcdir}/settings/* %{pkgdir}/usr/lib/%{pkgname}/;
    local distini="%pkgdir/usr/lib/%pkgname/distribution/distribution.ini";
    install -Dvm644 /dev/stdin "%distini" <<END

[Global]

[Preferences]
app.distributor=garudalinux
app.distributor.channel=%pkgname
app.partner.garudalinux=garudalinux


%files
/*
%exclude %dir /usr/bin
%exclude %dir /usr/lib

