#!/bin/sh
# Purpose: help librewolf-fedora-ff modified git repo by adding its readme and useful git config
# Startdate: 2021-04-29
# Dependencies:
#    git

#####################################
# Load settings
# basically, dot-source the conf file.
test -z "${librewolf_rpm_conf}" && export librewolf_rpm_conf="$( find "$( dirname "${0}" )" -maxdepth 2 -name "prep-librewolf-rpm.conf" -print 2>/dev/null | head -n1 )"
test ! -r "${librewolf_rpm_conf}" && { echo "Unable to load config file, which should be named prep-librewolf-rpm.conf. Aborted." 1>&2 ; exit 1 ; }
. "${librewolf_rpm_conf}"
script_dir="$( dirname "$( readlink -f "${0}" )" )"

# switch to target directory
src_rpm_dir=${CI_PROJECT_DIR}/${firefox_version}/git
cd "${src_rpm_dir}"
if test "$( git remote -v | awk '$1=="origin" && $3~/fetch/{print $2}' )" != "https://src.fedoraproject.org/rpms/firefox/" ; then
   echo "Cannot find git repo that cloned https://src.fedoraproject.org/rpms/firefox/. Aborted." 1>&2
   exit 1
fi
if ! test -f librewolf.spec ; then
   echo "Cannot determine that prep-librewolf-rpm.sh has run yet! Where is librewolf.spec?" 1>&2
   exit 1
fi
# So if we get here, we're in the right spot

# Make file changes
cp -p "${script_dir}/../for-repo/README.md" .
sed -i -r .gitignore \
   -e '/cbindgen-vendor/d'
grep -qE '\*\.spec\?' .gitignore || echo '*.spec?' >> .gitignore
grep -qE '\.\*\.swp' .gitignore || echo '.*.swp' >> .gitignore
# remove sources file which uses dist-git and lookaside cache
rm -f sources

# Add git remote
git remote add gitlab https://gitlab.com/bgstack15/librewolf-fedora-ff.git
git pull --all
