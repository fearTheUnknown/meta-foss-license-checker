SUMMARY = "System Test Case 5"
DESCRIPTION = "Test inclusion of header with function definition"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

#Switch off including base header files
INCLUDE_BASE_HEADERS = '0'

SRC_URI = "file://strong_header_executable.c"

S = "${WORKDIR}"

DEPENDS = "strong-header-def"

do_compile(){
    ${CC} -DUSE_SYSCALL strong_header_executable.c  ${LDFLAGS} -o strong_header_executable
}

do_install(){
    install -d ${D}${bindir}
    install -m 0755 strong_header_executable ${D}${bindir}
}
