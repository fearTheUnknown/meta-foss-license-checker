#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: MIT
#

# BB Class inspired by ebuild.sh
#
# This class will test files after installation for certain
# security issues and other kind of issues.
#
# Checks we do:
#  -Check the ownership and permissions
#  -Check the RUNTIME path for the $TMPDIR
#  -Check if .la files wrongly point to workdir
#  -Check if .pc files wrongly point to workdir
#  -Check if packages contains .debug directories or .so files
#   where they should be in -dev or -dbg
#  -Check if config.log contains traces to broken autoconf tests
#  -Check invalid characters (non-utf8) on some package metadata
#  -Ensure that binaries in base_[bindir|sbindir|libdir] do not link
#   into exec_prefix
#  -Check that scripts in base_[bindir|sbindir|libdir] do not reference
#   files under exec_prefix
#  -Check if the package name is upper case

# Elect whether a given type of error is a warning or error, they may
# have been set by other files.
WARN_QA ?= " libdir xorg-driver-abi buildpaths \
            textrel incompatible-license files-invalid \
            infodir build-deps src-uri-bad symlink-to-sysroot multilib \
            invalid-packageconfig host-user-contaminated uppercase-pn \
            mime mime-xdg unlisted-pkg-lics unhandled-features-check \
            missing-update-alternatives native-last missing-ptest \
            license-exists license-no-generic license-syntax license-format \
            license-incompatible license-file-missing obsolete-license \
            32bit-time virtual-slash \
            "
ERROR_QA ?= "dev-so debug-deps dev-deps debug-files arch pkgconfig la \
            perms dep-cmp pkgvarcheck perm-config perm-line perm-link \
            split-strip packages-list pkgv-undefined var-undefined \
            version-going-backwards expanded-d invalid-chars \
            license-checksum dev-elf file-rdeps configure-unsafe \
            configure-gettext perllocalpod shebang-size \
            already-stripped installed-vs-shipped ldflags compile-host-path \
            install-host-path pn-overrides unknown-configure-option \
            useless-rpaths rpaths staticdev empty-dirs \
            patch-fuzz \
            "
# Add usrmerge QA check based on distro feature
ERROR_QA:append = "${@bb.utils.contains('DISTRO_FEATURES', 'usrmerge', ' usrmerge', '', d)}"
ERROR_QA:append:layer-core = " patch-status"
WARN_QA:append:layer-core = " missing-metadata missing-maintainer"

FAKEROOT_QA = "host-user-contaminated"
FAKEROOT_QA[doc] = "QA tests which need to run under fakeroot. If any \
enabled tests are listed here, the do_package_qa task will run under fakeroot."

ALL_QA = "${WARN_QA} ${ERROR_QA}"

UNKNOWN_CONFIGURE_OPT_IGNORE ?= "--enable-nls --disable-nls --disable-silent-rules --disable-dependency-tracking --with-libtool-sysroot --disable-static"

# This is a list of directories that are expected to be empty.
QA_EMPTY_DIRS ?= " \
    /dev/pts \
    /media \
    /proc \
    /run \
    /tmp \
    ${localstatedir}/run \
    ${localstatedir}/volatile \
"
# It is possible to specify why a directory is expected to be empty by defining
# QA_EMPTY_DIRS_RECOMMENDATION:<path>, which will then be included in the error
# message if the directory is not empty. If it is not specified for a directory,
# then "but it is expected to be empty" will be used.

def package_qa_clean_path(path, d, pkg=None):
    """
    Remove redundant paths from the path for display.  If pkg isn't set then
    TMPDIR is stripped, otherwise PKGDEST/pkg is stripped.
    """
    if pkg:
        path = path.replace(os.path.join(d.getVar("PKGDEST"), pkg), "/")
    return path.replace(d.getVar("TMPDIR"), "/").replace("//", "/")

QAPATHTEST[shebang-size] = "package_qa_check_shebang_size"
def package_qa_check_shebang_size(path, name, d, elf, messages):
    import stat
    if os.path.islink(path) or stat.S_ISFIFO(os.stat(path).st_mode) or elf:
        return

    try:
        with open(path, 'rb') as f:
            stanza = f.readline(130)
    except IOError:
        return

    if stanza.startswith(b'#!'):
        try:
            stanza.decode("utf-8")
        except UnicodeDecodeError:
            #If it is not a text file, it is not a script
            return

        if len(stanza) > 129:
            oe.qa.add_message(messages, "shebang-size", "%s: %s maximum shebang size exceeded, the maximum size is 128." % (name, package_qa_clean_path(path, d, name)))
            return

QAPATHTEST[libexec] = "package_qa_check_libexec"
def package_qa_check_libexec(path,name, d, elf, messages):

    # Skip the case where the default is explicitly /usr/libexec
    libexec = d.getVar('libexecdir')
    if libexec == "/usr/libexec":
        return True

    if 'libexec' in path.split(os.path.sep):
        oe.qa.add_message(messages, "libexec", "%s: %s is using libexec please relocate to %s" % (name, package_qa_clean_path(path, d, name), libexec))
        return False

    return True

QAPATHTEST[rpaths] = "package_qa_check_rpath"
def package_qa_check_rpath(file,name, d, elf, messages):
    """
    Check for dangerous RPATHs
    """
    if not elf:
        return

    if os.path.islink(file):
        return

    bad_dirs = [d.getVar('BASE_WORKDIR'), d.getVar('STAGING_DIR_TARGET')]

    phdrs = elf.run_objdump("-p", d)

    import re
    rpath_re = re.compile(r"\s+RPATH\s+(.*)")
    for line in phdrs.split("\n"):
        m = rpath_re.match(line)
        if m:
            rpath = m.group(1)
            for dir in bad_dirs:
                if dir in rpath:
                    oe.qa.add_message(messages, "rpaths", "package %s contains bad RPATH %s in file %s" % (name, rpath, file))

QAPATHTEST[useless-rpaths] = "package_qa_check_useless_rpaths"
def package_qa_check_useless_rpaths(file, name, d, elf, messages):
    """
    Check for RPATHs that are useless but not dangerous
    """
    def rpath_eq(a, b):
        return os.path.normpath(a) == os.path.normpath(b)

    if not elf:
        return

    if os.path.islink(file):
        return

    libdir = d.getVar("libdir")
    base_libdir = d.getVar("base_libdir")

    phdrs = elf.run_objdump("-p", d)

    import re
    rpath_re = re.compile(r"\s+RPATH\s+(.*)")
    for line in phdrs.split("\n"):
        m = rpath_re.match(line)
        if m:
            rpath = m.group(1)
            if rpath_eq(rpath, libdir) or rpath_eq(rpath, base_libdir):
                # The dynamic linker searches both these places anyway.  There is no point in
                # looking there again.
                oe.qa.add_message(messages, "useless-rpaths", "%s: %s contains probably-redundant RPATH %s" % (name, package_qa_clean_path(file, d, name), rpath))

QAPATHTEST[dev-so] = "package_qa_check_dev"
def package_qa_check_dev(path, name, d, elf, messages):
    """
    Check for ".so" library symlinks in non-dev packages
    """

    if not name.endswith("-dev") and not name.endswith("-dbg") and not name.endswith("-ptest") and not name.startswith("nativesdk-") and path.endswith(".so") and os.path.islink(path):
        oe.qa.add_message(messages, "dev-so", "non -dev/-dbg/nativesdk- package %s contains symlink .so '%s'" % \
                 (name, package_qa_clean_path(path, d, name)))

QAPATHTEST[dev-elf] = "package_qa_check_dev_elf"
def package_qa_check_dev_elf(path, name, d, elf, messages):
    """
    Check that -dev doesn't contain real shared libraries.  The test has to
    check that the file is not a link and is an ELF object as some recipes
    install link-time .so files that are linker scripts.
    """
    if name.endswith("-dev") and path.endswith(".so") and not os.path.islink(path) and elf:
        oe.qa.add_message(messages, "dev-elf", "-dev package %s contains non-symlink .so '%s'" % \
                 (name, package_qa_clean_path(path, d, name)))

QAPATHTEST[staticdev] = "package_qa_check_staticdev"
def package_qa_check_staticdev(path, name, d, elf, messages):
    """
    Check for ".a" library in non-staticdev packages
    There are a number of exceptions to this rule, -pic packages can contain
    static libraries, the _nonshared.a belong with their -dev packages and
    libgcc.a, libgcov.a will be skipped in their packages
    """

    if not name.endswith("-pic") and not name.endswith("-staticdev") and not name.endswith("-ptest") and path.endswith(".a") and not path.endswith("_nonshared.a") and not '/usr/lib/debug-static/' in path and not '/.debug-static/' in path:
        oe.qa.add_message(messages, "staticdev", "non -staticdev package contains static .a library: %s path '%s'" % \
                 (name, package_qa_clean_path(path, d, name)))

QAPATHTEST[mime] = "package_qa_check_mime"
def package_qa_check_mime(path, name, d, elf, messages):
    """
    Check if package installs mime types to /usr/share/mime/packages
    while no inheriting mime.bbclass
    """

    if d.getVar("datadir") + "/mime/packages" in path and path.endswith('.xml') and not bb.data.inherits_class("mime", d):
        oe.qa.add_message(messages, "mime", "package contains mime types but does not inherit mime: %s path '%s'" % \
                 (name, package_qa_clean_path(path, d, name)))

QAPATHTEST[mime-xdg] = "package_qa_check_mime_xdg"
def package_qa_check_mime_xdg(path, name, d, elf, messages):
    """
    Check if package installs desktop file containing MimeType and requires
    mime-types.bbclass to create /usr/share/applications/mimeinfo.cache
    """

    if d.getVar("datadir") + "/applications" in path and path.endswith('.desktop') and not bb.data.inherits_class("mime-xdg", d):
        mime_type_found = False
        try:
            with open(path, 'r') as f:
                for line in f.read().split('\n'):
                    if 'MimeType' in line:
                        mime_type_found = True
                        break;
        except:
            # At least libreoffice installs symlinks with absolute paths that are dangling here.
            # We could implement some magic but for few (one) recipes it is not worth the effort so just warn:
            wstr = "%s cannot open %s - is it a symlink with absolute path?\n" % (name, package_qa_clean_path(path, d, name))
            wstr += "Please check if (linked) file contains key 'MimeType'.\n"
            pkgname = name
            if name == d.getVar('PN'):
                pkgname = '${PN}'
            wstr += "If yes: add \'inhert mime-xdg\' and \'MIME_XDG_PACKAGES += \"%s\"\' / if no add \'INSANE_SKIP:%s += \"mime-xdg\"\' to recipe." % (pkgname, pkgname)
            oe.qa.add_message(messages, "mime-xdg", wstr)
        if mime_type_found:
            oe.qa.add_message(messages, "mime-xdg", "%s: contains desktop file with key 'MimeType' but does not inhert mime-xdg: %s" % \
                    (name, package_qa_clean_path(path, d, name)))

def package_qa_check_libdir(d):
    """
    Check for wrong library installation paths. For instance, catch
    recipes installing /lib/bar.so when ${base_libdir}="lib32" or
    installing in /usr/lib64 when ${libdir}="/usr/lib"
    """
    import re

    pkgdest = d.getVar('PKGDEST')
    base_libdir = d.getVar("base_libdir") + os.sep
    libdir = d.getVar("libdir") + os.sep
    libexecdir = d.getVar("libexecdir") + os.sep
    exec_prefix = d.getVar("exec_prefix") + os.sep

    messages = []

    # The re's are purposely fuzzy, as some there are some .so.x.y.z files
    # that don't follow the standard naming convention. It checks later
    # that they are actual ELF files
    lib_re = re.compile(r"^/lib.+\.so(\..+)?$")
    exec_re = re.compile(r"^%s.*/lib.+\.so(\..+)?$" % exec_prefix)

    for root, dirs, files in os.walk(pkgdest):
        if root == pkgdest:
            # Skip subdirectories for any packages with libdir in INSANE_SKIP
            skippackages = []
            for package in dirs:
                if 'libdir' in (d.getVar('INSANE_SKIP:' + package) or "").split():
                    bb.note("Package %s skipping libdir QA test" % (package))
                    skippackages.append(package)
                elif d.getVar('PACKAGE_DEBUG_SPLIT_STYLE') == 'debug-file-directory' and package.endswith("-dbg"):
                    bb.note("Package %s skipping libdir QA test for PACKAGE_DEBUG_SPLIT_STYLE equals debug-file-directory" % (package))
                    skippackages.append(package)
            for package in skippackages:
                dirs.remove(package)
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, pkgdest)
            if os.sep in rel_path:
                package, rel_path = rel_path.split(os.sep, 1)
                rel_path = os.sep + rel_path
                if lib_re.match(rel_path):
                    if base_libdir not in rel_path:
                        # make sure it's an actual ELF file
                        elf = oe.qa.ELFFile(full_path)
                        try:
                            elf.open()
                            messages.append("%s: found library in wrong location: %s" % (package, rel_path))
                        except (oe.qa.NotELFFileError, FileNotFoundError):
                            pass
                if exec_re.match(rel_path):
                    if libdir not in rel_path and libexecdir not in rel_path:
                        # make sure it's an actual ELF file
                        elf = oe.qa.ELFFile(full_path)
                        try:
                            elf.open()
                            messages.append("%s: found library in wrong location: %s" % (package, rel_path))
                        except (oe.qa.NotELFFileError, FileNotFoundError):
                            pass

    if messages:
        oe.qa.handle_error("libdir", "\n".join(messages), d)

QAPATHTEST[debug-files] = "package_qa_check_dbg"
def package_qa_check_dbg(path, name, d, elf, messages):
    """
    Check for ".debug" files or directories outside of the dbg package
    """

    if not "-dbg" in name and not "-ptest" in name:
        if '.debug' in path.split(os.path.sep):
            oe.qa.add_message(messages, "debug-files", "%s: non debug package contains .debug directory %s" % \
                     (name, package_qa_clean_path(path, d, name)))

QAPATHTEST[arch] = "package_qa_check_arch"
def package_qa_check_arch(path,name,d, elf, messages):
    """
    Check if archs are compatible
    """
    import re, oe.elf

    if not elf:
        return

    host_os   = d.getVar('HOST_OS')
    host_arch = d.getVar('HOST_ARCH')
    provides = d.getVar('PROVIDES')
    bpn = d.getVar('BPN')

    if host_arch == "allarch":
        pn = d.getVar('PN')
        oe.qa.add_message(messages, "arch", pn + ": Recipe inherits the allarch class, but has packaged architecture-specific binaries")
        return

    # avoid following links to /usr/bin (e.g. on udev builds)
    # we will check the files pointed to anyway...
    if os.path.islink(path):
        return

    #if this will throw an exception, then fix the dict above
    (machine, osabi, abiversion, littleendian, bits) \
        = oe.elf.machine_dict(d)[host_os][host_arch]

    # Check the architecture and endiannes of the binary
    is_32 = (("virtual/kernel" in provides) or bb.data.inherits_class("module", d)) and \
            (host_os == "linux-gnux32" or host_os == "linux-muslx32" or \
            host_os == "linux-gnu_ilp32" or re.match(r'mips64.*32', d.getVar('DEFAULTTUNE')))
    is_bpf = (oe.qa.elf_machine_to_string(elf.machine()) == "BPF")
    if not ((machine == elf.machine()) or is_32 or is_bpf):
        oe.qa.add_message(messages, "arch", "Architecture did not match (%s, expected %s) in %s" % \
                 (oe.qa.elf_machine_to_string(elf.machine()), oe.qa.elf_machine_to_string(machine), package_qa_clean_path(path, d, name)))
    elif not ((bits == elf.abiSize()) or is_32 or is_bpf):
        oe.qa.add_message(messages, "arch", "Bit size did not match (%d, expected %d) in %s" % \
                 (elf.abiSize(), bits, package_qa_clean_path(path, d, name)))
    elif not ((littleendian == elf.isLittleEndian()) or is_bpf):
        oe.qa.add_message(messages, "arch", "Endiannes did not match (%d, expected %d) in %s" % \
                 (elf.isLittleEndian(), littleendian, package_qa_clean_path(path, d, name)))

QAPATHTEST[desktop] = "package_qa_check_desktop"
def package_qa_check_desktop(path, name, d, elf, messages):
    """
    Run all desktop files through desktop-file-validate.
    """
    if path.endswith(".desktop"):
        desktop_file_validate = os.path.join(d.getVar('STAGING_BINDIR_NATIVE'),'desktop-file-validate')
        output = os.popen("%s %s" % (desktop_file_validate, path))
        # This only produces output on errors
        for l in output:
            oe.qa.add_message(messages, "desktop", "Desktop file issue: " + l.strip())

QAPATHTEST[textrel] = "package_qa_textrel"
def package_qa_textrel(path, name, d, elf, messages):
    """
    Check if the binary contains relocations in .text
    """

    if not elf:
        return

    if os.path.islink(path):
        return

    phdrs = elf.run_objdump("-p", d)
    sane = True

    import re
    textrel_re = re.compile(r"\s+TEXTREL\s+")
    for line in phdrs.split("\n"):
        if textrel_re.match(line):
            sane = False
            break

    if not sane:
        path = package_qa_clean_path(path, d, name)
        oe.qa.add_message(messages, "textrel", "%s: ELF binary %s has relocations in .text" % (name, path))

QAPATHTEST[ldflags] = "package_qa_hash_style"
def package_qa_hash_style(path, name, d, elf, messages):
    """
    Check if the binary has the right hash style...
    """

    if not elf:
        return

    if os.path.islink(path):
        return

    gnu_hash = "--hash-style=gnu" in d.getVar('LDFLAGS')
    if not gnu_hash:
        gnu_hash = "--hash-style=both" in d.getVar('LDFLAGS')
    if not gnu_hash:
        return

    sane = False
    has_syms = False

    phdrs = elf.run_objdump("-p", d)

    # If this binary has symbols, we expect it to have GNU_HASH too.
    for line in phdrs.split("\n"):
        if "SYMTAB" in line:
            has_syms = True
        if "GNU_HASH" in line or "MIPS_XHASH" in line:
            sane = True
        if ("[mips32]" in line or "[mips64]" in line) and d.getVar('TCLIBC') == "musl":
            sane = True
    if has_syms and not sane:
        path = package_qa_clean_path(path, d, name)
        oe.qa.add_message(messages, "ldflags", "File %s in package %s doesn't have GNU_HASH (didn't pass LDFLAGS?)" % (path, name))


QAPATHTEST[buildpaths] = "package_qa_check_buildpaths"
def package_qa_check_buildpaths(path, name, d, elf, messages):
    """
    Check for build paths inside target files and error if paths are not
    explicitly ignored.
    """
    import stat

    # Ignore symlinks/devs/fifos
    mode = os.lstat(path).st_mode
    if stat.S_ISLNK(mode) or stat.S_ISBLK(mode) or stat.S_ISFIFO(mode) or stat.S_ISCHR(mode) or stat.S_ISSOCK(mode):
        return

    tmpdir = bytes(d.getVar('TMPDIR'), encoding="utf-8")
    with open(path, 'rb') as f:
        file_content = f.read()
        if tmpdir in file_content:
            trimmed = path.replace(os.path.join (d.getVar("PKGDEST"), name), "")
            oe.qa.add_message(messages, "buildpaths", "File %s in package %s contains reference to TMPDIR" % (trimmed, name))


QAPATHTEST[xorg-driver-abi] = "package_qa_check_xorg_driver_abi"
def package_qa_check_xorg_driver_abi(path, name, d, elf, messages):
    """
    Check that all packages containing Xorg drivers have ABI dependencies
    """

    # Skip dev, dbg or nativesdk packages
    if name.endswith("-dev") or name.endswith("-dbg") or name.startswith("nativesdk-"):
        return

    driverdir = d.expand("${libdir}/xorg/modules/drivers/")
    if driverdir in path and path.endswith(".so"):
        mlprefix = d.getVar('MLPREFIX') or ''
        for rdep in bb.utils.explode_deps(d.getVar('RDEPENDS:' + name) or ""):
            if rdep.startswith("%sxorg-abi-" % mlprefix):
                return
        oe.qa.add_message(messages, "xorg-driver-abi", "Package %s contains Xorg driver (%s) but no xorg-abi- dependencies" % (name, os.path.basename(path)))

QAPATHTEST[infodir] = "package_qa_check_infodir"
def package_qa_check_infodir(path, name, d, elf, messages):
    """
    Check that /usr/share/info/dir isn't shipped in a particular package
    """
    infodir = d.expand("${infodir}/dir")

    if infodir in path:
        oe.qa.add_message(messages, "infodir", "The /usr/share/info/dir file is not meant to be shipped in a particular package.")

QAPATHTEST[symlink-to-sysroot] = "package_qa_check_symlink_to_sysroot"
def package_qa_check_symlink_to_sysroot(path, name, d, elf, messages):
    """
    Check that the package doesn't contain any absolute symlinks to the sysroot.
    """
    if os.path.islink(path):
        target = os.readlink(path)
        if os.path.isabs(target):
            tmpdir = d.getVar('TMPDIR')
            if target.startswith(tmpdir):
                trimmed = path.replace(os.path.join (d.getVar("PKGDEST"), name), "")
                oe.qa.add_message(messages, "symlink-to-sysroot", "Symlink %s in %s points to TMPDIR" % (trimmed, name))

QAPATHTEST[32bit-time] = "check_32bit_symbols"
def check_32bit_symbols(path, packagename, d, elf, messages):
    """
    Check that ELF files do not use any 32 bit time APIs from glibc.
    """
    thirtytwo_bit_time_archs = {'arm','armeb','mipsarcho32','powerpc','x86'}
    overrides = set(d.getVar('OVERRIDES').split(':'))
    if not (thirtytwo_bit_time_archs & overrides):
        return

    import re
    # This list is manually constructed by searching the image folder of the
    # glibc recipe for __USE_TIME_BITS64.  There is no good way to do this
    # automatically.
    api32 = {
        # /usr/include/time.h
        "clock_getres", "clock_gettime", "clock_nanosleep", "clock_settime",
        "ctime", "ctime_r", "difftime", "gmtime", "gmtime_r", "localtime",
        "localtime_r", "mktime", "nanosleep", "time", "timegm", "timelocal",
        "timer_gettime", "timer_settime", "timespec_get", "timespec_getres",
        # /usr/include/bits/time.h
        "clock_adjtime",
        # /usr/include/signal.h
        "sigtimedwait",
        # /usr/include/sys/time.h
        "adjtime",
        "futimes", "futimesat", "getitimer", "gettimeofday", "lutimes",
        "setitimer", "settimeofday", "utimes",
        # /usr/include/sys/timex.h
        "adjtimex", "ntp_adjtime", "ntp_gettime", "ntp_gettimex",
        # /usr/include/sys/wait.h
        "wait3", "wait4",
        # /usr/include/sys/stat.h
        "fstat", "fstat64", "fstatat", "fstatat64", "futimens", "lstat",
        "lstat64", "stat", "stat64", "utimensat",
        # /usr/include/sys/poll.h
        "ppoll",
        # /usr/include/sys/resource.h
        "getrusage",
        # /usr/include/sys/ioctl.h
        "ioctl",
        # /usr/include/sys/select.h
        "select", "pselect",
        # /usr/include/sys/prctl.h
        "prctl",
        # /usr/include/sys/epoll.h
        "epoll_pwait2",
        # /usr/include/sys/timerfd.h
        "timerfd_gettime", "timerfd_settime",
        # /usr/include/sys/socket.h
        "getsockopt", "recvmmsg", "recvmsg", "sendmmsg", "sendmsg",
        "setsockopt",
        # /usr/include/sys/msg.h
        "msgctl",
        # /usr/include/sys/sem.h
        "semctl", "semtimedop",
        # /usr/include/sys/shm.h
        "shmctl",
        # /usr/include/pthread.h
        "pthread_clockjoin_np", "pthread_cond_clockwait",
        "pthread_cond_timedwait", "pthread_mutex_clocklock",
        "pthread_mutex_timedlock", "pthread_rwlock_clockrdlock",
        "pthread_rwlock_clockwrlock", "pthread_rwlock_timedrdlock",
        "pthread_rwlock_timedwrlock", "pthread_timedjoin_np",
        # /usr/include/semaphore.h
        "sem_clockwait", "sem_timedwait",
        # /usr/include/threads.h
        "cnd_timedwait", "mtx_timedlock", "thrd_sleep",
        # /usr/include/aio.h
        "aio_cancel", "aio_error", "aio_read", "aio_return", "aio_suspend",
        "aio_write", "lio_listio",
        # /usr/include/mqueue.h
        "mq_timedreceive", "mq_timedsend",
        # /usr/include/glob.h
        "glob", "glob64", "globfree", "globfree64",
        # /usr/include/sched.h
        "sched_rr_get_interval",
        # /usr/include/fcntl.h
        "fcntl", "fcntl64",
        # /usr/include/utime.h
        "utime",
        # /usr/include/ftw.h
        "ftw", "ftw64", "nftw", "nftw64",
        # /usr/include/fts.h
        "fts64_children", "fts64_close", "fts64_open", "fts64_read",
        "fts64_set", "fts_children", "fts_close", "fts_open", "fts_read",
        "fts_set",
        # /usr/include/netdb.h
        "gai_suspend",
    }

    ptrn = re.compile(
        r'''
        (?P<value>[\da-fA-F]+) \s+
        (?P<flags>[lgu! ][w ][C ][W ][Ii ][dD ]F) \s+
        (?P<section>\*UND\*) \s+
        (?P<alignment>(?P<size>[\da-fA-F]+)) \s+
        (?P<symbol>
        ''' +
        r'(?P<notag>' + r'|'.join(sorted(api32)) + r')' +
        r'''
        (@+(?P<tag>GLIBC_\d+\.\d+\S*)))
        ''', re.VERBOSE
    )

    # elf is a oe.qa.ELFFile object
    if elf is not None:
        phdrs = elf.run_objdump("-tw", d)
        syms = re.finditer(ptrn, phdrs)
        usedapis = {sym.group('notag') for sym in syms}
        if usedapis:
            elfpath = package_qa_clean_path(path, d, packagename)
            # Remove any .debug dir, heuristic that probably works
            # At this point, any symbol information is stripped into the debug
            # package, so that is the only place we will find them.
            elfpath = elfpath.replace('.debug/', '')
            allowed = "32bit-time" in (d.getVar('INSANE_SKIP') or '').split()
            if not allowed:
                msgformat = elfpath + " uses 32-bit api '%s'"
                for sym in usedapis:
                    oe.qa.add_message(messages, '32bit-time', msgformat % sym)
                oe.qa.add_message(
                    messages, '32bit-time',
                    'Suppress with INSANE_SKIP = "32bit-time"'
                )

# Check license variables
do_populate_lic[postfuncs] += "populate_lic_qa_checksum"
python populate_lic_qa_checksum() {
    """
    Check for changes in the license files.
    """

    lic_files = d.getVar('LIC_FILES_CHKSUM') or ''
    lic = d.getVar('LICENSE')
    pn = d.getVar('PN')

    if lic == "CLOSED":
        return

    if not lic_files and d.getVar('SRC_URI'):
        oe.qa.handle_error("license-checksum", pn + ": Recipe file fetches files and does not have license file information (LIC_FILES_CHKSUM)", d)

    srcdir = d.getVar('S')
    corebase_licensefile = d.getVar('COREBASE') + "/LICENSE"
    for url in lic_files.split():
        try:
            (type, host, path, user, pswd, parm) = bb.fetch.decodeurl(url)
        except bb.fetch.MalformedUrl:
            oe.qa.handle_error("license-checksum", pn + ": LIC_FILES_CHKSUM contains an invalid URL: " + url, d)
            continue
        srclicfile = os.path.join(srcdir, path)
        if not os.path.isfile(srclicfile):
            oe.qa.handle_error("license-checksum", pn + ": LIC_FILES_CHKSUM points to an invalid file: " + srclicfile, d)
            continue

        if (srclicfile == corebase_licensefile):
            bb.warn("${COREBASE}/LICENSE is not a valid license file, please use '${COMMON_LICENSE_DIR}/MIT' for a MIT License file in LIC_FILES_CHKSUM. This will become an error in the future")

        recipemd5 = parm.get('md5', '')
        beginline, endline = 0, 0
        if 'beginline' in parm:
            beginline = int(parm['beginline'])
        if 'endline' in parm:
            endline = int(parm['endline'])

        if (not beginline) and (not endline):
            md5chksum = bb.utils.md5_file(srclicfile)
            with open(srclicfile, 'r', errors='replace') as f:
                license = f.read().splitlines()
        else:
            with open(srclicfile, 'rb') as f:
                import hashlib
                lineno = 0
                license = []
                try:
                    m = hashlib.new('MD5', usedforsecurity=False)
                except TypeError:
                    m = hashlib.new('MD5')
                for line in f:
                    lineno += 1
                    if (lineno >= beginline):
                        if ((lineno <= endline) or not endline):
                            m.update(line)
                            license.append(line.decode('utf-8', errors='replace').rstrip())
                        else:
                            break
                md5chksum = m.hexdigest()
        if recipemd5 == md5chksum:
            bb.note (pn + ": md5 checksum matched for ", url)
        else:
            if recipemd5:
                msg = pn + ": The LIC_FILES_CHKSUM does not match for " + url
                msg = msg + "\n" + pn + ": The new md5 checksum is " + md5chksum
                max_lines = int(d.getVar('QA_MAX_LICENSE_LINES') or 20)
                if not license or license[-1] != '':
                    # Ensure that our license text ends with a line break
                    # (will be added with join() below).
                    license.append('')
                remove = len(license) - max_lines
                if remove > 0:
                    start = max_lines // 2
                    end = start + remove - 1
                    del license[start:end]
                    license.insert(start, '...')
                msg = msg + "\n" + pn + ": Here is the selected license text:" + \
                        "\n" + \
                        "{:v^70}".format(" beginline=%d " % beginline if beginline else "") + \
                        "\n" + "\n".join(license) + \
                        "{:^^70}".format(" endline=%d " % endline if endline else "")
                if beginline:
                    if endline:
                        srcfiledesc = "%s (lines %d through to %d)" % (srclicfile, beginline, endline)
                    else:
                        srcfiledesc = "%s (beginning on line %d)" % (srclicfile, beginline)
                elif endline:
                    srcfiledesc = "%s (ending on line %d)" % (srclicfile, endline)
                else:
                    srcfiledesc = srclicfile
                msg = msg + "\n" + pn + ": Check if the license information has changed in %s to verify that the LICENSE value \"%s\" remains valid" % (srcfiledesc, lic)

            else:
                msg = pn + ": LIC_FILES_CHKSUM is not specified for " +  url
                msg = msg + "\n" + pn + ": The md5 checksum is " + md5chksum
            oe.qa.handle_error("license-checksum", msg, d)

    oe.qa.exit_if_errors(d)
}

def qa_check_staged(path,d):
    """
    Check staged la and pc files for common problems like references to the work
    directory.

    As this is run after every stage we should be able to find the one
    responsible for the errors easily even if we look at every .pc and .la file.
    """

    tmpdir = d.getVar('TMPDIR')
    workdir = os.path.join(tmpdir, "work")
    recipesysroot = d.getVar("RECIPE_SYSROOT")

    if bb.data.inherits_class("native", d) or bb.data.inherits_class("cross", d):
        pkgconfigcheck = workdir
    else:
        pkgconfigcheck = tmpdir

    skip = (d.getVar('INSANE_SKIP') or "").split()
    skip_la = False
    if 'la' in skip:
        bb.note("Recipe %s skipping qa checking: la" % d.getVar('PN'))
        skip_la = True

    skip_pkgconfig = False
    if 'pkgconfig' in skip:
        bb.note("Recipe %s skipping qa checking: pkgconfig" % d.getVar('PN'))
        skip_pkgconfig = True

    skip_shebang_size = False
    if 'shebang-size' in skip:
        bb.note("Recipe %s skipping qa checkking: shebang-size" % d.getVar('PN'))
        skip_shebang_size = True

    # find all .la and .pc files
    # read the content
    # and check for stuff that looks wrong
    for root, dirs, files in os.walk(path):
        for file in files:
            path = os.path.join(root,file)
            if file.endswith(".la") and not skip_la:
                with open(path) as f:
                    file_content = f.read()
                    file_content = file_content.replace(recipesysroot, "")
                    if workdir in file_content:
                        error_msg = "%s failed sanity test (workdir) in path %s" % (file,root)
                        oe.qa.handle_error("la", error_msg, d)
            elif file.endswith(".pc") and not skip_pkgconfig:
                with open(path) as f:
                    file_content = f.read()
                    file_content = file_content.replace(recipesysroot, "")
                    if pkgconfigcheck in file_content:
                        error_msg = "%s failed sanity test (tmpdir) in path %s" % (file,root)
                        oe.qa.handle_error("pkgconfig", error_msg, d)

            if not skip_shebang_size:
                errors = {}
                package_qa_check_shebang_size(path, "", d, None, errors)
                for e in errors:
                    oe.qa.handle_error(e, errors[e], d)


# Run all package-wide warnfuncs and errorfuncs
def package_qa_package(warnfuncs, errorfuncs, package, d):
    warnings = {}
    errors = {}

    for func in warnfuncs:
        func(package, d, warnings)
    for func in errorfuncs:
        func(package, d, errors)

    for w in warnings:
        oe.qa.handle_error(w, warnings[w], d)
    for e in errors:
        oe.qa.handle_error(e, errors[e], d)

    return len(errors) == 0

# Run all recipe-wide warnfuncs and errorfuncs
def package_qa_recipe(warnfuncs, errorfuncs, pn, d):
    warnings = {}
    errors = {}

    for func in warnfuncs:
        func(pn, d, warnings)
    for func in errorfuncs:
        func(pn, d, errors)

    for w in warnings:
        oe.qa.handle_error(w, warnings[w], d)
    for e in errors:
        oe.qa.handle_error(e, errors[e], d)

    return len(errors) == 0

def prepopulate_objdump_p(elf, d):
    output = elf.run_objdump("-p", d)
    return (elf.name, output)

# Walk over all files in a directory and call func
def package_qa_walk(warnfuncs, errorfuncs, package, d):
    warnings = {}
    errors = {}
    elves = {}
    for path in pkgfiles[package]:
            elf = None
            if os.path.isfile(path):
                elf = oe.qa.ELFFile(path)
                try:
                    elf.open()
                    elf.close()
                except oe.qa.NotELFFileError:
                    elf = None
            if elf:
                elves[path] = elf

    results = oe.utils.multiprocess_launch(prepopulate_objdump_p, elves.values(), d, extraargs=(d,))
    for item in results:
        elves[item[0]].set_objdump("-p", item[1])

    for path in pkgfiles[package]:
            if path in elves:
                elves[path].open()
            for func in warnfuncs:
                func(path, package, d, elves.get(path), warnings)
            for func in errorfuncs:
                func(path, package, d, elves.get(path), errors)
            if path in elves:
                elves[path].close()

    for w in warnings:
        oe.qa.handle_error(w, warnings[w], d)
    for e in errors:
        oe.qa.handle_error(e, errors[e], d)

def package_qa_check_rdepends(pkg, pkgdest, skip, taskdeps, packages, d):
    # Don't do this check for kernel/module recipes, there aren't too many debug/development
    # packages and you can get false positives e.g. on kernel-module-lirc-dev
    if bb.data.inherits_class("kernel", d) or bb.data.inherits_class("module-base", d):
        return

    if not "-dbg" in pkg and not "packagegroup-" in pkg and not "-image" in pkg:
        localdata = bb.data.createCopy(d)
        localdata.setVar('OVERRIDES', localdata.getVar('OVERRIDES') + ':' + pkg)

        # Now check the RDEPENDS
        rdepends = bb.utils.explode_deps(localdata.getVar('RDEPENDS') or "")

        # Now do the sanity check!!!
        if "build-deps" not in skip:
            for rdepend in rdepends:
                if "-dbg" in rdepend and "debug-deps" not in skip:
                    error_msg = "%s rdepends on %s" % (pkg,rdepend)
                    oe.qa.handle_error("debug-deps", error_msg, d)
                if (not "-dev" in pkg and not "-staticdev" in pkg) and rdepend.endswith("-dev") and "dev-deps" not in skip:
                    error_msg = "%s rdepends on %s" % (pkg, rdepend)
                    oe.qa.handle_error("dev-deps", error_msg, d)
                if rdepend not in packages:
                    rdep_data = oe.packagedata.read_subpkgdata(rdepend, d)
                    if rdep_data and 'PN' in rdep_data and rdep_data['PN'] in taskdeps:
                        continue
                    if not rdep_data or not 'PN' in rdep_data:
                        for _, rdep_data in oe.packagedata.foreach_runtime_provider_pkgdata(d, rdepend):
                            if rdep_data and 'PN' in rdep_data and rdep_data['PN'] in taskdeps:
                                break
                    if rdep_data and 'PN' in rdep_data and rdep_data['PN'] in taskdeps:
                        continue
                    if rdep_data and 'PN' in rdep_data:
                        error_msg = "%s rdepends on %s, but it isn't a build dependency, missing %s in DEPENDS or PACKAGECONFIG?" % (pkg, rdepend, rdep_data['PN'])
                    else:
                        error_msg = "%s rdepends on %s, but it isn't a build dependency?" % (pkg, rdepend)
                    oe.qa.handle_error("build-deps", error_msg, d)

        if "file-rdeps" not in skip:
            ignored_file_rdeps = set(['/bin/sh', '/usr/bin/env', 'rtld(GNU_HASH)'])
            if bb.utils.contains('DISTRO_FEATURES', 'usrmerge', True, False, d):
                ignored_file_rdeps |= set(['/usr/bin/sh'])
            if bb.data.inherits_class('nativesdk', d):
                ignored_file_rdeps |= set(['/bin/bash', '/usr/bin/perl', 'perl'])
                if bb.utils.contains('DISTRO_FEATURES', 'usrmerge', True, False, d):
                    ignored_file_rdeps |= set(['/usr/bin/bash'])
            # For Saving the FILERDEPENDS
            filerdepends = {}
            rdep_data = oe.packagedata.read_subpkgdata(pkg, d)
            for key in rdep_data:
                if key.startswith("FILERDEPENDS:"):
                    for subkey in bb.utils.explode_deps(rdep_data[key]):
                        if subkey not in ignored_file_rdeps and \
                                not subkey.startswith('perl('):
                            # We already know it starts with FILERDEPENDS_
                            filerdepends[subkey] = key[13:]

            if filerdepends:
                done = rdepends[:]
                # Add the rprovides of itself
                if pkg not in done:
                    done.insert(0, pkg)

                # The python is not a package, but python-core provides it, so
                # skip checking /usr/bin/python if python is in the rdeps, in
                # case there is a RDEPENDS:pkg = "python" in the recipe.
                for py in [ d.getVar('MLPREFIX') + "python", "python" ]:
                    if py in done:
                        filerdepends.pop("/usr/bin/python",None)
                        done.remove(py)
                for rdep in done:
                    # The file dependencies may contain package names, e.g.,
                    # perl
                    filerdepends.pop(rdep,None)

                    for _, rdep_data in oe.packagedata.foreach_runtime_provider_pkgdata(d, rdep, True):
                        for key in rdep_data:
                            if key.startswith("FILERPROVIDES:") or key.startswith("RPROVIDES:"):
                                for subkey in bb.utils.explode_deps(rdep_data[key]):
                                    filerdepends.pop(subkey,None)
                            # Add the files list to the rprovides
                            if key.startswith("FILES_INFO:"):
                                # Use eval() to make it as a dict
                                for subkey in eval(rdep_data[key]):
                                    filerdepends.pop(subkey,None)

                    if not filerdepends:
                        # Break if all the file rdepends are met
                        break
            if filerdepends:
                for key in filerdepends:
                    error_msg = "%s contained in package %s requires %s, but no providers found in RDEPENDS:%s?" % \
                            (filerdepends[key].replace(":%s" % pkg, "").replace("@underscore@", "_"), pkg, key, pkg)
                    oe.qa.handle_error("file-rdeps", error_msg, d)
package_qa_check_rdepends[vardepsexclude] = "OVERRIDES"

def explode_libs(s):

    lib_list = s.split()

    def remove_parentheses(s):
        while '(' in s and ')' in s:
            start = s.find('(')
            end = s.find(')', start)
            if end == -1:
                break
            s = s[:start] + s[end+1:]
        return s
    
    return_list = [remove_parentheses(lib) for lib in lib_list]

    return return_list

def __recursively_add_dependent_packages(linked_package, linked_packages,d):

    shlibs_dir = d.getVar('SHLIBSDIRS')
    workdir_pkgdata_dir = d.getVar('WORKDIR_PKGDATA')
    runtime_dir = workdir_pkgdata_dir + '/runtime'

    #Check for file with the same package name in WORKDIR_PKGDATA/runtime
    package_file_path = os.path.join(runtime_dir, linked_package)
    
    #Open the corresponding package file
    if os.access(package_file_path, os.R_OK):
        with open(package_file_path, 'r') as package_file_fd:
            package_file_lines = package_file_fd.readlines()
    else:
        bb.error("Package file cannot be read: %s" % package_file_path)
    
    #Create depends_on_packages attribue to indicate which packages the linked_package is depending on
    linked_packages[linked_package]['depends_on_packages']= {}

    #Create list of license that the package must adhere to
    linked_packages[linked_package]['license'] = []
        
    for line in package_file_lines:
        #Add the license
        if 'LICENSE' == line.split(':')[0]:
            splitted_license_entry = line.split(':')
            
            #Check if the LICENSE contains 2 or 3 parts separated by ':'
            if len(splitted_license_entry) == 3:
                license_name = line.split(':')[2]

            elif len(splitted_license_entry) == 2:
            license_name = line.split(':')[1]

            else:
                bb.error("Undefined LICENSE entry format in package file: %s" % package_file_path)

            #Add the license name to the existing 'license' attribute
            linked_packages[linked_package]['license'].append(license_name.strip())
            
        #Add the depends attribute based on RDEPENDS of the package file
        if 'RDEPENDS' == line.split(':')[0]:
            #Get list of dependent packages
            rdepend_packages_raw = line.split(':')[2]
            rdepend_packages = bb.utils.explode_deps(rdepend_packages_raw)

            #With each package in the rdepend_packages, add it as an empty dictionary to the depends_on_packages attribute of linked_packages
            for rdepend_package in rdepend_packages:
                linked_packages[linked_package]['depends_on_packages'][rdepend_package] = {}
        
        #Add the corresponding shared libs in use
        if 'FILERDEPENDS' == line.split(':')[0]:
            #Check if 'depends_on_packages' is not empty, this means that there is at least one package under the dependency chain
            if linked_packages[linked_package]['depends_on_packages'] != {}:
                for linked_lib in linked_packages[linked_package]['linked_libs'].keys():

                    linked_lib_name = linked_lib.split('.')[0]
                    lib_file_of_current_package_which_depends_on_other_libs_from_other_dependent_packages = line.split(':')[1].replace('@underscore@', '_') #The character '_' is denoted as '@underscore@' in some package file

                    #Check if one of the linked libs of the linked_package is in the current FILERDEPENDS line which reveals a list of its dependency files
                    if linked_lib_name in lib_file_of_current_package_which_depends_on_other_libs_from_other_dependent_packages:
                        #Extract runtime depend libs as a list
                        rdepends_files_raw = line.split(':')[3]
                        rdepends_files_original = explode_libs(rdepends_files_raw)

                        #Remove duplication in the rdepends_files
                        rdepends_files = list(set(rdepends_files_original))

                        #Check which package in the RDEPENDS provides the rdepends_files
                        for rdepend_package in linked_packages[linked_package]['depends_on_packages'].keys():
                            list_file_path = os.path.join(shlibs_dir, rdepend_package + '.list')

                            linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'] = {}

                            #Open corresponding .list file in SHLIBSDIRS
                            if os.access(list_file_path, os.R_OK):
                                with open(list_file_path, 'r') as list_file_fd:
                                    list_file_log = list_file_fd.read()
                            else:
                                bb.error("List file cannot be read: %s" % list_file_path)

                            #Check if any rdepends_file is in the opened file
                            for rdepends_file in rdepends_files:
                                if rdepends_file in list_file_log:

                                    #Check for .so,.a extension of the linked libs to set the linking status accordingly
                                    if '.so' in rdepends_file:
                                        #Add the shared linked lib along with its linking status
                                        linked_lib = rdepends_file.split('.')[0] + '.so'
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][linked_lib] = {}
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][linked_lib]['linking_status'] = 'dynamic'

                                        #Add path to the linked_lib
                                        raw_lib_name = linked_lib.split('.')[0]
                                        found_libs = __get_matchhing_libs_in_recipe_sysroot_dir(raw_lib_name, d)
                                        lib_path = found_libs[linked_lib]
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][linked_lib]['path'] = lib_path

                                    elif rdepends_file.endswith('.a'):
                                        #Add the static linked lib along with its linking status
                                        linked_lib = rdepends_file
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][linked_lib] = {}
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][linked_lib]['linking_status'] = 'static'

                                        #Add path to the linked_lib
                                        raw_lib_name = linked_lib.split('.')[0]
                                        found_libs = __get_matchhing_libs_in_recipe_sysroot_dir(raw_lib_name, d)
                                        lib_path = found_libs[linked_lib]
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][linked_lib]['path'] = lib_path

                                    else:
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][rdepends_file] = {}
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][rdepends_file]['linking_status'] = 'unknown'
                                        linked_packages[linked_package]['depends_on_packages'][rdepend_package]['linked_libs'][rdepends_file]['path'] = ''

                                else:
                                    #Do nothing, the rdepends_file is not provided by the package
                                    pass
                    else:
                        #Do nothing
                        pass
                
                #Go down the dependency chain in depends_on_packages
                for rdepend_package in linked_packages[linked_package]['depends_on_packages'].keys():
                    __recursively_add_dependent_packages(linked_package=rdepend_package, linked_packages=linked_packages[linked_package]['depends_on_packages'], d=d)
                
            else:
                #Do nothing, this is the end package in the dependency chain. This also the base condition for the recursion to stop
                pass

def __get_packages_provide_the_linked_libs(linked_libs, d):
    #Check for the package which provides the lib with .list files in SHLIBSDIRS
    shlibs_dir = d.getVar('SHLIBSDIRS')
    list_files = os.listdir(shlibs_dir)

    linked_packages = {}

    #Loop through each file in shlibs_dir
    for list_file in list_files:

        isPackageLinked = False

        detected_linked_libs = {}

        #Get path of the list file
        list_file_path = os.path.join(shlibs_dir, list_file)

        #Get the package name without .list extension
        package_name = list_file.split('.')[0]

        #Open the corresponding .list file
        if os.access(list_file_path, os.R_OK):
            with open(list_file_path, 'r') as list_file_fd:
                list_file_lines = list_file_fd.readlines()
        else:
            bb.error("Log file cannot be read: %s" % log_path)

        
        #Check if any linked lib is in the opened file
        for line in list_file_lines:
            #Extract info from line for ease of processing
            splitted_line = line.split(':')
            shared_lib_name = splitted_line[0]
            shared_lib_path = splitted_line[1]
            shared_lib_version = splitted_line[2]

            #Check if any linked lib matches the shared lib name
            for linked_lib in linked_libs.items():
                linked_lib_name = linked_lib[0]
                linked_lib_attributes = linked_lib[1]

                if linked_lib_name in shared_lib_name:
                    #Add the lib to detected linked libs
                    detected_linked_libs[linked_lib_name] = linked_lib_attributes

                    #Set flag that this package does provide the linked lib
                    isPackageLinked = True

                else:
                    #Do nothing
                    pass
        
        if isPackageLinked:
            package_attributes = {
                "linked_libs": detected_linked_libs,
                "list_file": list_file,
                "list_file_path": list_file_path
            }

            #Add the attributes to the linked packages
            linked_packages[package_name] = package_attributes
        else:
            #Do nothing
            pass
    
    #With each package in the linked packages, recursively add the dependent packages and their libs
    for linked_package in linked_packages.keys():
        __recursively_add_dependent_packages(linked_package=linked_package, linked_packages=linked_packages, d=d)

    return linked_packages

def is_static_linking_flag_found(d):
    import re

    is_static_flag_found = False

    recipe_log_dir = d.getVar('T')
    log_path = os.path.join(recipe_log_dir, 'log.do_compile')

    #Read log file from T/log.do_compile into a list of lines
    if os.access(log_path, os.R_OK):
        with open(log_path, 'r') as log_fd:
            log_content = log_fd.read()
    else:
        bb.error("Log file cannot be read: %s" % log_path)
    
    #TODO: This is compiler and linker specific, might need to be updated these flags accordingly in the future
    #Apply regex to check for -static linking flag 
    static_flag_checker = re.compile(r"\s-static\s")

    is_static_flag_found = bool(static_flag_checker.search(log_content))
    
    return is_static_flag_found

def __get_matchhing_libs_in_recipe_sysroot_dir(raw_lib_name, d):
    import re

    #Get the RECIPE_SYSROOT directory path
    recipe_sysroot_dir = d.getVar('RECIPE_SYSROOT')

    #Get all subdirectories in RECIPE_SYSROOT
    sysroot_search_dirs = [sub_dir[0] for sub_dir in os.walk(recipe_sysroot_dir)]

    #To be selected, the lib must match the pattern <lib_name>.so or <lib_name>.a
    lib_matching_pattern = re.compile(r"\b%s\.(so|a)$" % raw_lib_name)

    matched_lib_files = {}

    for sysroot_search_dir in sysroot_search_dirs:

        #Get the list of all lib files in the directory being searched
        lib_files = os.listdir(sysroot_search_dir)

        #Filter out matched lib files and add them to the matched_lib_files
        for lib_file in lib_files:

            #Check for lib files that ends in .so or .a
            if lib_matching_pattern.fullmatch(lib_file):
                #Add the file to the matched_lib_files, along with its path
                matched_lib_files[lib_file] = os.path.join(sysroot_search_dir, lib_file)

            else:
                #Do nothing
                pass

    return matched_lib_files

def __get_linked_libs_name(d):
    import re
    
    linked_lib_names = []
    recipe_log_dir = d.getVar('T')
    log_path = os.path.join(recipe_log_dir, 'log.do_compile')

    #Read log file from T/log.do_compile into a list of lines
    if os.access(log_path, os.R_OK):
        with open(log_path, 'r') as log_fd:
            log_content = log_fd.read()
    else:
        bb.error("Log file cannot be read: %s" % log_path)

    #Apply regex to extract the raw linked libs
    parser = re.compile(r"\s-l\w+\b")
    raw_libs_with_linker_flag = parser.findall(log_content)
    unflagged_raw_libs = [raw_lib[3:] for raw_lib in raw_libs_with_linker_flag]

    #Prepend 'lib' to the linked libs
    linked_lib_names = ['lib' + unflagged_lib for unflagged_lib in unflagged_raw_libs]

    return linked_lib_names

def __check_type_of_files_generated(pkgfiles, d):
    is_executables_generated = False
    is_shared_libs_generated = False
    is_static_libs_generated = False

    pn = d.getVar('PN')
    pkgdest = d.getVar('PKGDEST')

    for package in pkgfiles:
        #If the package is not emtpy
        if pkgfiles[package] != []:
            #Get the file path of each file in the package
            for file_path in pkgfiles[package]:
                #Extract directory path of the file
                file_name = os.path.basename(file_path)
                file_dir = os.path.dirname(file_path)

                #If the directory path match PKGDEST/PN/usr/bin
                if file_dir == pkgdest + '/' + pn + '/usr/bin':
                    #Set the is_executables_generated to True
                    is_executables_generated = True

                #Else if the directory path match PKGDEST/PN-dev/usr/lib/
                elif file_dir == pkgdest + '/' + pn + '-dev/usr/lib':
                    #Set the is_shared_libs_generated to True
                    is_shared_libs_generated = True

                #Else if the directory path match PKGDEST/PN-staticdev/usr/lib/
                elif file_dir == pkgdest + '/' + pn + '-staticdev/usr/lib':
                    #Set the is_static_libs_generated to True
                    is_static_libs_generated = True
    
    return is_executables_generated, is_shared_libs_generated, is_static_libs_generated

def package_qa_check_license_compliance(packages, pkgfiles, d):
    
    # bb.warn("package_qa_check_license_compliance is called here in foss license check")

    #Initialize local attributes
    m_packages = packages
    m_pkgfiles = pkgfiles
    m_datastore = d

    m_linked_packages = None

    #Check if a recipe whether generates executables, shared libs, static libs or all
    (is_executables_generated, is_shared_libs_generated, is_static_libs_generated ) = __check_type_of_files_generated(m_pkgfiles, m_datastore)

    #If the package generates executables in PKGDEST/PN/usr/bin/
    if is_executables_generated:
        #Extract the linked libs from the latest compile log
        raw_linked_lib_names = __get_linked_libs_name(m_datastore)

        #A list of linked libs with their attributes for ease of futher processing
        linked_libs = {}

        #A list of packages which provides the linked libs along with other useful attributes
        linked_packages = {}

        #With each name in the raw linked libs
        for raw_linked_lib_name in raw_linked_lib_names:
            #Check for the matching lib files in RECIPE_SYSROOT/usr/lib
            matched_lib_files = __get_matchhing_libs_in_recipe_sysroot_dir(raw_lib_name=raw_linked_lib_name, d=m_datastore)

            #If there are more than one lib file matching the same name of a linked lib
            if len(matched_lib_files) == 2:
                #Extract the each lib in the matched lib files
                for matched_lib_file in matched_lib_files.items():
                    if matched_lib_file[0].endswith('.so'):
                        matched_shared_lib_file = matched_lib_file
                    elif matched_lib_file[0].endswith('.a'):
                        matched_static_lib_file = matched_lib_file
                

                #Check if compile log has pattern flag -static or .so is not a symbolic link
                if is_static_linking_flag_found(d=m_datastore): #TODO: Be careful of libc.so since it is a ld script to link both static and dynamic libs, might need to have a unique check for this later
                    static_lib_file = matched_static_lib_file[0]
                    static_lib_file_path = matched_static_lib_file[1]

                    #Set linking attribute of the lib to static
                    lib_attributes = {
                        "path": static_lib_file_path,
                        "linking": "static"
                    }

                    #Add the .a lib into linked libs
                    linked_libs[static_lib_file] = lib_attributes
                    
                
                else:
                    shared_lib_file = matched_shared_lib_file[0]
                    shared_lib_file_path = matched_shared_lib_file[1]

                    #Set linking attribute of the lib to dynamic
                    lib_attributes = {
                        "path": shared_lib_file_path,
                        "linking": "dynamic"
                    }

                    #Add the .so lib into linked libs
                    linked_libs[shared_lib_file] = lib_attributes

            elif len(matched_lib_files) == 1:
                #TODO: It is a little bit awkward to use a loop here since there is only one element in the dictionary, may find more elegant way to do this
                for matched_lib_file in matched_lib_files.items():
                    lib_name = matched_lib_file[0]
                    lib_path = matched_lib_file[1]

                #Set linking attribute to dynamic/static according ending .so/.a of the recently added lib
                if lib_name.endswith('.so'):
                    linking_status = "dynamic"
                elif lib_name.endswith('.a'):
                    linking_status = "static"
                else:
                    #Signal error
                    bb.error("Currently this tool is just working for Linux, other libs from different OS platforms are not supported yet")
                
                #Add the lib .so/.a found into linked libs
                lib_attributes = {
                        "path": lib_path,
                        "linking": linking_status
                }
                linked_libs[lib_name] = lib_attributes
            else:
                #Signal error, there must not be 3 libs matching the same name
                bb.error("There are more than 2 lib files matching the %s " % raw_linked_lib_name)
        

        #Get a list of packages which provides the linked libs
        m_linked_packages = __get_packages_provide_the_linked_libs(linked_libs=linked_libs, d=m_datastore) #TODO: Please be noted, this method is currently can only work with packages which provide shared libs .so files
        
        #Apply the FOSS license check algorithm on the depend package list

    #If the package generates .so libraries in PKGDEST/PN-dev/usr/lib/
    if is_shared_libs_generated:
        pass
        #TODO: TBD later

    #If the package generates .a libraries in PKGDEST/PN-staticdev/usr/lib/
    if is_static_libs_generated:
        pass
        #TODO: TBD later
        

def package_qa_check_deps(pkg, pkgdest, d):

    localdata = bb.data.createCopy(d)
    localdata.setVar('OVERRIDES', pkg)

    def check_valid_deps(var):
        try:
            rvar = bb.utils.explode_dep_versions2(localdata.getVar(var) or "")
        except ValueError as e:
            bb.fatal("%s:%s: %s" % (var, pkg, e))
        for dep in rvar:
            for v in rvar[dep]:
                if v and not v.startswith(('< ', '= ', '> ', '<= ', '>=')):
                    error_msg = "%s:%s is invalid: %s (%s)   only comparisons <, =, >, <=, and >= are allowed" % (var, pkg, dep, v)
                    oe.qa.handle_error("dep-cmp", error_msg, d)

    check_valid_deps('RDEPENDS')
    check_valid_deps('RRECOMMENDS')
    check_valid_deps('RSUGGESTS')
    check_valid_deps('RPROVIDES')
    check_valid_deps('RREPLACES')
    check_valid_deps('RCONFLICTS')

QAPKGTEST[usrmerge] = "package_qa_check_usrmerge"
def package_qa_check_usrmerge(pkg, d, messages):

    pkgdest = d.getVar('PKGDEST')
    pkg_dir = pkgdest + os.sep + pkg + os.sep
    merged_dirs = ['bin', 'sbin', 'lib'] + d.getVar('MULTILIB_VARIANTS').split()
    for f in merged_dirs:
        if os.path.exists(pkg_dir + f) and not os.path.islink(pkg_dir + f):
            msg = "%s package is not obeying usrmerge distro feature. /%s should be relocated to /usr." % (pkg, f)
            oe.qa.add_message(messages, "usrmerge", msg)
            return False
    return True

QAPKGTEST[perllocalpod] = "package_qa_check_perllocalpod"
def package_qa_check_perllocalpod(pkg, d, messages):
    """
    Check that the recipe didn't ship a perlocal.pod file, which shouldn't be
    installed in a distribution package.  cpan.bbclass sets NO_PERLLOCAL=1 to
    handle this for most recipes.
    """
    import glob
    pkgd = oe.path.join(d.getVar('PKGDEST'), pkg)
    podpath = oe.path.join(pkgd, d.getVar("libdir"), "perl*", "*", "*", "perllocal.pod")

    matches = glob.glob(podpath)
    if matches:
        matches = [package_qa_clean_path(path, d, pkg) for path in matches]
        msg = "%s contains perllocal.pod (%s), should not be installed" % (pkg, " ".join(matches))
        oe.qa.add_message(messages, "perllocalpod", msg)

QAPKGTEST[expanded-d] = "package_qa_check_expanded_d"
def package_qa_check_expanded_d(package, d, messages):
    """
    Check for the expanded D (${D}) value in pkg_* and FILES
    variables, warn the user to use it correctly.
    """
    sane = True
    expanded_d = d.getVar('D')

    for var in 'FILES','pkg_preinst', 'pkg_postinst', 'pkg_prerm', 'pkg_postrm':
        bbvar = d.getVar(var + ":" + package) or ""
        if expanded_d in bbvar:
            if var == 'FILES':
                oe.qa.add_message(messages, "expanded-d", "FILES in %s recipe should not contain the ${D} variable as it references the local build directory not the target filesystem, best solution is to remove the ${D} reference" % package)
                sane = False
            else:
                oe.qa.add_message(messages, "expanded-d", "%s in %s recipe contains ${D}, it should be replaced by $D instead" % (var, package))
                sane = False
    return sane

QAPKGTEST[unlisted-pkg-lics] = "package_qa_check_unlisted_pkg_lics"
def package_qa_check_unlisted_pkg_lics(package, d, messages):
    """
    Check that all licenses for a package are among the licenses for the recipe.
    """
    pkg_lics = d.getVar('LICENSE:' + package)
    if not pkg_lics:
        return True

    recipe_lics_set = oe.license.list_licenses(d.getVar('LICENSE'))
    package_lics = oe.license.list_licenses(pkg_lics)
    unlisted = package_lics - recipe_lics_set
    if unlisted:
        oe.qa.add_message(messages, "unlisted-pkg-lics",
                               "LICENSE:%s includes licenses (%s) that are not "
                               "listed in LICENSE" % (package, ' '.join(unlisted)))
        return False
    obsolete = set(oe.license.obsolete_license_list()) & package_lics - recipe_lics_set
    if obsolete:
        oe.qa.add_message(messages, "obsolete-license",
                               "LICENSE:%s includes obsolete licenses %s" % (package, ' '.join(obsolete)))
        return False
    return True

QAPKGTEST[empty-dirs] = "package_qa_check_empty_dirs"
def package_qa_check_empty_dirs(pkg, d, messages):
    """
    Check for the existence of files in directories that are expected to be
    empty.
    """

    pkgd = oe.path.join(d.getVar('PKGDEST'), pkg)
    for dir in (d.getVar('QA_EMPTY_DIRS') or "").split():
        empty_dir = oe.path.join(pkgd, dir)
        if os.path.exists(empty_dir) and os.listdir(empty_dir):
            recommendation = (d.getVar('QA_EMPTY_DIRS_RECOMMENDATION:' + dir) or
                              "but it is expected to be empty")
            msg = "%s installs files in %s, %s" % (pkg, dir, recommendation)
            oe.qa.add_message(messages, "empty-dirs", msg)

def package_qa_check_encoding(keys, encode, d):
    def check_encoding(key, enc):
        sane = True
        value = d.getVar(key)
        if value:
            try:
                s = value.encode(enc)
            except UnicodeDecodeError as e:
                error_msg = "%s has non %s characters" % (key,enc)
                sane = False
                oe.qa.handle_error("invalid-chars", error_msg, d)
        return sane

    for key in keys:
        sane = check_encoding(key, encode)
        if not sane:
            break

HOST_USER_UID := "${@os.getuid()}"
HOST_USER_GID := "${@os.getgid()}"

QAPATHTEST[host-user-contaminated] = "package_qa_check_host_user"
def package_qa_check_host_user(path, name, d, elf, messages):
    """Check for paths outside of /home which are owned by the user running bitbake."""

    if not os.path.lexists(path):
        return

    dest = d.getVar('PKGDEST')
    pn = d.getVar('PN')
    home = os.path.join(dest, name, 'home')
    if path == home or path.startswith(home + os.sep):
        return

    try:
        stat = os.lstat(path)
    except OSError as exc:
        import errno
        if exc.errno != errno.ENOENT:
            raise
    else:
        check_uid = int(d.getVar('HOST_USER_UID'))
        if stat.st_uid == check_uid:
            oe.qa.add_message(messages, "host-user-contaminated", "%s: %s is owned by uid %d, which is the same as the user running bitbake. This may be due to host contamination" % (pn, package_qa_clean_path(path, d, name), check_uid))
            return False

        check_gid = int(d.getVar('HOST_USER_GID'))
        if stat.st_gid == check_gid:
            oe.qa.add_message(messages, "host-user-contaminated", "%s: %s is owned by gid %d, which is the same as the user running bitbake. This may be due to host contamination" % (pn, package_qa_clean_path(path, d, name), check_gid))
            return False
    return True

QARECIPETEST[unhandled-features-check] = "package_qa_check_unhandled_features_check"
def package_qa_check_unhandled_features_check(pn, d, messages):
    if not bb.data.inherits_class('features_check', d):
        var_set = False
        for kind in ['DISTRO', 'MACHINE', 'COMBINED']:
            for var in ['ANY_OF_' + kind + '_FEATURES', 'REQUIRED_' + kind + '_FEATURES', 'CONFLICT_' + kind + '_FEATURES']:
                if d.getVar(var) is not None or d.hasOverrides(var):
                    var_set = True
        if var_set:
            oe.qa.handle_error("unhandled-features-check", "%s: recipe doesn't inherit features_check" % pn, d)

QARECIPETEST[missing-update-alternatives] = "package_qa_check_missing_update_alternatives"
def package_qa_check_missing_update_alternatives(pn, d, messages):
    # Look at all packages and find out if any of those sets ALTERNATIVE variable
    # without inheriting update-alternatives class
    for pkg in (d.getVar('PACKAGES') or '').split():
        if d.getVar('ALTERNATIVE:%s' % pkg) and not bb.data.inherits_class('update-alternatives', d):
            oe.qa.handle_error("missing-update-alternatives", "%s: recipe defines ALTERNATIVE:%s but doesn't inherit update-alternatives. This might fail during do_rootfs later!" % (pn, pkg), d)

# The PACKAGE FUNC to scan each package
python do_package_qa () {
    import subprocess
    import oe.packagedata
    
    bb.note("DO PACKAGE QA")

    main_lic = d.getVar('LICENSE')

    # Check for obsolete license references in main LICENSE (packages are checked below for any changes)
    main_licenses = oe.license.list_licenses(d.getVar('LICENSE'))
    obsolete = set(oe.license.obsolete_license_list()) & main_licenses
    if obsolete:
        oe.qa.handle_error("obsolete-license", "Recipe LICENSE includes obsolete licenses %s" % ' '.join(obsolete), d)

    bb.build.exec_func("read_subpackage_metadata", d)

    # Check non UTF-8 characters on recipe's metadata
    package_qa_check_encoding(['DESCRIPTION', 'SUMMARY', 'LICENSE', 'SECTION'], 'utf-8', d)

    logdir = d.getVar('T')
    pn = d.getVar('PN')

    # Scan the packages...
    pkgdest = d.getVar('PKGDEST')
    packages = set((d.getVar('PACKAGES') or '').split())

    global pkgfiles
    pkgfiles = {}
    for pkg in packages:
        pkgfiles[pkg] = []
        pkgdir = os.path.join(pkgdest, pkg)
        for walkroot, dirs, files in os.walk(pkgdir):
            # Don't walk into top-level CONTROL or DEBIAN directories as these
            # are temporary directories created by do_package.
            if walkroot == pkgdir:
                for control in ("CONTROL", "DEBIAN"):
                    if control in dirs:
                        dirs.remove(control)
            for file in files:
                pkgfiles[pkg].append(os.path.join(walkroot, file))

    # no packages should be scanned
    if not packages:
        return

    import re
    # The package name matches the [a-z0-9.+-]+ regular expression
    pkgname_pattern = re.compile(r"^[a-z0-9.+-]+$")

    taskdepdata = d.getVar("BB_TASKDEPDATA", False)
    taskdeps = set()
    for dep in taskdepdata:
        taskdeps.add(taskdepdata[dep][0])

    def parse_test_matrix(matrix_name):
        testmatrix = d.getVarFlags(matrix_name) or {}
        g = globals()
        warnchecks = []
        for w in (d.getVar("WARN_QA") or "").split():
            if w in skip:
               continue
            if w in testmatrix and testmatrix[w] in g:
                warnchecks.append(g[testmatrix[w]])

        errorchecks = []
        for e in (d.getVar("ERROR_QA") or "").split():
            if e in skip:
               continue
            if e in testmatrix and testmatrix[e] in g:
                errorchecks.append(g[testmatrix[e]])
        return warnchecks, errorchecks

    for package in packages:
        skip = set((d.getVar('INSANE_SKIP') or "").split() +
                   (d.getVar('INSANE_SKIP:' + package) or "").split())
        if skip:
            bb.note("Package %s skipping QA tests: %s" % (package, str(skip)))

        bb.note("Checking Package: %s" % package)
        # Check package name
        if not pkgname_pattern.match(package):
            oe.qa.handle_error("pkgname",
                    "%s doesn't match the [a-z0-9.+-]+ regex" % package, d)

        warn_checks, error_checks = parse_test_matrix("QAPATHTEST")
        package_qa_walk(warn_checks, error_checks, package, d)

        warn_checks, error_checks = parse_test_matrix("QAPKGTEST")
        package_qa_package(warn_checks, error_checks, package, d)

        package_qa_check_rdepends(package, pkgdest, skip, taskdeps, packages, d)
        package_qa_check_deps(package, pkgdest, d)

    warn_checks, error_checks = parse_test_matrix("QARECIPETEST")
    package_qa_recipe(warn_checks, error_checks, pn, d)

    if 'libdir' in d.getVar("ALL_QA").split():
        package_qa_check_libdir(d)
    
    package_qa_check_license_compliance(packages=packages, pkgfiles=pkgfiles, d=d)

    oe.qa.exit_if_errors(d)
}

# binutils is used for most checks, so need to set as dependency
# POPULATESYSROOTDEPS is defined in staging class.
do_package_qa[depends] += "${POPULATESYSROOTDEPS}"
do_package_qa[vardeps] = "${@bb.utils.contains('ERROR_QA', 'empty-dirs', 'QA_EMPTY_DIRS', '', d)}"
do_package_qa[vardepsexclude] = "BB_TASKDEPDATA"
do_package_qa[rdeptask] = "do_packagedata"
addtask do_package_qa after do_packagedata do_package before do_build

# Add the package specific INSANE_SKIPs to the sstate dependencies
python() {
    pkgs = (d.getVar('PACKAGES') or '').split()
    for pkg in pkgs:
        d.appendVarFlag("do_package_qa", "vardeps", " INSANE_SKIP:{}".format(pkg))
}

SSTATETASKS += "do_package_qa"
do_package_qa[sstate-inputdirs] = ""
do_package_qa[sstate-outputdirs] = ""
python do_package_qa_setscene () {
    sstate_setscene(d)
}
addtask do_package_qa_setscene

python do_qa_sysroot() {
    bb.note("QA checking do_populate_sysroot")
    sysroot_destdir = d.expand('${SYSROOT_DESTDIR}')
    for sysroot_dir in d.expand('${SYSROOT_DIRS}').split():
        qa_check_staged(sysroot_destdir + sysroot_dir, d)
    oe.qa.exit_with_message_if_errors("do_populate_sysroot for this recipe installed files with QA issues", d)
}
do_populate_sysroot[postfuncs] += "do_qa_sysroot"

python do_qa_patch() {
    import subprocess

    ###########################################################################
    # Check patch.log for fuzz warnings
    #
    # Further information on why we check for patch fuzz warnings:
    # http://lists.openembedded.org/pipermail/openembedded-core/2018-March/148675.html
    # https://bugzilla.yoctoproject.org/show_bug.cgi?id=10450
    ###########################################################################

    logdir = d.getVar('T')
    patchlog = os.path.join(logdir,"log.do_patch")

    if os.path.exists(patchlog):
        fuzzheader = '--- Patch fuzz start ---'
        fuzzfooter = '--- Patch fuzz end ---'
        statement = "grep -e '%s' %s > /dev/null" % (fuzzheader, patchlog)
        if subprocess.call(statement, shell=True) == 0:
            msg = "Fuzz detected:\n\n"
            fuzzmsg = ""
            inFuzzInfo = False
            f = open(patchlog, "r")
            for line in f:
                if fuzzheader in line:
                    inFuzzInfo = True
                    fuzzmsg = ""
                elif fuzzfooter in line:
                    fuzzmsg = fuzzmsg.replace('\n\n', '\n')
                    msg += fuzzmsg
                    msg += "\n"
                    inFuzzInfo = False
                elif inFuzzInfo and not 'Now at patch' in line:
                    fuzzmsg += line
            f.close()
            msg += "The context lines in the patches can be updated with devtool:\n"
            msg += "\n"
            msg += "    devtool modify %s\n" % d.getVar('PN')
            msg += "    devtool finish --force-patch-refresh %s <layer_path>\n\n" % d.getVar('PN')
            msg += "Don't forget to review changes done by devtool!\n"
            msg += "\nPatch log indicates that patches do not apply cleanly."
            oe.qa.handle_error("patch-fuzz", msg, d)

    # Check if the patch contains a correctly formatted and spelled Upstream-Status
    import re
    from oe import patch

    for url in patch.src_patches(d):
        (_, _, fullpath, _, _, _) = bb.fetch.decodeurl(url)

        msg = oe.qa.check_upstream_status(fullpath)
        if msg:
            oe.qa.handle_error("patch-status", msg, d)

    ###########################################################################
    # Check for missing ptests
    ###########################################################################
    def match_line_in_files(toplevel, filename_glob, line_regex):
        import pathlib
        try:
            toppath = pathlib.Path(toplevel)
            for entry in toppath.glob(filename_glob):
                try:
                    with open(entry, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f.readlines():
                            if re.match(line_regex, line):
                                return True
                except FileNotFoundError:
                    # Broken symlink in source
                    pass
        except FileNotFoundError:
            # pathlib.Path.glob() might throw this when file/directory
            # disappear while scanning.
            bb.note("unimplemented-ptest: FileNotFoundError exception while scanning (disappearing file while scanning?). Check was ignored." % d.getVar('PN'))
            pass
        return False

    srcdir = d.getVar('S')
    if not bb.utils.contains('DISTRO_FEATURES', 'ptest', True, False, d):
        pass
    elif bb.data.inherits_class('ptest', d):
        bb.note("Package %s QA: skipping unimplemented-ptest: ptest implementation detected" % d.getVar('PN'))
    elif srcdir == d.getVar('WORKDIR'):
        bb.note("Package %s QA: skipping unimplemented-ptest: This check is not supported for recipe with \"S = \"${WORKDIR}\"" % d.getVar('PN'))

    # Detect perl Test:: based tests
    elif os.path.exists(os.path.join(srcdir, "t")) and any(filename.endswith('.t') for filename in os.listdir(os.path.join(srcdir, 't'))):
        oe.qa.handle_error("unimplemented-ptest", "%s: perl Test:: based tests detected" % d.getVar('PN'), d)

    # Detect pytest-based tests
    elif match_line_in_files(srcdir, "**/*.py", r'\s*(?:import\s*pytest|from\s*pytest)'):
        oe.qa.handle_error("unimplemented-ptest", "%s: pytest-based tests detected" % d.getVar('PN'), d)

    # Detect meson-based tests
    elif os.path.exists(os.path.join(srcdir, "meson.build")) and match_line_in_files(srcdir, "**/meson.build", r'\s*test\s*\('):
        oe.qa.handle_error("unimplemented-ptest", "%s: meson-based tests detected" % d.getVar('PN'), d)

    # Detect cmake-based tests
    elif os.path.exists(os.path.join(srcdir, "CMakeLists.txt")) and match_line_in_files(srcdir, "**/CMakeLists.txt", r'\s*(?:add_test|enable_testing)\s*\('):
        oe.qa.handle_error("unimplemented-ptest", "%s: cmake-based tests detected" % d.getVar('PN'), d)

    # Detect autotools-based·tests
    elif os.path.exists(os.path.join(srcdir, "Makefile.in")) and (match_line_in_files(srcdir, "**/Makefile.in", r'\s*TESTS\s*\+?=') or match_line_in_files(srcdir,"**/*.at",r'.*AT_INIT')):
        oe.qa.handle_error("unimplemented-ptest", "%s: autotools-based tests detected" % d.getVar('PN'), d)

    # Last resort, detect a test directory in sources
    elif any(filename.lower() in ["test", "tests"] for filename in os.listdir(srcdir)):
        oe.qa.handle_error("unimplemented-ptest", "%s: test subdirectory detected" % d.getVar('PN'), d)

    oe.qa.exit_if_errors(d)
}

python do_qa_configure() {
    import subprocess

    ###########################################################################
    # Check config.log for cross compile issues
    ###########################################################################

    configs = []
    workdir = d.getVar('WORKDIR')

    skip = (d.getVar('INSANE_SKIP') or "").split()
    skip_configure_unsafe = False
    if 'configure-unsafe' in skip:
        bb.note("Recipe %s skipping qa checking: configure-unsafe" % d.getVar('PN'))
        skip_configure_unsafe = True

    if bb.data.inherits_class('autotools', d) and not skip_configure_unsafe:
        bb.note("Checking autotools environment for common misconfiguration")
        for root, dirs, files in os.walk(workdir):
            statement = "grep -q -F -e 'is unsafe for cross-compilation' %s" % \
                        os.path.join(root,"config.log")
            if "config.log" in files:
                if subprocess.call(statement, shell=True) == 0:
                    error_msg = """This autoconf log indicates errors, it looked at host include and/or library paths while determining system capabilities.
Rerun configure task after fixing this."""
                    oe.qa.handle_error("configure-unsafe", error_msg, d)

            if "configure.ac" in files:
                configs.append(os.path.join(root,"configure.ac"))
            if "configure.in" in files:
                configs.append(os.path.join(root, "configure.in"))

    ###########################################################################
    # Check gettext configuration and dependencies are correct
    ###########################################################################

    skip_configure_gettext = False
    if 'configure-gettext' in skip:
        bb.note("Recipe %s skipping qa checking: configure-gettext" % d.getVar('PN'))
        skip_configure_gettext = True

    cnf = d.getVar('EXTRA_OECONF') or ""
    if not ("gettext" in d.getVar('P') or "gcc-runtime" in d.getVar('P') or \
            "--disable-nls" in cnf or skip_configure_gettext):
        ml = d.getVar("MLPREFIX") or ""
        if bb.data.inherits_class('cross-canadian', d):
            gt = "nativesdk-gettext"
        else:
            gt = "gettext-native"
        deps = bb.utils.explode_deps(d.getVar('DEPENDS') or "")
        if gt not in deps:
            for config in configs:
                gnu = "grep \"^[[:space:]]*AM_GNU_GETTEXT\" %s >/dev/null" % config
                if subprocess.call(gnu, shell=True) == 0:
                    error_msg = "AM_GNU_GETTEXT used but no inherit gettext"
                    oe.qa.handle_error("configure-gettext", error_msg, d)

    ###########################################################################
    # Check unrecognised configure options (with a white list)
    ###########################################################################
    if bb.data.inherits_class("autotools", d):
        bb.note("Checking configure output for unrecognised options")
        try:
            if bb.data.inherits_class("autotools", d):
                flag = "WARNING: unrecognized options:"
                log = os.path.join(d.getVar('B'), 'config.log')
            output = subprocess.check_output(['grep', '-F', flag, log]).decode("utf-8").replace(', ', ' ').replace('"', '')
            options = set()
            for line in output.splitlines():
                options |= set(line.partition(flag)[2].split())
            ignore_opts = set(d.getVar("UNKNOWN_CONFIGURE_OPT_IGNORE").split())
            options -= ignore_opts
            if options:
                pn = d.getVar('PN')
                error_msg = pn + ": configure was passed unrecognised options: " + " ".join(options)
                oe.qa.handle_error("unknown-configure-option", error_msg, d)
        except subprocess.CalledProcessError:
            pass

    # Check invalid PACKAGECONFIG
    pkgconfig = (d.getVar("PACKAGECONFIG") or "").split()
    if pkgconfig:
        pkgconfigflags = d.getVarFlags("PACKAGECONFIG") or {}
        for pconfig in pkgconfig:
            if pconfig not in pkgconfigflags:
                pn = d.getVar('PN')
                error_msg = "%s: invalid PACKAGECONFIG: %s" % (pn, pconfig)
                oe.qa.handle_error("invalid-packageconfig", error_msg, d)

    oe.qa.exit_if_errors(d)
}

python do_qa_unpack() {
    src_uri = d.getVar('SRC_URI')
    s_dir = d.getVar('S')
    if src_uri and not os.path.exists(s_dir):
        bb.warn('%s: the directory %s (%s) pointed to by the S variable doesn\'t exist - please set S within the recipe to point to where the source has been unpacked to' % (d.getVar('PN'), d.getVar('S', False), s_dir))
}

python do_recipe_qa() {
    import re

    def test_missing_metadata(pn, d):
        fn = d.getVar("FILE")
        srcfile = d.getVar('SRC_URI').split()
        # Check that SUMMARY is not the same as the default from bitbake.conf
        if d.getVar('SUMMARY') == d.expand("${PN} version ${PV}-${PR}"):
            oe.qa.handle_error("missing-metadata", "Recipe {} in {} does not contain a SUMMARY. Please add an entry.".format(pn, fn), d)
        if not d.getVar('HOMEPAGE'):
            if srcfile and srcfile[0].startswith('file') or not d.getVar('SRC_URI'):
                # We are only interested in recipes SRC_URI fetched from external sources
                pass
            else:
                oe.qa.handle_error("missing-metadata", "Recipe {} in {} does not contain a HOMEPAGE. Please add an entry.".format(pn, fn), d)

    def test_missing_maintainer(pn, d):
        fn = d.getVar("FILE")
        if pn.endswith("-native") or pn.startswith("nativesdk-") or "packagegroup-" in pn or "core-image-ptest-" in pn:
            return
        if not d.getVar('RECIPE_MAINTAINER'):
            oe.qa.handle_error("missing-maintainer", "Recipe {} in {} does not have an assigned maintainer. Please add an entry into meta/conf/distro/include/maintainers.inc.".format(pn, fn), d)

    def test_srcuri(pn, d):
        skip = (d.getVar('INSANE_SKIP') or "").split()
        if 'src-uri-bad' in skip:
            bb.note("Recipe %s skipping qa checking: src-uri-bad" % pn)
            return

        if "${PN}" in d.getVar("SRC_URI", False):
            oe.qa.handle_error("src-uri-bad", "%s: SRC_URI uses PN not BPN" % pn, d)

        for url in d.getVar("SRC_URI").split():
            # Search for github and gitlab URLs that pull unstable archives (comment for future greppers)
            if re.search(r"git(hu|la)b\.com/.+/.+/archive/.+", url) or "//codeload.github.com/" in url:
                oe.qa.handle_error("src-uri-bad", "%s: SRC_URI uses unstable GitHub/GitLab archives, convert recipe to use git protocol" % pn, d)

    pn = d.getVar('PN')
    test_missing_metadata(pn, d)
    test_missing_maintainer(pn, d)
    test_srcuri(pn, d)
    oe.qa.exit_if_errors(d)
}

addtask do_recipe_qa before do_fetch do_package_qa do_build

SSTATETASKS += "do_recipe_qa"
do_recipe_qa[sstate-inputdirs] = ""
do_recipe_qa[sstate-outputdirs] = ""
python do_recipe_qa_setscene () {
    sstate_setscene(d)
}
addtask do_recipe_qa_setscene

# Check for patch fuzz
do_patch[postfuncs] += "do_qa_patch "

# Check broken config.log files, for packages requiring Gettext which
# don't have it in DEPENDS.
#addtask qa_configure after do_configure before do_compile
do_configure[postfuncs] += "do_qa_configure "

# Check does S exist.
do_unpack[postfuncs] += "do_qa_unpack"

python () {
    import re

    tests = d.getVar('ALL_QA').split()
    if "desktop" in tests:
        d.appendVar("PACKAGE_DEPENDS", " desktop-file-utils-native")

    ###########################################################################
    # Check various variables
    ###########################################################################

    # Checking ${FILESEXTRAPATHS}
    extrapaths = (d.getVar("FILESEXTRAPATHS") or "")
    if '__default' not in extrapaths.split(":"):
        msg = "FILESEXTRAPATHS-variable, must always use :prepend (or :append)\n"
        msg += "type of assignment, and don't forget the colon.\n"
        msg += "Please assign it with the format of:\n"
        msg += "  FILESEXTRAPATHS:append := \":${THISDIR}/Your_Files_Path\" or\n"
        msg += "  FILESEXTRAPATHS:prepend := \"${THISDIR}/Your_Files_Path:\"\n"
        msg += "in your bbappend file\n\n"
        msg += "Your incorrect assignment is:\n"
        msg += "%s\n" % extrapaths
        bb.warn(msg)

    overrides = d.getVar('OVERRIDES').split(':')
    pn = d.getVar('PN')
    if pn in overrides:
        msg = 'Recipe %s has PN of "%s" which is in OVERRIDES, this can result in unexpected behaviour.' % (d.getVar("FILE"), pn)
        oe.qa.handle_error("pn-overrides", msg, d)
    prog = re.compile(r'[A-Z]')
    if prog.search(pn):
        oe.qa.handle_error("uppercase-pn", 'PN: %s is upper case, this can result in unexpected behavior.' % pn, d)

    # Some people mistakenly use DEPENDS:${PN} instead of DEPENDS and wonder
    # why it doesn't work.
    if (d.getVar(d.expand('DEPENDS:${PN}'))):
        oe.qa.handle_error("pkgvarcheck", "recipe uses DEPENDS:${PN}, should use DEPENDS", d)

    # virtual/ is meaningless for these variables
    if "virtual-slash" in (d.getVar("ALL_QA") or "").split():
        for k in ['RDEPENDS', 'RPROVIDES']:
            for var in bb.utils.explode_deps(d.getVar(k + ':' + pn) or ""):
                if var.startswith("virtual/"):
                    oe.qa.handle_error("virtual-slash", "%s is set to %s but the substring 'virtual/' holds no meaning in this context. It only works for build time dependencies, not runtime ones. It is suggested to use 'VIRTUAL-RUNTIME_' variables instead." % (k, var), d)

    issues = []
    if (d.getVar('PACKAGES') or "").split():
        for dep in (d.getVar('QADEPENDS') or "").split():
            d.appendVarFlag('do_package_qa', 'depends', " %s:do_populate_sysroot" % dep)
        for var in 'RDEPENDS', 'RRECOMMENDS', 'RSUGGESTS', 'RCONFLICTS', 'RPROVIDES', 'RREPLACES', 'FILES', 'pkg_preinst', 'pkg_postinst', 'pkg_prerm', 'pkg_postrm', 'ALLOW_EMPTY':
            if d.getVar(var, False):
                issues.append(var)

        fakeroot_tests = d.getVar('FAKEROOT_QA').split()
        if set(tests) & set(fakeroot_tests):
            d.setVarFlag('do_package_qa', 'fakeroot', '1')
            d.appendVarFlag('do_package_qa', 'depends', ' virtual/fakeroot-native:do_populate_sysroot')
    else:
        d.setVarFlag('do_package_qa', 'rdeptask', '')
    for i in issues:
        oe.qa.handle_error("pkgvarcheck", "%s: Variable %s is set as not being package specific, please fix this." % (d.getVar("FILE"), i), d)

    if 'native-last' not in (d.getVar('INSANE_SKIP') or "").split():
        for native_class in ['native', 'nativesdk']:
            if bb.data.inherits_class(native_class, d):

                inherited_classes = d.getVar('__inherit_cache', False) or []
                needle = "/" + native_class

                bbclassextend = (d.getVar('BBCLASSEXTEND') or '').split()
                # BBCLASSEXTEND items are always added in the end
                skip_classes = bbclassextend
                if bb.data.inherits_class('native', d) or 'native' in bbclassextend:
                    # native also inherits nopackages and relocatable bbclasses
                    skip_classes.extend(['nopackages', 'relocatable'])

                broken_order = []
                for class_item in reversed(inherited_classes):
                    if needle not in class_item:
                        for extend_item in skip_classes:
                            if '/%s.bbclass' % extend_item in class_item:
                                break
                        else:
                            pn = d.getVar('PN')
                            broken_order.append(os.path.basename(class_item))
                    else:
                        break
                if broken_order:
                    oe.qa.handle_error("native-last", "%s: native/nativesdk class is not inherited last, this can result in unexpected behaviour. "
                                             "Classes inherited after native/nativesdk: %s" % (pn, " ".join(broken_order)), d)

    oe.qa.exit_if_errors(d)
}
