# Daily workspace

[Dansk](DAILY-WORKSPACE.md)

These features are prepared for the next app version; use a complete release when updating.

### A useful starting point

From beta.34, relevant setup steps complete automatically when settings or records are actually saved, such as the congregation, both print profiles, publishers and cards. Opening a shortcut or preview does not count. New installations start with a folder minimum of 0; enter and save your chosen number even when it should be 0. Existing minimum values and progress are preserved. **Skip** and **Undo** remain available. Connections and the overall assignment review still require **Done**, because the app cannot verify that the whole review is finished.

From beta.33, **Hurtig oprettelse → Range** generates card numbers from the inclusive start to the inclusive end. Optionally choose a minimum number of digits for zero padding and one prefix letter. 0–300 with four digits gives 0000–0300, 301 cards; a prefix is preserved. The limit remains 500 cards per batch. Review all numbers, the count and any duplicates before confirming. Preview creates nothing. **Custom list** still treats 1–10 as one literal card number, not a range.

From beta.32, **Tasks** handles all follow-up. Existing notes become tasks while retaining their text, dates, card links and completion status. The same conversion runs after explicitly importing an older backup; previewing one changes nothing. User text is never translated. Legacy storage/API names remain compatible with existing backups.

Navigation counts open tasks only. Cards with open tasks are marked in the card/folder list and get a prominent assignment-form warning containing their task text. Tasks do not create do-not-call records automatically or block assignment. Use them to add a do-not-call record, check house numbers or remove a house that does not exist. **○** marks a task done; **✓** reopens it. Completed tasks stay editable under Completed without losing content or links.

Home shows the current service year, where the cards are, completed rounds and follow-up. The carry-folder, storage-box and open-task shortcuts open the corresponding existing lists. Counts are calculated from the local records; a card covered twice contributes two completions, but coverage counts that card only once. Estimated visits describe the address/unit counts on completed cards, not recorded house-to-house activity.

The follow-up list uses four calendar months from the start of the current round. It is a prompt for your own review, not a congregational decision or an automatic reassignment. Changed-side counts are reminders to check and reprint physical cards. Opening the dashboard does not change any records.

The monthly graph has an expandable table containing the same figures. It includes empty months. The last recorded circuit-overseer visit is marked when it falls within the displayed service year. Numeric dates and decimal formatting currently retain the Danish convention.

### Find a card or publisher

Use the search control at the top or **Ctrl K / Command K** outside a text field. Search by card number, card name, road, area or publisher. Search stays in the local app: it does not call an external search service. Matching names and notes are never translated. Large result sets show a stated limit; narrow the search to find more. Escape closes the search dialog through the normal dialog controls.

On a phone, the menu button announces whether the menu is open. Tap the backdrop or press Escape to close it. The blue logo and the dark interface remain the same across screen sizes; reduced-motion preferences disable the menu transition.

### Sign-in and keyboard

Sign-in supports Danish/English. Changing language preserves the field and does not change the password. Only the language choice is saved as a preference; enter your password in your local app, never in chat or feedback. Sign-in errors appear in the form, and interrupted requests are not automatically repeated.

Inside dialogs, Tab and Shift+Tab move between available controls. Escape follows the normal save/close checks; decline closing to keep the fields when saving is uncertain. After closing, focus returns to the control that opened the dialog when it is still available.

### Connection is not the same as saving

- **All changes saved** means the normal app operation completed successfully.
- **Saving…** means a save operation is in progress.
- **Saving is not confirmed** means the app cannot confirm the result. A disconnected request may already have reached the server. Keep the open text, restore the connection, then check the records before repeating the action.
- **The change is saved · refresh data before making another change** means the write was acknowledged, but the subsequent read or display did not complete. Do not repeat the creation, import or sharing action. Finish the edit, choose Refresh and check the result.
- **The change was rejected** means the app received a known rejection, such as an existing card number. Correct the reported error; your fields have not been overwritten.
- **The connection is responding again** confirms only that the server answered a connection check. It does not confirm a previous write. The app does not automatically resend it or clear the uncertain-save indicator.

Connection checks are read-only and leave open fields intact. Finish or deliberately close an edit before choosing **Refresh**. Refresh reads the server state; it is not an automatic retry of a failed write. After an uncertain save, the status says **Data refreshed · check the earlier change**, not **All changes saved**. Compare the records with your intended change. If the app cannot open at all, its recovery screen offers a retry and tells you to check the computer/Home Assistant, Wi-Fi and VPN, without assuming a particular platform.
