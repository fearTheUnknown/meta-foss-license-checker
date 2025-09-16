SUMMARY = "System Test Case 10"
DESCRIPTION = "Test strong link status in case of an executable links to both strong and weak symbols in a static lib"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

#Switch off including base header files
INCLUDE_BASE_HEADERS = '0'

SRC_URI = "file://strong_weak_executable_obj.c"

S = "${WORKDIR}"

DEPENDS = "strong-weak-obj"

do_compile(){
    ${CC} -DUSE_SYSCALL strong_weak_executable_obj.c recipe-sysroot/usr/lib/strong_weak_obj.o  ${LDFLAGS} -o strong_weak_executable_obj
}

do_install(){
    install -d ${D}${bindir}
    install -m 0755 strong_weak_executable_obj ${D}${bindir}
}
