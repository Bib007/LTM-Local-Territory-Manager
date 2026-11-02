# LTM 1.12.8 · Clear numeric street summaries

Physical card fronts now show numeric street envelopes, with separate even and odd sides. Internal A/B/C/D variants and house numbers that do not exist locally do not fragment the interval. A known existing numeric house outside the card creates a break: for example 2–46 & 50–52 when 48 is excluded. Keep the final suffix at a boundary such as 3–9B; 8A, 8C and 10 display as 8–10.

These labels summarize a card. They never expand its actual membership or visit count. Exact address units, IB, manual lines and original forms are preserved. The bounded front layout from 1.12.7 remains.

Update normally to 1.12.8 in Home Assistant, preserving the existing installation and data. Download private LTM and account backups first. Do not uninstall or delete data.
