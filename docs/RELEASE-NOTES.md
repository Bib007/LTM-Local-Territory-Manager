# LTM 1.12.7 · Compact street intervals and bounded card fronts

Fixes the 1.12.6 front-layout regression. Exact houses appear as compact intervals, separated by `&` at gaps: for example `20–24 & 28–30 (lige)`. Each road has separate even and odd lines; address types are combined on the physical front while exact units and visit counts remain intact. Consecutive lettered houses are compacted without hiding gaps.

Dense lists fit within the original form body. They cannot paint over its footer. A list that cannot fit is explicitly flagged and cannot be printed through the normal print control. The original forms are unchanged.

Home Assistant users, including anyone who installed an earlier 1.12.6 build, can install 1.12.7 as a normal update. Download a private LTM data backup and, where profiles are enabled, an account backup first. Preserve the existing installation and its data directory. Do not uninstall or delete data.
