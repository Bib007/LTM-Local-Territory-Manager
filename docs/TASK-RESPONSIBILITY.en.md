# Task responsibility

Available from LTM 1.12.4.

Users who can manage accounts and edit notes can choose an optional responsible person when creating or editing a task. The choice uses active local LTM accounts. An assignment grants no additional permissions and sends no notification.

The responsible person sees **Assigned to you** and can use **My tasks**. Other note readers see that someone is responsible, without receiving that account's name or identifier. Account administrators can see the selected name. **Unassigned** shows tasks with no responsible person.

An administrator can create a linked task from an automatic follow-up. Opening the action again edits the same task. The task remains available if the original follow-up disappears, and must be completed explicitly. Completing it does not approve a print revision, change a card, or resolve the original condition.

Weekly tasks keep their assignment when a weekly occurrence is completed. Ordinary text edits retain an assignment, including an inactive account. Inactive accounts cannot receive a new assignment; an administrator can clear or replace the old assignment. Concurrent changes to the responsible person require a refresh instead of silently replacing the other choice.

Assignments are local note data and follow normal data backups. Accounts use their separate account backup. If an account is absent after restoration, the task stays assigned to an **inactive or removed account** until an administrator clears or replaces it. No account is created automatically.

Verification uses fictional accounts and temporary SQLite files. Run the `test_task_ownership_*` methods in `distrikt/tests/test_profiles_integration.py` and the focused browser script `scripts/check_task_ownership_browser.cjs`.
