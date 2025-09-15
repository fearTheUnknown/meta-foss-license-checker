LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " file://weak1.c \
            file://weak2.c \ 
            file://weak.h "

S = "${WORKDIR}"

do_compile() {
    #Compile weak object files
    ${CC} -c weak1.c
    ${CC} -c weak2.c
}

do_install() {

    #Install weak object files to default location in root filesystem
    install -d ${D}${libdir}
    install -m 0755 weak1.o weak2.o ${D}${libdir}

    #Install header file of weak static lib to default location in root filesystem
    install -d ${D}${includedir}
    install -m 0644 weak.h ${D}${includedir}
}