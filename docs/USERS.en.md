# Accounts, roles and personal introductions

LTM profiles belong to one installed system. The administrator chooses the people, roles and permissions inside that installation; no advance list of names is required.

## Enable profiles deliberately

Open user administration from the installation you already have access to, choose the first administrator account and confirm activation. The first administrator can manage users and permissions. Once profiles are enabled, protected application routes use individual account sessions. The older shared server password does not grant access to profile data.

Keep a separate private account backup and a recovery plan before relying on profiles. Forgotten administrator credentials have a local recovery path; they are not reset through an anonymous public endpoint.

## Choose the necessary access

Roles combine when an account has more than one. Managing users does not automatically mean reading every territory record. Give each account only the areas it needs.

- **Home overview** and **report summaries** are separate permissions. Summary-only access shows aggregate counts without raw names, IB, notes, addresses, card identifiers or detailed records.
- **Cards, publishers, assignments, history, IB, geography and tasks** retain their own read/write permissions. Detailed reports and original S-13 export still require the corresponding underlying records.
- **Connections**, **public image sharing**, **backups** and **user administration** have separate permissions. A backup reminder does not itself grant export or restore rights.
- Operations that change several modules require the relevant permissions for their effects. A permitted import preview is not permission to apply every proposed change.

The role panel groups permissions and describes dependencies. Ordinary updates migrate older role combinations conservatively, using visible compatibility roles where necessary to preserve former overview/report access. Review those visible grants, then change them deliberately if you want a different policy. Later choices are preserved.

## Personal introduction and release news

A personal guide follows the account's current permissions. It does not change the installation's common setup plan. A user administrator can preview the selected account's permitted guide and schedule it for that account's **next successful login**. A currently open session does not consume that next-login request.

Progress and seen release items are saved for the account. A stale acknowledgement cannot finish a newer guide request. Permission changes alter the steps and release items that are available. Manually replaying the introduction preserves the current form draft.

## Two people editing

Keep an editor open while making the change. Independent field edits can be combined. When saved proposals disagree, LTM retains evidence and both proposals for review; a later validated change remains current until a permitted reviewer deliberately chooses a retained proposal.

An unchanged ordinary form sends no new write. The first deliberate confirmation of a zero carry-folder target is still meaningful and is saved. Open editors retain session-bound bases through ordinary page reads, within time/capacity limits.

If a base expires, the form keeps its text and explains why it needs reopening. If a write is confirmed but the refreshed overview fails, the app reports it as saved and asks for a check before another write. If the actual outcome is unknown, inspect current records before repeating the action. These cases are different from a rejected write.

## Backups and restore

Territory-data backups, account backups and connection configuration are different things. A normal data ZIP excludes account/session files and custom connection-token values. A restore preserves the destination's custom address connection value and treats imported public-image bindings as inert; a new local publication approval is required.

Account restoration reconfirms the administrator password, validates a short-lived preview and logs active sessions out. Keep the previous installation and private backups until recovery has been checked. Do not send account backups or connection material to public feedback, the demo or the project repository.

English is the default for new users; saved language choices and Danish remain supported. Translation is still partial, and original printed forms are unchanged.
