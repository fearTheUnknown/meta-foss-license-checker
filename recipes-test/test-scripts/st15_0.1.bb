SUMMARY = "System Test Case 15"
DESCRIPTION = "Test the warning of undefined licenses"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

#Switch off including base header files
INCLUDE_BASE_HEADERS = '0'

SRC_URI =   "file://dynamic_executable.c\
            file://strong_executable.c\
            file://weak_executable.c "

S = "${WORKDIR}"

DEPENDS = "dynamic strong weak"

do_compile(){
    ${CC} -DUSE_SYSCALL dynamic_executable.c ${LDFLAGS} -o dynamic_executable -ldynamic
    ${CC} -DUSE_SYSCALL strong_executable.c ${LDFLAGS} -o strong_executable -lstrong
    ${CC} -DUSE_SYSCALL weak_executable.c ${LDFLAGS} -o weak_executable -lweak
}

do_install(){
    install -d ${D}${bindir}
    install -m 0755 dynamic_executable ${D}${bindir}
    install -m 0755 strong_executable ${D}${bindir}
    install -m 0755 weak_executable ${D}${bindir}
}
