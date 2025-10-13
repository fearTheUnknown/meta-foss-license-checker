SUMMARY = "System Test Case 1"
DESCRIPTION = "Test strong symbol link status in a static library"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

#Switch off including base header files
INCLUDE_BASE_HEADERS = '0'

SRC_URI = "file://strong_executable.c"

S = "${WORKDIR}"

DEPENDS = "strong"

do_compile(){
    ${CC} -DUSE_SYSCALL strong_executable.c ${LDFLAGS} -o strong_executable -lstrong
}

do_install(){
    install -d ${D}${bindir}
    install -m 0755 strong_executable ${D}${bindir}
}
