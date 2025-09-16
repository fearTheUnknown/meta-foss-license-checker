LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " file://strong.c \
            file://strong_duplicate.c \
            file://strong.h "

S = "${WORKDIR}"

do_compile() {
    #Compile strong static lib
    ${CC} -c strong.c
    ${CC} -c strong_duplicate.c

    #Produce the strong lib
    ${AR} rcs libstrong.a strong.o

    #Produce the strong duplicate lib
    ${AR} rcs libstrong_duplicate.a strong_duplicate.o
}

do_install() {

    #Install strong static lib to default location in root filesystem
    install -d ${D}${libdir}
    install -m 0755 libstrong.a ${D}${libdir}

    #Install strong duplicate static lib to default location in root filesystem
    install -m 0755 libstrong_duplicate.a ${D}${libdir}

    #Install header file of strong static lib to default location in root filesystem
    install -d ${D}${includedir}
    install -m 0644 strong.h ${D}${includedir}
}