SUMMARY = "System Test Case 2"
DESCRIPTION = "Tes duplicate strong symbol link status in a static library"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

#Switch off including base header files
INCLUDE_BASE_HEADERS = '0'

SRC_URI = "file://strong_executable.c"

S = "${WORKDIR}"

DEPENDS = "strong-duplicate"

do_compile(){
    #Link strong_executable to strong lib
    ${CC} -DUSE_SYSCALL strong_executable.c ${LDFLAGS} -o strong_executable -lstrong

    #Link duplicate_strong_executable to duplicate strong lib
    ${CC} -DUSE_SYSCALL strong_executable.c ${LDFLAGS} -o duplicate_strong_executable -lstrong_duplicate
}

do_install(){
    install -d ${D}${bindir}
    install -m 0755 strong_executable ${D}${bindir}
    install -m 0755 duplicate_strong_executable ${D}${bindir}
}
