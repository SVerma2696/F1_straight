# Security Policy

This is a small personal/educational pixel-art racing game, not
software that handles money, passwords, or anyone's private data. Even
so, if you find a real security problem -- like something that lets
code run that shouldn't, or a way to make the app crash/misbehave in a
harmful way -- please tell me privately first, instead of opening a
public issue, so it can get fixed before anyone else finds it.

## Supported Versions

Only the most recent tagged release (see the
[Releases page](https://github.com/SVerma2696/f1_straight/releases))
gets security fixes. If you're on an older version, please update
first and check whether the problem is still there.

## Reporting a Vulnerability

Please use GitHub's private vulnerability reporting for this repo:
[Report a vulnerability](https://github.com/SVerma2696/f1_straight/security/advisories/new)
(also found under this repo's **Security** tab). If you'd rather not
use GitHub, email **saksham2696@gmail.com** instead.

When you report it, please include:
* What the problem is, and which file or feature it's in
* Steps to make it happen again, if you can
* How bad you think it could be

## What Happens Next

This is a one-person hobby project, so please be patient -- there's no
dedicated security team behind it. I'll try to:
1. Reply within a few days to say I've seen your report.
2. Confirm whether it's a real issue and how serious it is.
3. Let you know once a fix is out, and credit you (if you'd like).

Please don't share the details publicly until a fix has been released.

## Scope

This policy covers the code in this repository: `game.py`,
`launcher.py`, `build_app.py`, and the ESP32 firmware in `firmware/`.
It does not cover third-party dependencies (`pygame-ce`,
`customtkinter`, `pillow`, `pyserial`) -- please report issues with
those directly to their own projects.
