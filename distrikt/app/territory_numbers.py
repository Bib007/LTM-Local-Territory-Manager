"""Explicit, atomic dual territory-number operations.

The immutable cards.id is the only relational key. cards.number remains the
legacy/public printed number; internal_number never becomes a foreign key.
Operations run inside Store.guarded_mutate's BEGIN IMMEDIATE transaction.
"""
import hashlib
import json
import re

INTERNAL = re.compile(r"[A-Z0-9]{1,30}\Z")
PREFIX = re.compile(r"[A-Z]{0,10}\Z")


def internal_code(value):
    if value is None or value == "":
        return ""
    if not isinstance(value, str):
        raise ValueError("Internt nummer skal være tekst.")
    value = value.strip().upper()
    if not INTERNAL.fullmatch(value):
        raise ValueError("Internt nummer skal bestå af 1–30 bogstaver (A–Z) og tal (0–9).")
    return value


def natural_key(value):
    """Numeric components sort numerically; leading zeroes remain significant text."""
    value = str(value or "")
    return tuple((1, int(part), len(part), part) if part.isdecimal()
                 else (0, part.casefold()) for part in re.findall(r"\d+|\D+", value))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def scheme_values(data):
    prefix = data.get("prefix", "")
    if not isinstance(prefix, str) or not PREFIX.fullmatch(prefix.upper()):
        raise ValueError("Præfikset må højst være 10 bogstaver (A–Z).")
    result = {"prefix": prefix.upper()}
    for field, maximum in (("start", 999999999), ("end", 999999999), ("width", 20)):
        value = data.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, str)) or not re.fullmatch(r"\d{1,9}", str(value)):
            raise ValueError("Start, slut og bredde skal være hele, positive tal.")
        value = int(value)
        if value > maximum:
            raise ValueError("Nummerintervallet er for stort.")
        result[field] = value
    if result["start"] > result["end"] or result["width"] < 1:
        raise ValueError("Start må ikke være efter slut, og bredde skal være mindst 1.")
    if len(result["prefix"]) + max(result["width"], len(str(result["end"]))) > 30:
        raise ValueError("Det interne nummer må højst være 30 tegn.")
    return result


def collisions(active, deleted, changes):
    """Check both complete final namespaces, including reserved deleted cards."""
    planned = {c["id"]: c for c in changes}
    seen = {"number": {}, "internal_number": {}}
    errors = []
    for card in active + deleted:
        row = planned.get(card["id"], {})
        for field, label in (("number", "Offentligt"), ("internal_number", "Internt")):
            value = row.get(field, card.get(field, ""))
            if not value:
                if field == "number":
                    errors.append("Et kort mangler offentligt nummer.")
                continue
            key = str(value).casefold()
            old = seen[field].setdefault(key, card["id"])
            if old != card["id"]:
                errors.append(label + " nummer " + str(value) + " bruges allerede af et andet kort.")
    return sorted(set(errors))


class TerritoryNumbering:
    def numbering_area(self, action, data):
        area = self.require("settings", data.get("area_id"))
        if area.get("entity") or area["id"] == "config":
            raise ValueError("Vælg et gyldigt område.")
        previous = area.get("numbering") or {}
        values = scheme_values(data)
        expected = digest({"area_id": area["id"], "numbering": previous})
        response = {"expected": expected, "before": previous, "after": values}
        if action.endswith(".preview"):
            return response
        if data.get("expected") != expected or data.get("confirm") != "GEM INTERVAL":
            raise ValueError("Området blev ændret. Kontrollér intervallet og bekræft igen.")
        self.put("settings", dict(area, numbering=values))
        return {"area_id": area["id"]}

    def numbering_plan(self, data):
        scope, mode = data.get("scope"), data.get("mode")
        if scope not in ("card", "area", "all") or mode not in ("swap", "assign"):
            raise ValueError("Vælg enkeltkort, område eller alle kort samt en handling.")
        cards = self.all("cards")
        deleted = self.all("cards", deleted=True)
        if scope == "card":
            selected = [self.require("cards", data.get("card_id"))]
        elif scope == "area":
            area = self.require("settings", data.get("area_id"))
            if area.get("entity") or area["id"] == "config":
                raise ValueError("Vælg et gyldigt område.")
            selected = [c for c in cards if c.get("area_id") == area["id"]]
        else:
            selected = cards[:]
        if not selected:
            raise ValueError("Ingen kort er valgt.")
        selected.sort(key=lambda c: (natural_key(c["number"]), c["id"]))
        errors, candidates = [], {}
        if mode == "assign":
            used = {str(c.get("internal_number", "")).casefold()
                    for c in cards + deleted if c.get("internal_number")}
            for card in selected:
                if card.get("internal_number"):
                    continue
                area = self.get("settings", card.get("area_id"))
                config = (area or {}).get("numbering")
                if not config:
                    errors.append("Intet internt nummerinterval for området på kort " + card["number"] + ".")
                    continue
                config = scheme_values(config)
                candidate = ""
                # At most len(used)+1 candidates are needed to locate a free value.
                # Never iterate across a billion-number sparse interval.
                last = min(config["end"], config["start"] + len(used))
                for n in range(config["start"], last + 1):
                    value = config["prefix"] + str(n).zfill(config["width"])
                    if value.casefold() not in used:
                        candidate = value
                        used.add(value.casefold())
                        break
                if not candidate:
                    errors.append("Ingen ledige interne numre til kort " + card["number"] + ".")
                else:
                    candidates[card["id"]] = (card["number"], candidate)
        else:
            for card in selected:
                old_internal = card.get("internal_number", "")
                if not old_internal:
                    errors.append("Kort " + card["number"] + " mangler internt nummer.")
                    continue
                try:
                    swapped_internal = internal_code(card["number"])
                except ValueError:
                    errors.append("Offentligt nummer " + card["number"] + " kan ikke bruges som internt nummer.")
                    continue
                candidates[card["id"]] = (old_internal, swapped_internal)
        changes = []
        for card in selected:
            if card["id"] not in candidates:
                continue
            public, internal = candidates[card["id"]]
            if card["number"] == public and card.get("internal_number", "") == internal:
                continue
            changes.append({"id": card["id"], "area_id": card.get("area_id", ""),
                            "before": {"number": card["number"], "internal_number": card.get("internal_number", "")},
                            "after": {"number": public, "internal_number": internal}})
        proposed = [{"id": c["id"], **c["after"]} for c in changes]
        errors += collisions(cards, deleted, proposed)
        # Hash *all* card content and numbering settings. A concurrent edit,
        # delete, restore or new card always invalidates the confirmation.
        areas = [a for a in self.all("settings") if not a.get("entity")]
        expected = digest({"data": {k: data.get(k) for k in ("scope", "mode", "card_id", "area_id")},
                           "cards": cards, "deleted": deleted, "areas": areas})
        return {"changes": changes, "conflicts": sorted(set(errors)), "expected": expected,
                "selected": len(selected), "scope": scope, "mode": mode}

    def numbering_undo(self, action, data):
        batch = self.require("settings", data.get("batch_id"))
        if batch.get("entity") != "territory-numbering-batch" or batch.get("undone_at"):
            raise ValueError("Denne nummerændring kan ikke fortrydes.")
        changes = batch["changes"]
        errors = []
        for entry in changes:
            card = self.get("cards", entry["id"])
            if not card or any(card.get(k, "") != v for k, v in entry["after"].items()):
                errors.append("Kort " + entry["before"]["number"] + " er ændret siden nummerbyttet.")
        cards = self.all("cards")
        before = [{"id": e["id"], **e["before"]} for e in changes]
        errors += collisions(cards, self.all("cards", deleted=True), before)
        expected = digest([self.get("cards", e["id"]) for e in changes])
        response = {"changes": changes, "conflicts": sorted(set(errors)), "expected": expected}
        if action.endswith(".preview"):
            return response
        if errors or data.get("expected") != expected or data.get("confirm") != "FORTRYD NUMRE":
            raise ValueError("Fortrydelse er ikke længere sikker. Kontrollér ændringerne igen.")
        from store import now
        for entry in changes:
            card = self.require("cards", entry["id"])
            card.update(entry["before"])
            if entry["before"]["number"] != entry["after"]["number"]:
                card["front_revision"] = card["back_revision"] = True
            self.put("cards", card)
        self.put("settings", dict(batch, undone_at=now()))
        return {"undone": len(changes)}

    def numbering_mutate(self, action, data):
        if action.startswith("area.numbering."):
            return self.numbering_area(action, data)
        if action in ("card.numbering.undo.preview", "card.numbering.undo"):
            return self.numbering_undo(action, data)
        if action not in ("card.numbering.preview", "card.numbering.apply"):
            raise ValueError("Ukendt nummerhandling.")
        plan = self.numbering_plan(data)
        if action.endswith(".preview"):
            return plan
        confirmation = "BYT NUMRE" if plan["mode"] == "swap" else "TILDEL NUMRE"
        if plan["conflicts"] or not plan["changes"] or data.get("expected") != plan["expected"] or data.get("confirm") != confirmation:
            raise ValueError("Numrene blev ændret, er i konflikt, eller mangler bekræftelse. Kontrollér forhåndsvisningen igen.")
        from store import new_id, now
        batch_id = "numbering-" + new_id()
        # Durable, local targeted recovery snapshot; no file or foreign keys move.
        self.put("settings", {"id": batch_id, "entity": "territory-numbering-batch",
                              "created": now(), "mode": plan["mode"], "scope": plan["scope"],
                              "changes": plan["changes"]})
        for entry in plan["changes"]:
            card = self.require("cards", entry["id"])
            card.update(entry["after"])
            if entry["before"]["number"] != entry["after"]["number"]:
                card["front_revision"] = card["back_revision"] = True
            self.put("cards", card)
        return {"count": len(plan["changes"]), "batch_id": batch_id}
