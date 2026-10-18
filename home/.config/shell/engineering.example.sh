# Optional: source this file from shell/environment.local.sh.
# Resolve an installed qsys executable instead of retaining a package-build cache.
_dotfiles_qsys=$(command -v qsys 2>/dev/null) || _dotfiles_qsys=
if [ -n "$_dotfiles_qsys" ]; then
    _dotfiles_qsys=$(readlink -f -- "$_dotfiles_qsys")
    export QSYS_ROOTDIR="${_dotfiles_qsys%/*}"
fi
unset _dotfiles_qsys
# Or set QSYS_ROOTDIR locally to an existing Quartus sopc_builder/bin directory.
# Keep this particular cross compiler optional; omit if the course is finished.
_dotfiles_cross="$HOME/Projects/st4r_l1ght/arm-rockchip830-linux-uclibcgnueabihf/bin"
if [ -x "$_dotfiles_cross/arm-rockchip830-linux-uclibcgnueabihf-gcc" ]; then
    case ":$PATH:" in
        *":$_dotfiles_cross:"*) ;;
        *) PATH="$_dotfiles_cross:$PATH" ;;
    esac
    export PATH
fi
unset _dotfiles_cross
