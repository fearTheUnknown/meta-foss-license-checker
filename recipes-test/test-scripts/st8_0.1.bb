SUMMARY = "System Test Case 8"
DESCRIPTION = "Test dynamic linking with a shared libray"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

#Switch off including base header files
INCLUDE_BASE_HEADERS = '0'

SRC_URI = "file://dynamic_executable.c"

S = "${WORKDIR}"

DEPENDS = "dynamic"

do_compile(){
    ${CC} -DUSE_SYSCALL dynamic_executable.c ${LDFLAGS} -o dynamic_executable -ldynamic
}

do_install(){
    install -d ${D}${bindir}
    install -m 0755 dynamic_executable ${D}${bindir}
}
