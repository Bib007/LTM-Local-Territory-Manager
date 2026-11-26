"""Dual identifiers: synthetic-only migration, printing, concurrency and rollback."""
import concurrent.futures
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from store import Store
from territory_numbers import natural_key
from profile_policy import ACTIONS, state_for
from readable_export import tables


class TerritoryNumberTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.addCleanup(self.store.close)

    def card(self, public, internal="", area_id=""):
        return self.store.mutate("card.save", {
            "number": public, "internal_number": internal, "area_id": area_id,
            "temporary": True, "addresses": []
        })["id"]

    def area(self, name="Fiktivt område"):
        return self.store.mutate("area.save", {"name": name})["id"]

    def preview(self, **data):
        return self.store.mutate("card.numbering.preview", data)

    def apply(self, plan, **data):
        return self.store.mutate("card.numbering.apply", {
            **data, "expected": plan["expected"],
            "confirm": "BYT NUMRE" if data["mode"] == "swap" else "TILDEL NUMRE"
        })

    def scheme(self, area_id, prefix="T", start=25, end=30, width=4):
        args = {"area_id": area_id, "prefix": prefix, "start": start,
                "end": end, "width": width}
        plan = self.store.mutate("area.numbering.preview", args)
        self.store.mutate("area.numbering.save", {
            **args, "expected": plan["expected"], "confirm": "GEM INTERVAL"
        })

    def test_legacy_card_id_and_printed_number_are_stable_until_explicit_change(self):
        old = self.card("25")
        state = self.store.state()
        self.assertEqual(next(c for c in state["cards"] if c["id"] == old)["internal_number"], "")
        self.store.mutate("card.save", {**self.store.require("cards", old),
                                       "name": "Fiktivt distrikt"})
        self.assertEqual(self.store.require("cards", old)["number"], "25")
        self.assertEqual(self.store.require("cards", old)["internal_number"], "")
        # No startup/global operation backfills or renumbers existing territory cards.
        self.assertTrue(self.preview(scope="all", mode="swap")["conflicts"])

    def test_single_swap_preserves_related_loan_and_marks_both_print_sides(self):
        card_id = self.card("25", "T0025")
        publisher_id = self.store.mutate("publisher.save", {"name": "Fiktiv forkynder"})["id"]
        loan_id = self.store.mutate("loan.issue", {
            "card_id": card_id, "publisher_id": publisher_id,
            "date": date.today().isoformat(), "initial": True
        })["id"]
        previous_loans = self.store.all("loans")
        preview = self.preview(scope="card", mode="swap", card_id=card_id)
        self.assertFalse(preview["conflicts"])
        saved = self.apply(preview, scope="card", mode="swap", card_id=card_id)
        row = self.store.require("cards", card_id)
        self.assertEqual((row["id"], row["number"], row["internal_number"]),
                         (card_id, "T0025", "25"))
        self.assertTrue(row["front_revision"])
        self.assertTrue(row["back_revision"])
        self.assertEqual(self.store.all("loans"), previous_loans)
        self.assertEqual(self.store.require("loans", loan_id)["card_id"], card_id)
        self.assertEqual(self.store.state()["numbering_last_batch"]["id"], saved["batch_id"])

    def test_undo_durable_and_safe_after_restart(self):
        card_id = self.card("25", "T0025")
        plan = self.preview(scope="card", mode="swap", card_id=card_id)
        changed = self.apply(plan, scope="card", mode="swap", card_id=card_id)
        self.store.close()
        self.store = Store(self.temp.name)
        self.addCleanup(self.store.close)
        undo = self.store.mutate("card.numbering.undo.preview", {"batch_id": changed["batch_id"]})
        self.assertEqual(undo["conflicts"], [])
        self.store.mutate("card.numbering.undo", {
            "batch_id": changed["batch_id"], "expected": undo["expected"],
            "confirm": "FORTRYD NUMRE"
        })
        row = self.store.require("cards", card_id)
        self.assertEqual((row["number"], row["internal_number"]), ("25", "T0025"))
        self.assertIsNone(self.store.state()["numbering_last_batch"])
        with self.assertRaises(ValueError):
            self.store.mutate("card.numbering.undo", {
                "batch_id": changed["batch_id"], "expected": undo["expected"],
                "confirm": "FORTRYD NUMRE"
            })

    def test_scope_collision_and_atomic_two_card_exchange(self):
        a, b = self.card("25", "M0101"), self.card("M0101", "D0201")
        single = self.preview(scope="card", mode="swap", card_id=a)
        self.assertTrue(single["conflicts"])
        full = self.preview(scope="all", mode="swap")
        self.assertFalse(full["conflicts"])
        self.apply(full, scope="all", mode="swap")
        self.assertEqual(self.store.require("cards", a)["number"], "M0101")
        self.assertEqual(self.store.require("cards", b)["number"], "D0201")
        self.assertEqual(self.store.require("cards", a)["internal_number"], "25")
        self.assertEqual(self.store.require("cards", b)["internal_number"], "M0101")

    def test_missing_and_invalid_swap_inputs_are_read_only(self):
        a = self.card("25")
        b = self.card("B-26", "T0026")
        before = self.store.all("cards")
        self.assertTrue(self.preview(scope="card", mode="swap", card_id=a)["conflicts"])
        self.assertTrue(self.preview(scope="card", mode="swap", card_id=b)["conflicts"])
        self.assertEqual(self.store.all("cards"), before)

    def test_area_scheme_allocates_only_blank_codes_with_padded_zeros(self):
        rural = self.area("Fiktiv by")
        city = self.area("Fiktivt land")
        self.scheme(rural, prefix="T", start=25, end=28, width=4)
        a = self.card("10", area_id=rural)
        existing = self.card("20", "T0025", rural)
        second = self.card("11", area_id=rural)
        other = self.card("100", area_id=city)
        plan = self.preview(scope="area", mode="assign", area_id=rural)
        self.assertFalse(plan["conflicts"])
        self.assertEqual([x["after"]["internal_number"] for x in plan["changes"]],
                         ["T0026", "T0027"])
        self.apply(plan, scope="area", mode="assign", area_id=rural)
        self.assertEqual(self.store.require("cards", a)["internal_number"], "T0026")
        self.assertEqual(self.store.require("cards", second)["internal_number"], "T0027")
        self.assertEqual(self.store.require("cards", existing)["internal_number"], "T0025")
        self.assertEqual(self.store.require("cards", other).get("internal_number"), "")

    def test_preview_is_invalidated_by_concurrent_edit(self):
        card_id = self.card("25", "T0025")
        plan = self.preview(scope="all", mode="swap")
        self.store.mutate("card.save", {**self.store.require("cards", card_id),
                                       "name": "Andet fiktivt navn"})
        with self.assertRaisesRegex(ValueError, "Kontrollér forhåndsvisningen"):
            self.apply(plan, scope="all", mode="swap")
        self.assertEqual(self.store.require("cards", card_id)["number"], "25")

    def test_two_concurrent_confirmations_have_one_winner(self):
        card_id = self.card("25", "T0025")
        plan = self.preview(scope="all", mode="swap")
        def commit(_):
            try:
                return self.apply(plan, scope="all", mode="swap")
            except ValueError:
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(commit, (1,2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(self.store.require("cards", card_id)["number"], "T0025")

    def test_atomic_rollback_when_second_card_write_fails(self):
        a, b = self.card("25", "T0025"), self.card("26", "T0026")
        plan = self.preview(scope="all", mode="swap")
        before = self.store.all("cards")
        put = self.store.put
        calls = [0]
        def fail_second(module, row):
            if module == "cards":
                calls[0] += 1
                if calls[0] == 2:
                    raise RuntimeError("Fiktiv diskfejl")
            return put(module, row)
        with patch.object(self.store, "put", side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                self.apply(plan, scope="all", mode="swap")
        self.assertEqual(self.store.all("cards"), before)
        self.assertFalse(any(x.get("entity") == "territory-numbering-batch"
                             for x in self.store.all("settings")))

    def test_duplicate_internal_numbers_are_reserved_case_insensitively(self):
        a = self.card("25", "M0101")
        with self.assertRaisesRegex(ValueError, "interne nummer"):
            self.card("26", "m0101")
        self.assertEqual(self.store.require("cards", a)["internal_number"], "M0101")

    def test_number_sort_preserves_padding_as_tie_breaker(self):
        codes = ["T25", "T0101", "T0025", "M0101", "D0201", "T0009"]
        self.assertEqual(sorted(codes, key=natural_key),
                         ["D0201", "M0101", "T0009", "T25", "T0025", "T0101"])

    def test_export_keeps_technical_id_and_adds_internal_column(self):
        ident = self.card("25", "T0025")
        csv_data = tables(self.store.state(), [])["CSV/kort.csv"].decode("utf-8-sig")
        self.assertIn("kort_id;kortnummer;", csv_data)
        self.assertIn("internt_nummer", csv_data)
        self.assertIn(ident, csv_data)
        self.assertIn("T0025", csv_data)
        # Both PDF card sides and S-13 continue reading the legacy/public 'number'.

    def test_s12_s13_and_qr_retain_identity_and_follow_public_number(self):
        from pdf_export import allocation_rows, s13_pdf
        from sharing import Publications, fingerprint
        year = date.today().year + 1
        ident = self.card("25", "T0025")
        before = self.store.state()
        saved = next(c for c in before["cards"] if c["id"] == ident)
        self.assertEqual(allocation_rows(before, year)[0]["number"], "25")
        with self.store.transaction():
            self.store.put("maps", {
                "id": "publication:" + ident, "entity": "publication",
                "card_id": ident, "status": "published",
                "url": "https://drive.google.com/file/d/TEST_FICTIONAL/view",
                "fingerprint": fingerprint(self.store, saved)
            })
        original_qr = Publications(self.store).qr(ident)
        self.assertIn(b"<svg", original_qr)
        plan = self.preview(scope="card", mode="swap", card_id=ident)
        self.apply(plan, scope="card", mode="swap", card_id=ident)
        after = self.store.state()
        updated = next(c for c in after["cards"] if c["id"] == ident)
        self.assertEqual(allocation_rows(after, year)[0]["number"], "T0025")
        self.assertEqual(updated["id"], saved["id"])
        self.assertNotEqual(updated["front_print_token"], saved["front_print_token"])
        self.assertNotEqual(updated["back_print_token"], saved["back_print_token"])
        self.assertNotEqual(fingerprint(self.store, updated), fingerprint(self.store, saved))
        # Pre-existing public URLs and QR artifacts are not destroyed by a rename.
        self.assertEqual(Publications(self.store).qr(ident), original_qr)
        with self.assertRaisesRegex(ValueError, "Publicér igen"):
            Publications(self.store).qr(ident, require_current=True)
        self.assertTrue(s13_pdf(after, year).startswith(b"%PDF"))

    def test_roles_require_edit_rights_and_area_policy(self):
        self.assertIn("cards.edit", ACTIONS["card.numbering.apply"])
        self.assertIn("cards.edit", ACTIONS["card.numbering.undo"])
        self.assertIn("settings.manage", ACTIONS["area.numbering.save"])


if __name__ == "__main__":
    unittest.main()
