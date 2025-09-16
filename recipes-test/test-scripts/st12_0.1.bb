SUMMARY = "System Test Case 10"
DESCRIPTION = "Test the warning function for linked files with strict licenses"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

#Switch off including base header files
INCLUDE_BASE_HEADERS = '0'

SRC_URI = "file://strong_weak_executable_obj.c\
            file://strong_executable.c\
            file://weak_executable.c"

S = "${WORKDIR}"

DEPENDS = "strong-weak-obj strong weak"

do_compile(){
    ${CC} -DUSE_SYSCALL strong_weak_executable_obj.c recipe-sysroot/usr/lib/strong_weak_obj.o  ${LDFLAGS} -o strong_weak_executable_obj
    ${CC} -DUSE_SYSCALL strong_executable.c ${LDFLAGS} -o strong_executable -lstrong
    ${CC} -DUSE_SYSCALL weak_executable.c ${LDFLAGS} -o weak_executable -lweak1 -lweak2 -lweak
}

do_install(){
    install -d ${D}${bindir}
    install -m 0755 strong_weak_executable_obj ${D}${bindir}
    install -m 0755 strong_executable ${D}${bindir}
    install -m 0755 weak_executable ${D}${bindir}
}
