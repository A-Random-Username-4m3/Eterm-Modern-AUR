# Maintainer: Mike Pento <mjpento@gmail.com>

# list of source files to be patched
_file_list=(
    'libscream.c'
    'options.c'
    'pixmap.c'
    'pixmap.h'
    'screen.c'
)

pkgname=eterm
_pkgname=Eterm
pkgver=0.9.6
pkgrel=29
_pkgrel=1
pkgdesc="A vt102 terminal emulator intended as a replacement for xterm."
arch=('i686' 'x86_64')
url="https://launchpad.net/ubuntu/+source/eterm/0.9.6-1"
license=('custom')
depends=('libast>=0.7' 'libxmu' 'libxres' 'libutempter' 'xorg-fonts-75dpi'
'xorg-fonts-misc')
options=('!libtool' '!debug')
# Xft/Fontconfig are needed for Unicode glyph fallback.
makedepends=('pkgconf' 'python' 'ncurses')
depends+=('libxft' 'fontconfig' 'libutf8proc')
provides=('esetroot')
conflicts=('esetroot')
install=${pkgname}.install
source=(https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/${pkgname}/${pkgver}-${_pkgrel}/${pkgname}_${pkgver}.orig.tar.gz 
    eterm.install
    patches.tgz
)

md5sums=('90e424584c22d4050496874d14f78bb1'
    '32eddc4b9f4d34b0603c4af2ecaee39a'
    '8e4bb6a66b2d61feeae8108d0e1ae122'
)

# All modernization changes are one auditable, fuzz-free C patch.
# Apply after the original five AUR patches from patches.tgz.
source+=('eterm-modernization-v24.patch')
md5sums+=('f040fc6efd55f419ac87629ad8410319')
# Normalize the 2011 release's two legacy mouse-source variants before patching.
source+=('eterm-v24-compat-prep.py')
md5sums+=('25cd23868317af637c1aa9accf15f981')
# Direct per-cell RGB storage; preserve indexed palettes on other visuals.
source+=('eterm-truecolor-v25.patch')
md5sums+=('6df2704df5b51709244b203703260540')
# Optional terminfo profiles: indexed colors by default, RGB only if requested.
source+=('eterm-modern-v26.terminfo')
md5sums+=('6dd4b988b72027d5991b7e42dbccc340')
# v29: size Unicode redraw bookkeeping for the real fullscreen column count.
source+=('eterm-fullscreen-resize-v29.patch')
md5sums+=('5b046a866f943057fdfefcb520d96295')

prepare() {
    cd "${srcdir}/${_pkgname}-${pkgver}/src"

    # Preserve all five original AUR patches.
    for _file in "${_file_list[@]}"; do
        patch -b < "${srcdir}/patches/${_file}.patch"
    done

    # Apply all 0.9.6-24 changes as one ordinary unified diff.
    # --fuzz=0 deliberately fails if the source no longer matches.
    # -N avoids unexpectedly reversing already-applied hunks.
    cd "${srcdir}/${_pkgname}-${pkgver}"
    # This only normalizes mouse-report source syntax; all functional
    # modifications remain in the consolidated C patch below.
    python "${srcdir}/eterm-v24-compat-prep.py" "${srcdir}/${_pkgname}-${pkgver}" || return 1
    patch --batch -N -p1 --fuzz=0 -i "${srcdir}/eterm-modernization-v24.patch" || return 1
    # Change only the 64-bit rendition/color handling after the verified v24 patch.
    patch --batch -N -p1 --fuzz=0 -i "${srcdir}/eterm-truecolor-v25.patch" || return 1

    # Prevent fullscreen redraw from writing past the legacy 250-column
    # stack buffer; leave the capped bitmap draw-run buffer unchanged.
    patch --batch -N -p1 --fuzz=0 -i "${srcdir}/eterm-fullscreen-resize-v29.patch" || return 1

    # libast 0.7's AUR package currently installs headers at
    # /usr/include/foo.h, but libast.h asks for <libast/foo.h>.
    # Create a build-only compatibility include directory. Never modify
    # the system headers or change the installed libast package.
    mkdir -p "${srcdir}/libast-compat/libast"
    local header
    while IFS= read -r header; do
        if [[ "${header}" == /usr/include/*.h && -f "${header}" ]]; then
            ln -sfn "${header}" \
                "${srcdir}/libast-compat/libast/${header##*/}"
        fi
    done < <(pacman -Qlq libast)
    if [[ ! -e "${srcdir}/libast-compat/libast/sysdefs.h" && \
          ! -e /usr/include/libast/sysdefs.h ]]; then
        printf '%s\n' 'Missing LibAST sysdefs.h; check libast headers.' >&2
        return 1
    fi
}

build() {
  cd ${_pkgname}-${pkgver}
  CONF=""
  [ "${CARCH}" = "x86_64" ] && CONF="--disable-mmx"
  # Recent LibAST no longer defines Eterm's historic MEMSET macro.
  # Map it to libc memset and preserve the build-only header workaround.
  local xft_cflags xft_libs u8_cflags u8_libs
  xft_cflags="$(pkg-config --cflags xft fontconfig)" || return 1
  xft_libs="$(pkg-config --libs xft fontconfig)" || return 1
  u8_cflags="$(pkg-config --cflags libutf8proc)" || return 1
  u8_libs="$(pkg-config --libs libutf8proc)" || return 1
  CPPFLAGS="-DMEMSET=memset -I${srcdir}/libast-compat ${xft_cflags} ${u8_cflags} ${CPPFLAGS:-}" \
  LIBS="${xft_libs} ${u8_libs} ${LIBS:-}" \
  ./configure --prefix=/usr --mandir=/usr/share/man \
    --enable-trans --enable-utmp \
    --enable-multi-charset=utf-8 \
    --enable-xim --with-theme-update \
    --with-backspace=bs --without-terminfo \
    --enable-multi-charset ${CONF}
  
  make CFLAGS+=-std=gnu89
}

package() {
  cd ${_pkgname}-${pkgver}
  make DESTDIR=${pkgdir} install
  install -Dm644 LICENSE ${pkgdir}/usr/share/licenses/${pkgname}/LICENSE
  # Install only new, uniquely named entries; do not overwrite ncurses' Eterm.
  install -d "${pkgdir}/usr/share/terminfo"
  tic -x -o "${pkgdir}/usr/share/terminfo" "${srcdir}/eterm-modern-v26.terminfo"
}

