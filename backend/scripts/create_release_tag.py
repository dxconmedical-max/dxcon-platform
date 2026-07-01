#!/usr/bin/env python3
"""Print recommended release tag commands (does not execute git)."""

from __future__ import annotations


def main():
    print("Recommended release tag commands:")
    print('git tag -a v1.0.0-rc1 -m "DxCon v1.0.0 RC1"')
    print("git push origin v1.0.0-rc1")


if __name__ == "__main__":
    main()
