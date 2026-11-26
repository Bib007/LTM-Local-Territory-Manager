"""#97: geo cache invalidation must follow geo_state inputs only. Fictional SQLite."""
import json
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from store import Store
from server import Server


def fictional_address(ident, number, longitude):
    return {"id": ident, "entity": "address", "road": "Fiktivvej",
            "number": number, "postcode": "9999", "floor": "", "door": "",
            "count": 1, "lat": 55.5, "lng": longitude, "label": "Fiktivvej " + number}


class GeoCacheTransactionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ltm-geo-cache-fictional-")
        self.s = Store(self.tmp.name)
        with self.s.transaction():
            self.s.put("geo", fictional_address("fictional-a", "1", 9.5))
            self.s.put("geo", fictional_address("fictional-b", "3", 9.501))
        self.card = self.s.mutate("card.save", {"number": "F101", "temporary": True})["id"]
        with self.s.transaction():
            c = self.s.require("cards", self.card)
            c["address_ids"] = ["fictional-a"]
            c["geo_polygon"] = [[9.499, 55.499], [9.502, 55.499],
                                [9.502, 55.502], [9.499, 55.502]]
            self.s.put("cards", c)
        self.s.geo_state()

    def tearDown(self):
        self.s.close()
        self.tmp.cleanup()

    def unchanged(self, operation):
        before = self.s.geo_state()
        generation = self.s.geo_generation
        revision = self.s.revision
        operation()
        self.assertNotEqual(self.s.revision, revision, "Committed records still advance revision")
        self.assertEqual(self.s.geo_generation, generation)
        self.assertIs(self.s.geo_state(), before, "A valid cache must be reused, not rebuilt")

    def changed(self, operation):
        before = self.s.geo_state()
        generation = self.s.geo_generation
        operation()
        self.assertEqual(self.s.geo_generation, generation + 1)
        self.assertIsNot(self.s.geo_state(), before)

    def edit(self, **fields):
        with self.s.transaction():
            c = self.s.require("cards", self.card)
            c.update(fields)
            self.s.put("cards", c)

    def test_name_color_and_physical_location_do_not_reload_geo(self):
        self.unchanged(lambda: self.edit(name="Fiktivt navn"))
        self.unchanged(lambda: self.s.mutate("card.color", {
            "card_id": self.card, "map_color": "#aabbcc"}))
        self.unchanged(lambda: self.edit(in_folder=True, last_completed="2026-01-01"))
        self.assertEqual(self.s.geo_state()["status"]["fictional-a"]["card_id"], self.card)

    def test_loan_issue_and_finish_with_or_without_completion_keep_cache(self):
        publisher = self.s.mutate("publisher.save", {"name": "Fiktiv person"})["id"]
        day = date.today().isoformat()
        for complete in (False, True):
            self.unchanged(lambda: self.s.mutate("loan.issue", {
                "card_id": self.card, "publisher_id": publisher,
                "date": day, "initial": True}))
            loan = self.s.active_loan(self.card)["id"]
            self.unchanged(lambda: self.s.mutate("loan.finish", {
                "id": loan, "date": day, "complete": complete,
                "retain": False, "revise_ib": complete}))
        self.assertEqual(len(self.s.all("loans")), 2)
        self.assertEqual(len(self.s.all("completions")), 1)
        self.assertEqual(self.s.geo_state()["status"]["fictional-a"]["card_id"], self.card)

    def test_boundary_report_reuses_cache_after_issue_and_return(self):
        polygon=[[9.49,55.49],[9.52,55.49],[9.52,55.52],[9.49,55.52]]
        with self.s.transaction():
            self.s.put('geo',{'id':'main-boundary','entity':'main-boundary','points':polygon})
        local=fictional_address('fictional-local','7',9.503)
        self.edit(geo_addresses=[local])
        baseline=self.s.boundary_report()
        self.assertEqual(baseline['visits'],3)
        person=self.s.mutate('publisher.save',{'name':'Fiktiv person'})['id']
        day=date.today().isoformat()
        loan=self.s.mutate('loan.issue',{'card_id':self.card,'publisher_id':person,
                                        'date':day,'initial':True})['id']
        self.assertIs(self.s.boundary_report(),baseline)
        self.s.mutate('loan.finish',{'id':loan,'date':day,'complete':True})
        self.assertIs(self.s.boundary_report(),baseline)
        self.edit(geo_addresses=[{**local,'count':4}])
        recalculated=self.s.boundary_report()
        self.assertIsNot(recalculated,baseline)
        self.assertEqual(recalculated['visits'],6)
        self.edit(address_ids=[])
        self.assertIsNot(self.s.boundary_report(),recalculated)

    def test_loan_finish_plus_relevant_geometry_in_same_transaction_invalidates(self):
        publisher = self.s.mutate("publisher.save", {"name": "Fiktiv person"})["id"]
        day = date.today().isoformat()
        loan = self.s.mutate("loan.issue", {"card_id": self.card,
            "publisher_id": publisher, "date": day, "initial": True})["id"]
        def combined():
            with self.s.transaction():
                self.s._mutate("loan.finish", {"id": loan, "date": day,
                                               "complete": False, "retain": False})
                c = self.s.require("cards", self.card)
                c["geo_polygon"] = [[9.0, 55.0], [9.2, 55.0], [9.2, 55.2]]
                self.s.put("cards", c)
        self.changed(combined)
        self.assertEqual(self.s.geo_state()["status"]["fictional-b"]["within"], [])
        self.assertIsNotNone(self.s.get("loans", loan)["returned"])

    def test_all_geo_state_card_inputs_invalidate(self):
        self.changed(lambda: self.edit(number="F102"))
        self.assertEqual(self.s.geo_state()["status"]["fictional-a"]["card_number"], "F102")
        self.changed(lambda: self.edit(address_ids=["fictional-b"]))
        self.assertEqual(self.s.geo_state()["status"]["fictional-b"]["card_id"], self.card)
        self.changed(lambda: self.edit(geo_polygon=[[9, 55], [10, 55], [10, 56]]))
        # Legacy ownership is keyed by postcode/road/number/floor/door.
        self.changed(lambda: self.edit(geo_addresses=[{
            "postcode": "9999", "road": "Fiktivvej", "number": "1",
            "floor": "", "door": "", "count": 1, "lat": 55.5, "lng": 9.5}]))
        self.assertEqual(self.s.geo_state()["status"]["fictional-a"]["card_id"], self.card)
        self.unchanged(lambda: self.edit(geo_addresses=[{
            "postcode": "9999", "road": "FIKTIVVEJ", "number": "1",
            "floor": "", "door": "", "count": 9, "lat": 55.9, "lng": 9.9}]))
        self.changed(lambda: self.edit(geo_addresses=[]))
        self.changed(lambda: self.edit(archived=True))
        self.assertNotIn("card_id", self.s.geo_state()["status"]["fictional-b"])
        self.changed(lambda: self.edit(archived=False))
        self.assertEqual(self.s.geo_state()["status"]["fictional-b"]["card_id"], self.card)

    def test_deleted_and_recovered_cards_change_owner_and_cache(self):
        deleted = []
        def remove():
            deleted.append(self.s.mutate("delete", {"module": "cards", "id": self.card})["batch"])
        self.changed(remove)
        self.assertNotIn("card_id", self.s.geo_state()["status"]["fictional-a"])
        self.changed(lambda: self.s.mutate("restore", {"batch": deleted[0]}))
        self.assertEqual(self.s.geo_state()["status"]["fictional-a"]["card_id"], self.card)

    def test_direct_sql_and_mixed_sql_are_fail_closed(self):
        def raw_name():
            with self.s.transaction():
                c = self.s.require("cards", self.card)
                c["name"] = "Direkte SQL"
                self.s.db.execute("UPDATE cards.records SET payload=? WHERE id=?",
                    (json.dumps(c), self.card))
        self.changed(raw_name)
        def mixed_sql():
            with self.s.transaction():
                self.s.put("notes", {"id": "fictional-note", "text": "Test"})
                c = self.s.require("cards", self.card)
                c["name"] = "Ukendt ændring"
                self.s.db.execute("UPDATE cards.records SET payload=? WHERE id=?",
                    (json.dumps(c), self.card))
        self.changed(mixed_sql)
        def raw_geo():
            with self.s.transaction():
                row = fictional_address("fictional-extra", "9", 9.509)
                self.s.db.execute("INSERT INTO geo.records (id,payload) VALUES (?,?)",
                    (row["id"], json.dumps(row)))
        self.changed(raw_geo)
        self.assertIn("fictional-extra", self.s.geo_state()["status"])
        # Even an untracked geo SQL write mixed with a tracked note must clear
        # ancillary geo_info(), not only the top-level geo_state cache.
        def mixed_raw_geo():
            with self.s.transaction():
                self.s.put("notes", {"id": "fictional-note-2", "text": "Fiktiv"})
                row = fictional_address("fictional-mixed-extra", "11", 9.511)
                self.s.db.execute("INSERT INTO geo.records (id,payload) VALUES (?,?)",
                    (row["id"], json.dumps(row)))
        self.changed(mixed_raw_geo)
        self.assertEqual(self.s.geo_state()["info"]["addresses"], 4)

    def test_rollback_does_not_invalidate_or_leak_preimages(self):
        original = self.s.geo_state()
        generation = self.s.geo_generation
        revision = self.s.revision
        with self.assertRaisesRegex(RuntimeError, "rollback"):
            with self.s.transaction():
                c = self.s.require("cards", self.card)
                c["address_ids"] = []
                self.s.put("cards", c)
                raise RuntimeError("rollback")
        self.assertIs(self.s.geo_state(), original)
        self.assertEqual(self.s.geo_generation, generation)
        self.assertEqual(self.s.revision, revision)
        self.assertEqual(self.s.get("cards", self.card)["address_ids"], ["fictional-a"])
        self.unchanged(lambda: self.edit(name="Efter rollback"))

    def test_undo_falls_back_for_unaccounted_sql(self):
        self.s.mutate("card.color", {"card_id": self.card, "map_color": "#123456"})
        self.changed(lambda: self.s.mutate("workflow.undo", {}))
        self.assertEqual(self.s.get("cards", self.card)["map_color"], "#477596")

    def test_sqlite_durability_and_unchanged_cache_are_separate(self):
        self.unchanged(lambda: self.edit(name="Bevaret efter genåbning"))
        self.s.close()
        self.s = Store(self.tmp.name)
        self.assertEqual(self.s.get("cards", self.card)["name"], "Bevaret efter genåbning")
        self.assertEqual(self.s.geo_state()["status"]["fictional-a"]["card_id"], self.card)

    def test_serialized_concurrent_writers_still_invalidate_relevant_write(self):
        def name():
            self.s.mutate("card.color", {"card_id": self.card, "map_color": "#aabbcc"})
        def geo():
            self.edit(address_ids=["fictional-b"])
        with ThreadPoolExecutor(max_workers=2) as executor:
            a, b = executor.submit(name), executor.submit(geo)
            a.result(timeout=10)
            b.result(timeout=10)
        self.assertEqual(self.s.geo_state()["status"]["fictional-b"]["card_id"], self.card)


class GeoCacheHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ltm-geo-http-fictional-")
        self.store = Store(self.tmp.name)
        self.server = Server(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.store.close()
        self.tmp.cleanup()

    def change(self, action, data):
        import urllib.request
        request = urllib.request.Request(
            self.server.origin + "/api/mutate",
            data=json.dumps({"action": action, "data": data}).encode("utf8"),
            headers={"X-Distrikt-Token": self.server.token, "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)

    def test_preview_without_profiles_releases_locks_on_failure(self):
        import urllib.request
        import urllib.error
        from unittest.mock import patch
        self.change('geo.import',{'records':[fictional_address('f1','1',10)],'source':'Test','label':'Fiktiv'})
        before=self.store.revision
        entered=threading.Event();release=threading.Event()
        def held(*args):
            entered.set()
            if not release.wait(5):raise RuntimeError('Preview not released')
            raise ValueError('Fiktiv afvisning')
        with patch('geo_store.suggest_outline',held),ThreadPoolExecutor() as pool:
            pending=pool.submit(self.change,'geo.preview',{'address_ids':['f1'],'suggest_outline':True})
            try:
                self.assertTrue(entered.wait(2))
                request=urllib.request.Request(self.server.origin+'/api/state',headers={'X-Distrikt-Token':self.server.token})
                with urllib.request.urlopen(request,timeout=2) as response:self.assertEqual(response.status,200)
                # Neither global lock nor a write transaction survives capture.
                self.assertFalse(self.store.db.in_transaction)
                with self.server.accounts.lock,self.store.lock:self.assertEqual(self.store.revision,before)
            finally:release.set()
            with self.assertRaises(urllib.error.HTTPError) as error:pending.result(timeout=2)
            self.assertEqual(error.exception.code,400)
        self.assertEqual(self.store.revision,before)
        self.assertEqual(len(self.change('geo.preview',{'address_ids':['f1']})['result']['addresses']),1)

    def test_late_preview_response_does_not_hold_global_locks(self):
        import urllib.request
        from http.client import RemoteDisconnected
        from unittest.mock import patch
        handler=self.server.RequestHandlerClass;original=handler.send
        entered=threading.Event();release=threading.Event()
        def delayed(request,data,*args,**kwargs):
            if request.path=='/api/mutate' and isinstance(data,dict) and 'result' in data:
                entered.set()
                if not release.wait(5):raise RuntimeError('Response not released')
                # Model a disconnected client after a late calculation.
                raise BrokenPipeError()
            return original(request,data,*args,**kwargs)
        with patch.object(handler,'send',delayed),ThreadPoolExecutor() as pool:
            pending=pool.submit(self.change,'geo.preview',{'address_ids':[]})
            try:
                self.assertTrue(entered.wait(2))
                request=urllib.request.Request(self.server.origin+'/api/state',headers={'X-Distrikt-Token':self.server.token})
                with urllib.request.urlopen(request,timeout=2) as response:self.assertEqual(response.status,200)
            finally:release.set()
            with self.assertRaises(RemoteDisconnected):pending.result(timeout=2)
        self.assertEqual(self.change('geo.preview',{'address_ids':[]})['result']['addresses'],[])

    def test_geo_changed_receipts_follow_actual_changes(self):
        new = self.change("card.save", {"number": "F401", "temporary": True})
        self.assertTrue(new["geo_changed"])
        ident = new["result"]["id"]
        with self.store.lock:
            self.store.geo_state()
        self.assertFalse(self.change("card.color", {"card_id": ident, "map_color": "#aabbcc"})["geo_changed"])
        self.assertFalse(self.change("card.save", {"id": ident, "number": "F401",
            "name": "Fiktivt navn", "temporary": True})["geo_changed"])
        day = date.today().isoformat()
        self.assertFalse(self.change("loan.issue", {"card_id": ident,
            "publisher_name": "Fiktiv person", "date": day, "initial": True})["geo_changed"])
        loan = self.store.active_loan(ident)["id"]
        self.assertFalse(self.change("loan.finish", {"id": loan, "date": day,
            "complete": True, "retain": False, "revise_ib": True})["geo_changed"])
        self.assertTrue(self.change("geo.boundary", {"card_id": ident, "polygon": [
            [9.49, 55.49], [9.51, 55.49], [9.50, 55.51]]})["geo_changed"])
        self.assertTrue(self.change("card.save", {"id": ident, "number": "F402",
            "name": "Fiktivt navn", "temporary": True})["geo_changed"])


if __name__ == "__main__":
    unittest.main()
