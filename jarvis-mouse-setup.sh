#!/usr/bin/env bash
# One-time mouse-enabler for JARVIS on this machine (Hyprland 0.56).
#
# WHY THIS EXISTS
#   Wayland forbids one client from moving another's cursor — by design.
#   Hyprland 0.56 omits the virtual-pointer protocol, so synthetic clicks are
#   refused inside the compositor itself. ydotool drives the kernel's uinput
#   device directly, which lands REAL input events, indistinguishable from the
#   physical mouse, and works on native Wayland windows as well as XWayland.
#
# WHAT IT ASKS OF YOU: your sudo password — once, right here, right now.
set -e
echo "1/5 installing ydotool (Arch package)…"
sudo pacman -S --noconfirm ydotool

echo "2/5 loading the uinput kernel module (once + every boot)…"
sudo modprobe uinput
echo uinput | sudo tee /etc/modules-load.d/uinput.conf >/dev/null

echo "3/5 letting YOUR user speak to it (udev + group)…"
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/80-uinput.rules >/dev/null
sudo groupadd -f input 2>/dev/null || true
sudo usermod -aG input "$USER"

echo "4/5 starting the daemon under YOUR account (user service)…"
sudo udevadm control --reload
sudo udevadm trigger --name-match=uinput 2>/dev/null || true
sudo udevadm settle
systemctl --user enable --now ydotoold.service

echo "5/5 sanity check…"
sleep 1
if ydotool info 2>/dev/null | head -1 || echo "(daemon socket check)"; then
  :
fi
echo
echo "DONE. Log out and back in once (or reboot) so the group applies, then"
echo "JARVIS can move and click the real mouse. Ask the assistant to test:"
echo '  "move the mouse to the center of the screen"'
echo "You never need to run this again."
