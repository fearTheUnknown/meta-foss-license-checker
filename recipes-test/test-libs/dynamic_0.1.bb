LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " file://dynamic.c \ 
            file://dynamic.h "

S = "${WORKDIR}"

do_compile() {
    #Compile dynamic lib
    ${CC} -c -fPIC dynamic.c
    ${CC} ${LDFLAGS}  -shared -Wl,-soname,libdynamic.so.1 -o libdynamic.so.1.0 dynamic.o
}

do_install() {

    #Install the dynamic lib
    install -d ${D}${libdir}
    install -m 0755 libdynamic.so.1.0 ${D}${libdir}

    #Create symbolic link to satisfy Linux standard
    ln -s libdynamic.so.1.0 ${D}${libdir}/libdynamic.so.1
    ln -s libdynamic.so.1 ${D}${libdir}/libdynamic.so

    #Install the dynamic header file
    install -d ${D}${includedir}
    install -m 0644 dynamic.h ${D}${includedir}
}