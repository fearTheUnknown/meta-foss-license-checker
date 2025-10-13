LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " file://strong_weak_obj.c \
            file://strong_weak_obj.h "

S = "${WORKDIR}"

do_compile() {
    #Compile an object file that contains strong and weak symbol
    ${CC} -c strong_weak_obj.c
}

do_install() {

    #Install a static lib with both strong and weak symbol to default location in root filesystem
    install -d ${D}${libdir}
    install -m 0755 strong_weak_obj.o ${D}${libdir}

    #Install header file of weak static lib to default location in root filesystem
    install -d ${D}${includedir}
    install -m 0644 strong_weak_obj.h ${D}${includedir}
}