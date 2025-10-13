SUMMARY = "System Test Case 6"
DESCRIPTION = "Test weak symbol link status in 2 static libraries"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

#Switch off including base header files
INCLUDE_BASE_HEADERS = '0'

SRC_URI = "file://weak_executable.c"

S = "${WORKDIR}"

DEPENDS = "weak"

do_compile(){
    ${CC} -DUSE_SYSCALL weak_executable.c ${LDFLAGS} -o weak_executable -lweak1 -lweak2 -lweak
}

do_install(){
    install -d ${D}${bindir}
    install -m 0755 weak_executable ${D}${bindir}
}
