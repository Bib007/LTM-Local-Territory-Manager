# Optional Google Drive and QR setup

[Dansk](GOOGLE-DRIVE.md)

LTM works without Google. This optional connection publishes an individually reviewed PNG map to your chosen Drive account and gives the paper card a QR link. People with the link can view the image without signing in to Google; test that with your own account before distributing cards.

The private databases, publishers, assignments, notes and do-not-call list are not uploaded by this feature. Visible geography and allowed visit points are still part of the image: inspect the entire preview before approving it.

The installed app is currently Danish. The menu and file names below are the actual Danish names, not labels that depend on a future full English translation.

## Digital card in beta.12

From beta.12 the shared image has a new layout with a clear card number/name, a large map and a small printed-front miniature in the corner. The miniature reuses the blank S-12 front and the physical front’s road-row formatter, but is built only from approved public addresses. It does not copy an image of the private card. DNC details, notes and holder records are excluded.

Existing QR links and the loan-driven access cycle are preserved. Older layouts are marked under Sharing and QR. Choose **Opdater Google Drive-upload**, review the entire image and miniature, and explicitly approve publication. A layout update does not upload anything by itself. The QR still opens a PNG image on Google Drive; no new public website is created.

## 1. Create your own Google client

1. Sign in to [Google Cloud Console](https://console.cloud.google.com/) with your chosen account and create a project. A dedicated account makes later handover easier.
2. Enable **Google Drive API** in the project's API library.
3. Configure the OAuth app name, contact address and audience. An ordinary personal account normally uses an external audience.
4. Create an OAuth client of type **Desktop app**, and download its client JSON. A Web application client or service account is not the connector used by LTM.
5. If testing the OAuth app, add your account as a test user. Before ongoing use, review the publishing status: external OAuth apps in Testing can issue refresh tokens that expire after seven days for this scope. Follow Google's current requirements and reconnect after the appropriate production setup.

Google may change console labels or require additional account steps. Do not work around an account restriction or paste a client/token file into an issue. The Google project belongs to you; LTM does not use a shared developer OAuth project.

The scope is **drive.file**, for files the app creates or receives access to. It is not a request to read every file in the account. An OAuth app's production status does not publish your local databases.

## 2. Connect on Mac or Windows

Run `Forbind-Google-Drive.command` on Mac or `Forbind-Google-Drive.cmd` on Windows from the program folder. Python is required, as for the desktop app.

Choose the downloaded client JSON. The helper opens Google's sign-in page. Select the intended account and approve the requested file access. Your Google password is entered only at Google.

The helper receives the callback at a temporary **127.0.0.1** address on your own computer, using PKCE and a random state value. No router port needs to be opened. It normally saves `Distrikt-Google-forbindelse.json` in Downloads.

## 3. Import the connection privately

Open your installed LTM app, including over your own router-VPN if using HA away from home. Go to **Indstillinger → Forbindelser** and select `Distrikt-Google-forbindelse.json`. Check that the intended account is displayed.

Delete the connection file from Downloads afterwards. Treat it like a password: it contains continuing access. Never upload it to GitHub or send it to AI. The app keeps it separate from its record databases; it is excluded from the app's data export and HA backups. Reconnection is therefore needed when moving installations.

## 4. Publish and test one map

1. Open a card with saved geographical boundary and visit points.
2. Choose **Publicér / opdater på Google Drive** in its geographical view.
3. Wait for the OpenStreetMap preview and review the full image, including the card number/name and reminder to check the physical IB/DNC side.
4. Explicitly approve publication. The server queues the approved image and handles uploading and link access.
5. Check **Deling og QR** for its publication status. Print the card front to include its QR code, or use the separate QR output where appropriate.
6. Open the preview link in a private browser without Google login and scan the printed QR with a phone.

Sharing is read-only for anyone with the link. It is not an interactive territory app, and link recipients can save or forward the image. Keeping Drive's public discovery option off is not a promise that the content is confidential.

## Access follows the loan

An approved image can be uploaded privately and its QR printed before the card is issued. LTM enables public read access when the card is issued and removes it when the card is returned. Completing a round while keeping the card leaves access open. Reissuing the card reopens the same approved file without uploading it again. If Google changes its actual viewer link, the front is marked for reprinting; check the QR after first enabling public access. Outdated images require a new approved preview. A manual withdrawal stays private until a new publication.

Only file-permission requests are sent to Google, not the loan history or publisher identity. The app must be running and connected to Google. The status distinguishes pending/failed changes from confirmed closure. After five unsuccessful attempts, use **Prøv adgangsændring igen**. Pending replacement uploads do not postpone the attempt to close the old image on return.

The same QR link works for everyone who has it, including former card holders when it reopens. This closes access between loans; it is not access restricted to the current holder. Downloaded copies cannot be recalled. Owners, separately invited accounts and inherited folder permissions may still permit access. Do not move the image into a publicly shared folder or grant separate access if it must follow LTM's loan status.

Closed links show Google's own access page. LTM does not customize that page, approve access requests, or introduce another public website. Test privately with a non-sensitive fictional card: prepare, issue, return and reissue using the same QR, checking access in a signed-out browser at each step.

## Updating the image

The next approved publication updates the existing Drive file and preserves its ID/link. Do not manually delete that file if already printed QR codes must continue to work.

Relevant card/IB changes mark the image as outdated. The app attempts to remove public access to the old image when it can reach Google. That is not instantaneous, and downloaded copies cannot be recalled. Check the status and resolve errors.

Generate and approve a fresh preview in the browser to publish the updated image. The server can upload/retry an approved image after the browser closes, but it does not silently generate new OpenStreetMap images on its own. Automatic retries are bounded; after five failed attempts, use the displayed manual retry action.

## Moving or disconnecting

Remove public access to each map first if those images should no longer be available. Disconnecting Google stops uploads but does not itself remove already shared files.

When moving between HA, Mac and Windows, retain the same Google account/client if the existing QR links need to remain. Import the private app data, reconnect that account and review/re-publish the maps. File IDs travel with the record export, but credentials do not. A different Google account needs a deliberate removal/republication process and new links.

## Official references

- [OAuth for installed applications](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Refresh token expiration](https://developers.google.com/identity/protocols/oauth2#expiration)
- [Drive API scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)
- [Drive sharing](https://developers.google.com/workspace/drive/api/guides/manage-sharing)

For Danish instructions included with the program, see [GOOGLE-DRIVE-OPSAETNING.md](../distrikt/GOOGLE-DRIVE-OPSAETNING.md).
