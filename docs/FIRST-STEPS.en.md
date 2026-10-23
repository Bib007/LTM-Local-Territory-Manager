# Your first session with LTM

[Dansk](FIRST-STEPS.md)

From beta.23 there is one unified setup guide. An empty installation opens it automatically. It explains local data, one shared HA installation, private backups and optional Google sharing. Answer the questions, then choose **Save and start tour**.

Answers are saved first; **Finish tour** marks setup complete. The guide closes and the overview displays your plan with direct links to the actual tools. The tour creates no cards, addresses or do-not-call records. **Continue later** or closing interrupts without completing setup; a saved unfinished plan resumes on the next start. Existing completed installations are not forced through the tour again. Reopen the same guide under **Settings → General**.

With maps selected, the plan includes **Connect the address source · your own API key**. Follow the [Datafordeler guide](DATAFORDELER.en.md) and enter your key only in your local app.

Import previous history, existing territory cards and your local do-not-call list under **Settings → Import**. **Follow-ups** brings together card checks, each changed print side, long-running assignments and pending address changes. Each independent item has its own row and count.

You do not need to digitise every paper card before using LTM. Begin with the card numbers and existing assignments. Add geography and printing later, on those same records.

These instructions describe the installed app. The browser demo uses invented records and does not import your data. The app defaults to Danish and offers English controls. Original forms and report content remain Danish.

## 1. Start the right installation

After a complete release is available, follow [Installation](INSTALL.en.md). Use one authoritative installation for your congregation's records. With Home Assistant, your computer and phone open that same private app; they do not each need a database copy.

If moving from an existing installation, use its private export/import process first. A normal program update should preserve the existing data folder and does not require importing the backup again.

## 2. Enter the card numbers

Open **Distriktskort** and create a temporary card, or use quick creation to enter several numbers. A temporary card is a real register entry with assignment history; it simply has no address list or printable geography yet.

Add area names that make sense locally, such as a town and its rural surroundings. Choose urban/rural types where known. These can be edited later.

## 3. Record cards already assigned

Add the publishers under **Forkyndere**. Then use **Registrer eksisterende udlevering** for each card already held by a publisher, with its known assignment date. Do not record an invented completion date just to fill a gap in old history.

Open a publisher to check their active cards. A number-only temporary card can be assigned and returned while you gradually enter the rest of its information.

## 4. Use the desk workflow

| Danish label | What it means |
| --- | --- |
| Forside | Dashboard |
| Daglig brug | Territory desk: assignments and returns |
| Udleverede distriktskort | Cards currently assigned |
| Kort i mappen | Available cards in the physical carry folder |
| Kort i kassen | Available cards in the storage box at home |
| Aflever til kassen | Return the card to the storage box |
| Gennemgået | Record completion |
| Opgaver | Follow-up tasks · open tasks counted only |

Put the cards you actually carry into the folder in the app. When assigning one, select its publisher and date. When it is returned, record whether it was completed and optionally add a task, for example to review a do-not-call entry later. **Returns go to the box**, not automatically back into the folder.

Each recorded completion counts, including repeated completions of the same card. The visit total is an estimate based on the card's address/unit count; it is not a record of individual calls made. A service year runs from **1 September to 31 August**.

## 5. Add detail when ready

- Import/draw the congregation's outer boundary, review it, then fetch addresses inside it. Keep your actual KML and records private.
- Fill in existing cards individually, or draw each card and select addresses in the map editor. Automatic division proposals are paused from beta.61.
- Select do-not-call entries from the card's own addresses. The English abbreviation is DNC; the installed Danish app uses IB.
- Test front/back printing on ordinary paper and save your printer profiles before using pre-cut cards.
- Google Drive is optional. Follow [Drive and QR setup](GOOGLE-DRIVE.en.md) only if you want approved public map images.

Download a private backup after the initial setup. Keep a copy outside the app's machine, somewhere only the responsible operator can access. Keep credentials and backups out of GitHub and AI conversations.
