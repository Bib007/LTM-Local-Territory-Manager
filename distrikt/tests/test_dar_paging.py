"""Fictional GraphQL pages only; no credentials, network or local card data."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from dar_paging import collect_pages, IncompleteResult

ENTITY = 'DAR_Adresse'


def page(ids=(), more=False, cursor=None):
    return {'data': {ENTITY: {
        'nodes': [{'id_lokalId': value, 'adressebetegnelse': 'Fiktivvej 1'} for value in ids],
        'pageInfo': {'hasNextPage': more, 'endCursor': cursor}}}}


class PagingTests(unittest.TestCase):
    def test_complete_pages_keep_order_and_forward_opaque_cursor(self):
        fetch = Mock(side_effect=[page(['a', 'b'], True, 'opaque+/='),
                                  page(['c'], False, 'last')])
        self.assertEqual([n['id_lokalId'] for n in collect_pages(fetch, ENTITY)], ['a', 'b', 'c'])
        self.assertEqual([call.args for call in fetch.call_args_list], [(None,), ('opaque+/=',)])

    def test_empty_complete_result_and_empty_terminal_page(self):
        self.assertEqual(collect_pages(lambda _: page(), ENTITY), [])
        fetch = Mock(side_effect=[page(['a'], True, 'next'), page()])
        self.assertEqual(len(collect_pages(fetch, ENTITY)), 1)

    def test_partial_data_with_provider_error_never_accepted_or_echoed(self):
        reply = page(['a'], False, 'last')
        reply['errors'] = [{'message': 'FICTIONAL_SECRET https://fake.invalid'}]
        with self.assertRaises(IncompleteResult) as error:
            collect_pages(lambda _: reply, ENTITY)
        self.assertNotIn('FICTIONAL_SECRET', str(error.exception))
        self.assertNotIn('fake.invalid', str(error.exception))

    def test_missing_connection_nodes_and_page_info(self):
        for reply in (None, [], {}, {'data': None}, {'data': {}},
                      {'data': {ENTITY: None}}, {'data': {ENTITY: {}}}):
            with self.subTest(reply=reply), self.assertRaises(IncompleteResult):
                collect_pages(lambda _: reply, ENTITY)
        for nodes, info in ((None, {}), ({}, {}), ([], None), ([], {}),
                            ([], {'hasNextPage': 'false'}), ([], {'hasNextPage': 0})):
            reply = {'data': {ENTITY: {'nodes': nodes, 'pageInfo': info}}}
            with self.subTest(nodes=nodes, info=info), self.assertRaises(IncompleteResult):
                collect_pages(lambda _: reply, ENTITY)

    def test_missing_invalid_or_empty_progress(self):
        for ids, more, cursor in ((['a'], True, None), (['a'], False, None),
                                  (['a'], True, 5), (['a'], True, ' '),
                                  ([], True, 'next'), ([], False, [])):
            with self.subTest(ids=ids, more=more, cursor=cursor), self.assertRaises(IncompleteResult):
                collect_pages(lambda _: page(ids, more, cursor), ENTITY)

    def test_cursor_cycle_is_rejected_even_with_new_ids(self):
        for terminal in (True, False):
            fetch = Mock(side_effect=[page(['a'], True, 'one'), page(['b'], True, 'two'),
                                      page(['c'], terminal, 'one')])
            with self.subTest(terminal=terminal), self.assertRaises(IncompleteResult):
                collect_pages(fetch, ENTITY)
            self.assertEqual(fetch.call_count, 3)

    def test_duplicate_ids_on_same_or_later_page_are_rejected(self):
        for pages in ([page(['a', 'a'], False, 'last')],
                      [page(['a'], True, 'one'), page(['a'], False, 'two')]):
            with self.subTest(pages=pages), self.assertRaises(IncompleteResult):
                collect_pages(Mock(side_effect=pages), ENTITY)

    def test_missing_or_invalid_identity_is_rejected(self):
        for node in (None, [], {}, {'id_lokalId': None}, {'id_lokalId': 1}, {'id_lokalId': ' '}):
            reply = page(['a'], False, 'last')
            reply['data'][ENTITY]['nodes'] = [node]
            with self.subTest(node=node), self.assertRaises(IncompleteResult):
                collect_pages(lambda _: reply, ENTITY)

    def test_bounds_fail_instead_of_truncating(self):
        fetch = Mock(return_value=page(['a'], True, 'one'))
        with self.assertRaises(IncompleteResult):
            collect_pages(fetch, ENTITY, max_pages=1)
        self.assertEqual(fetch.call_count, 1)
        with self.assertRaises(IncompleteResult):
            collect_pages(lambda _: page(['a', 'b'], False, 'last'), ENTITY, max_nodes=1)
        self.assertEqual(len(collect_pages(lambda _: page(['a'], False, 'last'),
                                          ENTITY, max_pages=1, max_nodes=1)), 1)

    def test_invalid_bounds_never_fetch(self):
        fetch = Mock()
        for option in ('max_pages', 'max_nodes'):
            for value in (0, -1, True, 1.5, None):
                with self.subTest(option=option, value=value), self.assertRaises(ValueError):
                    collect_pages(fetch, ENTITY, **{option: value})
        fetch.assert_not_called()

    def test_cancel_before_request_or_after_response_returns_no_result(self):
        class Cancelled(Exception):
            pass
        for checks in ([Cancelled()], [None, Cancelled()], [None, None, Cancelled()]):
            fetch = Mock(return_value=page(['a'], True, 'one'))
            with self.subTest(checks=len(checks)), self.assertRaises(Cancelled):
                collect_pages(fetch, ENTITY, check_cancel=Mock(side_effect=checks))
            self.assertLessEqual(fetch.call_count, 1)

    def test_transport_failure_after_first_page_does_not_return_partial_data(self):
        fetch = Mock(side_effect=[page(['a'], True, 'one'), TimeoutError('fictional transport')])
        with self.assertRaises(TimeoutError):
            collect_pages(fetch, ENTITY)


if __name__ == '__main__':
    unittest.main()
