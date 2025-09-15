LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " file://weak1.c \
            file://weak2.c \ 
            file://weak.h "

S = "${WORKDIR}"

do_compile() {
    #Compile weak static libs
    ${CC} -c weak1.c
    ${CC} -c weak2.c
    ${AR} rcs libweak1.a weak1.o
    ${AR} rcs libweak2.a weak2.o
    ${AR} rcs libweak.a weak1.o weak2.o
}

do_install() {

    #Install weak static libs to default location in root filesystem
    install -d ${D}${libdir}
    install -m 0755 libweak1.a ${D}${libdir}
    install -m 0755 libweak2.a ${D}${libdir}
    install -m 0755 libweak.a ${D}${libdir}

    #Install header file of weak static lib to default location in root filesystem
    install -d ${D}${includedir}
    install -m 0644 weak.h ${D}${includedir}
}