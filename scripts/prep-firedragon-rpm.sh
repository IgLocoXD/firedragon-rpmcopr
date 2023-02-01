#!/bin/sh
# File: prep-firedragon-rpm.sh
# Location: https://gitlab.com/bgstack15/firedragon-fedora
# Latest supported version: firedragon-88.0-6.fc33
# Author: bgstack15
# SPDX-License-Identifier: CC-BY-SA-4.0
# Startdate: 2021-04-28
# Title: Build Rpm for LibreWolf
# Purpose: Prepare src.rpm for running "rpmbuild -ra firedragon.src.rpm" for LibreWolf by adapting distro Firefox assets
# History:
# Usage:
#    Can send the output to COPR
#    Reset the local build environment with:
#       rm -rf ../git ../prepared ../88.0
# References:
#    https://gitlab.com/firedragon-community/browser/linux/-/tree/master/scripts
# Improve:
# Dependencies:
#    req-fedora: rpmdevtools, dnf

set -e # fail out on any errors

#####################################
# Load settings
# basically, dot-source the conf file.
test -z "${firedragon_rpm_conf}" && export firedragon_rpm_conf="$( find "$( dirname "${0}" )" -maxdepth 2 -name "$( basename "${0%%.sh}.conf" )" -print 2>/dev/null | head -n1 )"
test ! -r "${firedragon_rpm_conf}" && { echo "Unable to load config file, which should be named the same as this script but with a .conf ending. Aborted." 1>&2 ; exit 1 ; }
. "${firedragon_rpm_conf}"
cachypatch_url=https://github.com/CachyOS/CachyOS-Browser-Common.git
firedragon_common_url=https://gitlab.com/dr460nf1r3/common.git
firedragon_setting_url=https://gitlab.com/dr460nf1r3/settings.git
librewolf_source_url=https://gitlab.com/librewolf-community/browser/source.git
librewolf_common_url=https://gitlab.com/librewolf-community/browser/common.git
librewolf_settings_url=https://gitlab.com/librewolf-community/settings.git
librewolf_linux_url=https://gitlab.com/librewolf-community/browser/linux.git

case "${DISTRO}" in
   fedora)
      _mozconfig='firefox-mozconfig'
      src_rpm_git_url="https://src.fedoraproject.org/rpms/firefox/"
      src_rpm_git_commit="main"
      ;;
   *)
      echo "Unconfigured DISTRO ${DISTRO}. Where in repo is mozconfig, and what is git url?" 1>&2
      exit 1
   ;;
esac

# user configurable
git_source_dir=${CI_PROJECT_DIR}/git  # where LibreWolf git contents are cached
src_rpm_dir=${CI_PROJECT_DIR}/${firefox_version}/git # where the src git repo is downloaded
work_dir=${CI_PROJECT_DIR}/prepared/

#############################3
# Download initial components
mkdir -p "${work_dir}" ; cd "${work_dir}"
if test -z "${SKIP_DOWNLOAD}" ; then
   mkdir -p "${src_rpm_dir}" ; cd "${src_rpm_dir}"
   git clone "${src_rpm_git_url}" . || :
   test -n "${src_rpm_git_commit}" && {
      git checkout "${src_rpm_git_commit}"
   }
   # Download original firefox source
else : ; fi

# Download git sources
if test -z "${SKIP_GIT}" ; then (
   # yes, use sub-shell for cd. pushd is a bashism.
   mkdir -p "${git_source_dir}" ; cd "${git_source_dir}"
   git clone "${cachypatch_url}" ${git_source_dir}/cachyos-source || :
   git clone "${firedragon_common_url}" ${git_source_dir}/common || :
   git clone "${firedragon_setting_url}" ${git_source_dir}/settings || :
   git clone "${librewolf_source_url}" ${git_source_dir}/source-librewolf || :
   git clone "${librewolf_common_url}" ${git_source_dir}/common-librewolf || :
   git clone "${librewolf_settings_url}" ${git_source_dir}/settings-librewolf || :
   git clone "${librewolf_linux_url}" ${git_source_dir}/linux || :
) ; else : ; fi


#############################3
# Script 1 tasks
# Modify dependencies, and also lw-ize firefox fedora sources
cd "${src_rpm_dir}"
sed -r firefox.spec \
   -e '/^%global mozapp/{s:\/firefox:\/firedragon:;}' \
   -e '/^Name:/{s:firefox:firedragon:;}' \
   -e '/^%package (x11|wayland)/,/^\s*$/{s/firefox/firedragon/g;s/Firefox/FireDragon/g;}' \
   -e '/^BuildRequires.*zip$/aBuildRequires: jack-audio-connection-kit-devel\' \
   -e 'BuildRequires: alsa-lib-devel' \
   > firefox.spec2

#####################################
# Script 2 tasks

# none. Download happened earlier

#####################################
# Script 3 tasks

# Make new source tarball of branding elements
cd "${git_source_dir}"/common/source_files/browser/branding ; tar -zcf "${src_rpm_dir}"/firedragon-branding.tgz firedragon

# add new source tarball for the common.git/source_files/browser/branding/firedragon,a nd other script3 tasks
# just change any logic for enable tests to disable them
cd "${src_rpm_dir}"
# MOZ_SMP_FLAGS is inside the %build and only appears once in the spec file, so should be a good place to add LW-specific settings.
sed -r firefox.spec2 \
   -e '/^%description\s*$/iSource100: firedragon-branding.tgz\' \
   -e 'Source101: firedragon.cfg' \
   -e '/__rm.*\.mozconfig/i( cd browser/branding ; tar -zxf %{SOURCE100} )' \
   -e 's/--enable-tests\>/--disable-tests/g;' \
   -e 's/--enable-debug\>/--disable-debug/g;' \
   -e '/^Version/i%global enable_mozilla_crashreporter 0' \
   -e '/^MOZ_SMP_FLAGS/iecho "ac_add_options --enable-hardening" >> .mozconfig\' \
      -e 'echo "ac_add_options --enable-rust-simd" >> .mozconfig\' \
      -e 'echo "ac_add_options --with-app-name=firedragon" >> .mozconfig\' \
      -e 'echo "ac_add_options --with-app-basename=FireDragon" >> .mozconfig\' \
      -e 'echo "ac_add_options --with-branding=browser/branding/firedragon" >> .mozconfig\' \
      -e 'echo "ac_add_options --with-branding=browser/branding/firedragon" >> .mozconfig\' \
      -e 'echo "ac_add_options --with-distribution-id=org.garudalinux" >> .mozconfig\' \
      -e 'echo "ac_add_options --with-unsigned-addon-scopes=app,system" >> .mozconfig\' \
      -e 'echo "ac_add_options --enable-alsa" >> .mozconfig\' \
      -e 'echo "ac_add_options --enable-jack" >> .mozconfig\' \
      -e 'echo "export MOZ_REQUIRE_SIGNING=0" >> .mozconfig\' \
      -e 'echo "ac_add_options --disable-updater" >> .mozconfig\' \
      -e 'echo "mk_add_options MOZ_CRASHREPORTER=0" >> .mozconfig\' \
      -e 'echo "mk_add_options MOZ_DATA_REPORTING=0" >> .mozconfig\' \
      -e 'echo "mk_add_options MOZ_SERVICES_HEALTHREPORT=0" >> .mozconfig\' \
      -e 'echo "mk_add_options MOZ_TELEMETRY_REPORTING=0" >> .mozconfig' \
      -e '/%global run_firefox_tests [0-9]/s/_tests.*$/_tests 0/;' \
   -e '/__install.*\.1/i%{__cp} -p %{SOURCE101} %{buildroot}/%{mozappdir}/' \
   > firefox.spec3

# Somewhere after the make install, add this firedragon.cfg
cp -p "${git_source_dir}"/settings/firedragon.cfg .

# script 3 notes: fedora firefox already includes some important options:
#    enable-release
#    allow-addon-sideload
#
# Unfortunately aarch64 is outside of my scope.

# still in script 3, add the relevant patches to the spec
#cp -pf "${git_source_dir}"/linux/megabar.patch "${src_rpm_dir}"
#cp -pf "${git_source_dir}"/linux/remove_addons.patch "${src_rpm_dir}"
#cp -pf "${git_source_dir}"/linux/mozilla-vpn-ad.patch "${src_rpm_dir}"
#cp -pf "${git_source_dir}"/linux/context-menu.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/linux/deb_patches/*.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/cachyos-source/patches/gentoo/0016-bmo-1516081-Disable-watchdog-during-PGO-builds.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/remove_addons.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/unity_kde/mozilla-kde.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/unity_kde/firefox-kde.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/unity_kde/unity-menubar.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/sed-patches/disable-pocket.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/sed-patches/allow-searchengines-non-esr.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/sed-patches/stop-undesired-requests.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/urlbarprovider-interventions.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/allow-ubo-private-mode.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/custom-ubo-assets-bootstrap-location.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/pref-naming.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/remap-links.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/hide-default-browser.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/lw-logo-devtools.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/privacy-preferences.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/remove-branding-urlbar.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/remove-cfrprefs.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/remove-organization-policy-banner.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/remove-snippets-from-home.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/website-appearance-ui-rfp.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/ui-patches/handlers.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/disable-data-reporting-at-compile-time.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/hide-passwordmgr.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/source-librewolf/patches/faster-package-multi-locale.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/common/patches/arch/0002-Bug-1804973-Wayland-Check-size-for-valid-EGLWindows-.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/common/patches/custom/librewolf-pref-pane.patch "${src_rpm_dir}"
cp -pf "${git_source_dir}"/common/patches/custom/add_firedragon_svg.patch "${src_rpm_dir}"

# "cd browser/branding" was added in the previous sed command
sed -r firefox.spec3 \
    -e '/^%description\s*$/iPatch900: armhf-reduce-linker-memory-use.patch\' \
      -e 'Patch901: fix-armhf-webrtc-build.patch\' \
      -e 'Patch902: webrtc-fix-compiler-flags-for-armhf.patch\' \
      -e 'Patch903: sandbox-update-arm-syscall-numbers.patch\' \
      -e 'Patch904: remove_addons.patch\' \
      -e 'Patch905: megabar.patch\' \
      -e 'Patch906: reduce-rust-debuginfo.patch\' \
      -e 'Patch907: mozilla-vpn-ad.patch\' \
      -e 'Patch908: context-menu.patch\' \
      -e 'Patch910: remove_addons.patch\' \
      -e 'Patch911: mozilla-kde.patch\' \
      -e 'Patch912: firefox-kde.patch\' \
      -e 'Patch913: unity-menubar.patch\' \
      -e 'Patch914: disable-pocket.patch\' \
      -e 'Patch915: allow-searchengines-non-esr.patch\' \
      -e 'Patch916: stop-undesired-requests.patch\' \
      -e 'Patch917: urlbarprovider-interventions.patch\' \
      -e 'Patch918: allow-ubo-private-mode.patch\' \
      -e 'Patch919: custom-ubo-assets-bootstrap-location.patch\' \
      -e 'Patch920: pref-naming.patch\' \
       -e 'Patch921: remap-links.patch\' \
       -e 'Patch922: hide-default-browser.patch\' \
        -e 'Patch923: lw-logo-devtools.patch\' \
         -e 'Patch924:privacy-preferences.patch\' \
          -e 'Patch925:remove-branding-urlbar.patch\' \
          -e 'Patch926:remove-cfrprefs.patch\' \
          -e 'Patch927:remove-organization-policy-banner.patch\' \
          -e 'Patch928:remove-snippets-from-home.patch\' \
          -e 'Patch929:website-appearance-ui-rfp.patch\' \
          -e 'Patch930:handlers.patch\' \
          -e 'Patch931:disable-data-reporting-at-compile-time.patch\' \
          -e 'Patch932:hide-passwordmgr.patch\' \
          -e 'Patch933:faster-package-multi-locale.patch\' \
          -e 'Patch934:0002-Bug-1804973-Wayland-Check-size-for-valid-EGLWindows-.patch\' \
          -e 'Patch935:librewolf-pref-pane.patch\' \
          -e 'Patch936:add_firedragon_svg.patch\' \
   > firefox.spec4
# unity-menubar is not a feature expected in Fedora at all, so ignore it.

###################################
# Script 4 tasks
# "cd browser/branding" was added in the previous sed command
sed firefox.spec4 \
   -e '/ cd browser\/branding/iexport MOZ_NOSPAM=1' \
   > firefox.spec5

# but the build itself will happen of course in the build environment and not here.

###################################
# Additional steps for rpm implementation
cd "${src_rpm_dir}"
mv -f firefox.spec4 firedragon.spec
sed -i -r firedragon.spec \
   -e '/%changelog\s*$/a* '"$( date "+%a %b %d %Y" ) B. Stack <bgstack15@gmail.com> - ${firefox_version}-${distro_firefox_release}"'\' \
   -e '- Fork to firedragon release.\' -e ''

# upstream fedora firefox src.rpm lists some sources which are only used inside if-endif blocks
# Also, fix %files list, and make langpacks disabled by default, nix the Fedora default bookmarks, and add the firedragon.cfg.
sed -i -r firedragon.spec \
   -e '/^Source[0-9]+:.*mochitest-python\.tar/{i%if 0' -e 'a%endif' -e '}' \
   -e '/^%files -f/,/^%change/{' -e '/_bindir|mozappdir|\/icons/{/browser/!{s/firefox/firedragon/g;}}}' \
   -e '/%bcond_with(out)? langpacks/s/_without/_with/;' \
   -e '/^#.*our default bookmarks/,/^\%endif/{s/^\%if.*/\%if 0/;}' \
   -e '/locale works/,/^\s*$/d' \
   -e '/^%files -f/a%{mozappdir}/firedragon.cfg'

# Apparently firedragon puts its build instructions in objdir/instrumented?
sed -i -r firedragon.spec \
   -e '/^DESTDIR.*make.*objdir/{s/objdir /objdir\/instrumented /;}'

# fix icons, to use the official firedragon branded ones, and the sizes available
# The hicolor/symbolic fix is listed after the _seds definition from the .desktop files
sed -i -r firedragon.spec \
   -e '/^for s in.*do\s*$/,/^done/{/for s in/s/[0-9 ]{5,90}/ 16 32 48 64 128/;s:\/official\/:\/firedragon\/:g;s/firefox\.png/firedragon\.png/g;}' \
   -e '/__cp/{N;/hicolor\/symbolic/{s/apps$/apps\/$( basename %{SOURCE25} | sed -r -e "${_seds}" )/;}}' \
   -e '/__cp/{N;/icons\/hicolor\/\$.s.x/{s/firefox/firedragon/;}}' \
   -e '/%files -f/,/%change/{/22x22/d;s/256x256/128x128/;s/24x24/64x64/;}'

# Convert .desktop files to use Librewolf name, and modify spec to deploy these. Also, convert installed file names to firedragon.
sed -i -r firedragon.spec \
	-e '/__mkdir_p.*applications/a_seds="s/Firefox/LibreWolf/g;s/firefox/firedragon/g;"\' \
	-e 'S20="$( basename "%{SOURCE20}" | sed -r -e ${_seds} )"\' \
	-e 'S31="$( basename "%{SOURCE31}" | sed -r -e ${_seds} )"\' \
	-e 'S29="$( basename "%{SOURCE29}" | sed -r -e ${_seds} )"\' \
	-e 'sed -r %{SOURCE20} -e ${_seds} > ${S20}\' \
	-e 'sed -r %{SOURCE31} -e ${_seds} > ${S31}\' \
	-e 'sed -r %{SOURCE29} -e ${_seds} > ${S29}' -e '/desktop-file-install/{s/%\{SOURCE/$\{S/;}' \
   -e '/set up the/,/for s in/{s/firefox/firedragon/g;}'

# Fix the appdata.xml file too
sed -r -i firedragon.spec \
   -e '/__sed/{N;N;/>.*\/metainfo\/firefox\.app/{s/firefox/firedragon/g;}}'

# Fix the /usr/bin/firedragon script to run firedragon, and the Fedora-ized restorecon step in that script
# Someday this will be ~/.config/firedragon and not ~/.firedragon, but not yet for v88.0
sed -r -i firedragon.spec \
   -e '/__sed.*_bindir}\/firedragon$/a%{__sed} -i %{buildroot}%{_bindir}/firedragon \\\' \
   -e '   -e "${_seds}" \\\' \
   -e '   -e "/restorecon/{s/\.mozilla\\/firefox/\.firedragon/;}"'

# Fix the distribution.ini file
sed -r -i firedragon.spec \
   -e '/__cp.*\/distribution$/{acat > distribution.ini <<END\' \
   -e '[Global]\' \
   -e 'id=garudalinux\' \
   -e 'version=1.0\' \
   -e 'about=FireDragon for Fedora\' \
   -e '\' \
   -e '[Preferences]\' \
   -e 'app.distributor=garudalinux\' \
   -e 'app.distributor.channel=firedragon\' \
   -e 'app.partner.garudalinux=garudalinux\' \
   -e 'END\' \
   -e 'install -Dvm644 distribution.ini %{buildroot}%{mozappdir}/distribution' \
   -e ';}'

# Build the src.rpm asset, which is not strictly required for the git repo which COPR can ingest.
if test -z "${SKIP_SRC_RPM}" ; then
   if test -f "firefox-${firefox_version}.source.tar.xz" || test -z "${SKIP_SPECTOOL}" ; then
      spectool -g firedragon.spec --source 0 # from rpmdevtools
   fi
   # Upstream fedora firefox does not include some tarballs for some weird reason, so let's pull them from Fedora src.rpm and rip them out
   # Unfortunately the version available may not be identical to what is in src.fedoraproject.org
   cd "${work_dir}" ; dnf download --source firefox
   this_srcrpm="$( find . -iname 'firefox-*.src.rpm' -printf '%f\n' | sort | tail -n1 )"
   # find the tarballs closest to these expressions: cbindgen-vendor
   cd "${src_rpm_dir}" ; rpm2cpio "${work_dir}/${this_srcrpm}" | cpio -idm $( spectool -l --sources "${src_rpm_dir}/firedragon.spec" | awk '$NF ~/z$/ && $NF ~ /cbindgen/{print $NF}' )
   # I only know how to get rpmbuild to pull sources from ~/rpmbuild/SOURCES
   mkdir -p ~/rpmbuild/SOURCES
   cd "${src_rpm_dir}" ; cp -pf * ~/rpmbuild/SOURCES ;
   rpmbuild -bs firedragon.spec # creates the firedragon src.rpm in ~/rpmbuild/SRPMS/
   cp -p ~/rpmbuild/SRPMS/firedragon-${firefox_version}-${distro_firefox_version}*.src.rpm "${work_dir}"
fi
