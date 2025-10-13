LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " file://strong.c \ 
            file://strong.h "

S = "${WORKDIR}"

do_compile() {
    #Compile object file with strong symbol
    ${CC} -c strong.c

    #Compile duplicate object file with strong symbol
    ${CC} -c strong.c -o strong_duplicate.o
}

do_install() {

    #Install strong static lib to default location in root filesystem
    install -d ${D}${libdir}
    install -m 0755 strong.o ${D}${libdir}
    install -m 0755 strong_duplicate.o ${D}${libdir}

    #Install header file of strong static lib to default location in root filesystem
    install -d ${D}${includedir}
    install -m 0644 strong.h ${D}${includedir}
}