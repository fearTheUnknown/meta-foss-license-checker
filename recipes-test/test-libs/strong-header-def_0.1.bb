LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " file://strong_def.h "

S = "${WORKDIR}"

do_install() {
    #Install header file with function definition in it
    install -d ${D}${includedir}
    install -m 0644 strong_def.h ${D}${includedir}
}