LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " file://weak1.c \
            file://weak2.c \
            file://strong.c \
            file://strong.h \
            file://weak.h "

S = "${WORKDIR}"

do_compile() {
    #Compile strong and weak object files
    ${CC} -c weak1.c
    ${CC} -c weak2.c
    ${CC} -c strong.c

    #Archive object files into a static lib
    ${AR} rcs libstrong_weak.a weak1.o weak2.o strong.o
}

do_install() {

    #Install a static lib with both strong and weak symbol to default location in root filesystem
    install -d ${D}${libdir}
    install -m 0755 libstrong_weak.a ${D}${libdir}

    #Install header files of static lib to default location in root filesystem
    install -d ${D}${includedir}
    install -m 0644 weak.h ${D}${includedir}
    install -m 0644 strong.h ${D}${includedir}
}