"""Read-only estimates of historical editing activity from LTM audit events.

An interval counts only when TWO committed edits by the same known actor (or
the same unattributed shared-login bucket) are at most 15 minutes apart.
Single edits and longer gaps add no time. This is not a login or presence log.
No personal notes, addresses or card contents are included in the result.
"""
from collections import defaultdict
from datetime import datetime, timezone

IDLE_SECONDS = 15 * 60
SHARED = "__shared__"


def _timestamp(raw):
    if not isinstance(raw, str):
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return value.astimezone(timezone.utc) if value.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def _month(value):
    return value.astimezone().strftime("%Y-%m")


def _round_minutes(seconds):
    return round(seconds / 60.0, 1)


def _merge_seconds(intervals):
    """Count overlapping editing intervals once for system-active time."""
    if not intervals:
        return 0.0
    ordered = sorted(intervals)
    begin, end = ordered[0]
    total = 0.0
    for start, stop in ordered[1:]:
        if start <= end:
            end = max(end, stop)
        else:
            total += (end - begin).total_seconds()
            begin, end = start, stop
    return total + (end - begin).total_seconds()


def summarize(events):
    """Return small aggregates only, never raw audit event payloads."""
    by_actor = defaultdict(list)
    for event in events:
        if not isinstance(event, dict):
            continue
        at = _timestamp(event.get("at"))
        if at is None:
            continue
        actor_id = event.get("actor_id")
        actor_id = actor_id if isinstance(actor_id, str) and actor_id else None
        actor_name = event.get("actor_name")
        actor_name = actor_name if isinstance(actor_name, str) and actor_name.strip() else ""
        by_actor[actor_id or SHARED].append((at, actor_name))

    users = []
    all_intervals = []
    total_months = defaultdict(lambda: {"actions": 0, "seconds": 0.0})
    all_days = set()
    first = last = None
    for key, items in by_actor.items():
        items.sort(key=lambda item: item[0])
        months = defaultdict(lambda: {"actions": 0, "seconds": 0.0})
        days = set()
        user_seconds = 0.0
        intervals = []
        for index, (stamp, _) in enumerate(items):
            month = _month(stamp)
            months[month]["actions"] += 1
            total_months[month]["actions"] += 1
            day = stamp.astimezone().date().isoformat()
            days.add(day)
            all_days.add(day)
            if index:
                previous = items[index - 1][0]
                gap = (stamp - previous).total_seconds()
                if 0 < gap <= IDLE_SECONDS:
                    user_seconds += gap
                    months[month]["seconds"] += gap
                    total_months[month]["seconds"] += gap
                    intervals.append((previous, stamp))
        all_intervals.extend(intervals)
        first = min(first, items[0][0]) if first else items[0][0]
        last = max(last, items[-1][0]) if last else items[-1][0]
        name = next((name for _, name in reversed(items) if name), "")
        users.append({
            "actor_id": None if key == SHARED else key,
            "actor_name": name if key != SHARED else "",
            "actions": len(items),
            "minutes": _round_minutes(user_seconds),
            "active_days": len(days),
            "first_at": items[0][0].isoformat(),
            "last_at": items[-1][0].isoformat(),
            "months": [{"month": month, "actions": counts["actions"],
                        "minutes": _round_minutes(counts["seconds"])}
                       for month, counts in sorted(months.items(), reverse=True)],
        })
    users.sort(key=lambda user: (-user["minutes"], -user["actions"], user["actor_id"] or ""))
    system_seconds = _merge_seconds(all_intervals)
    person_seconds = sum((end - start).total_seconds() for start, end in all_intervals)
    return {
        "method": "paired_saves_15m",
        "idle_minutes": IDLE_SECONDS // 60,
        "system_minutes": _round_minutes(system_seconds),
        "person_minutes": _round_minutes(person_seconds),
        "actions": sum(len(items) for items in by_actor.values()),
        "active_days": len(all_days),
        "first_at": first.isoformat() if first else None,
        "last_at": last.isoformat() if last else None,
        "users": users,
        "months": [{"month": month, "actions": counts["actions"],
                    "minutes": _round_minutes(counts["seconds"])}
                   for month, counts in sorted(total_months.items(), reverse=True)],
    }
