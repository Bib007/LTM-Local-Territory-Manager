"""Synthetic-only checks for the release version policy. No user/repo data read."""
import unittest

from version_policy import parse,next_version,validate,tagged_versions


class VersionPolicyTests(unittest.TestCase):
    def test_exact_version_grammar_and_semantic_order(self):
        self.assertEqual(str(parse("1.12.36-beta.1")),"1.12.36-beta.1")
        self.assertEqual(parse("1.13.0").base,(1,13,0))
        for bad in ("v1.12.36","1.12","1.12.36-beta.0","01.12.36","1.12.36-rc.1","1.12.36-beta.-1"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):parse(bad)

    def test_next_baselines_and_beta_reset(self):
        self.assertEqual(str(next_version(parse("1.12.35"),"fix")),"1.12.36-beta.1")
        self.assertEqual(str(next_version(parse("1.12.35"),"feature")),"1.13.0-beta.1")
        self.assertEqual(str(next_version(parse("1.12.35"),"breaking")),"2.0.0-beta.1")

    def test_beta_fresh_and_second_iteration(self):
        old=["v1.12.34","v1.12.19-beta.37"]
        self.assertEqual(str(validate("beta","1.12.36-beta.1","1.12.35",old,{},"newsha")),"1.12.36-beta.1")
        old+=["v1.12.36-beta.1"]
        self.assertEqual(str(validate("beta","1.12.36-beta.2","1.12.35",old,{},"newsha")),"1.12.36-beta.2")
        with self.assertRaisesRegex(ValueError,"exactly one"):
            validate("beta","1.12.36-beta.4","1.12.35",old,{},"newsha")

    def test_beta_cannot_use_stable_number_or_skip_base(self):
        for candidate in ("1.12.35-beta.1","1.12.37-beta.1","1.12.19-beta.38","1.14.0-beta.1"):
            with self.subTest(candidate=candidate),self.assertRaisesRegex(ValueError,"next fix"):
                validate("beta",candidate,"1.12.35",[],{},"sha")
        with self.assertRaisesRegex(ValueError,"Beta must use"):
            validate("beta","1.12.36","1.12.35",[],{},"sha")
        with self.assertRaisesRegex(ValueError,"missing the latest main"):
            validate("beta","1.12.36-beta.1","1.12.35",[],{},"sha",main_synced=False)

    def test_beta_must_not_move_backwards(self):
        tags=["v1.12.36-beta.1","v1.13.0-beta.1"]
        with self.assertRaisesRegex(ValueError,"newer version base"):
            validate("beta","1.12.36-beta.2","1.12.35",tags,{},"sha")

    def test_tagged_release_must_use_same_commit(self):
        tags=["v1.12.34","v1.12.36-beta.1"]
        with self.assertRaisesRegex(ValueError,"different code"):
            validate("beta","1.12.36-beta.1","1.12.35",tags,{"v1.12.36-beta.1":"wrong"},"new")
        self.assertEqual(str(validate("beta","1.12.36-beta.1","1.12.35",tags,{"v1.12.36-beta.1":"same"},"same")),"1.12.36-beta.1")

    def test_stable_same_base_as_beta(self):
        tags=["v1.12.35","v1.12.36-beta.1","v1.12.36-beta.2"]
        self.assertEqual(str(validate("stable","1.12.36","1.12.36",tags,{},"sha")),"1.12.36")
        with self.assertRaisesRegex(ValueError,"latest Beta source"):
            validate("stable","1.12.36","1.12.36",tags,{},"sha",source_matches=False)
        with self.assertRaisesRegex(ValueError,"published Beta"):
            validate("stable","1.12.36","1.12.36",["v1.12.35"],{},"sha")

    def test_stable_bump_and_branch_correctness(self):
        tags=["v1.12.35","v1.13.0-beta.1"]
        self.assertEqual(str(validate("stable","1.13.0","1.13.0",tags,{},"sha")),"1.13.0")
        with self.assertRaisesRegex(ValueError,"increment patch"):
            validate("stable","1.12.37","1.12.37",tags+["v1.12.37-beta.1"],{},"sha")
        with self.assertRaisesRegex(ValueError,"exact origin/main"):
            validate("stable","1.13.0","1.12.35",tags,{},"sha")
        with self.assertRaisesRegex(ValueError,"without -beta"):
            validate("stable","1.13.0-beta.1","1.13.0",tags,{},"sha")

    def test_existing_stable_track_retry_and_legacy_cutover(self):
        self.assertEqual(str(validate("stable","1.12.35","1.12.35",
                            ["v1.12.34"],{},"sha")),"1.12.35")
        self.assertEqual(str(validate("stable","1.12.35","1.12.35",
                            ["v1.12.34","v1.12.35"],{"v1.12.35":"sha"},"sha")),"1.12.35")
        with self.assertRaisesRegex(ValueError,"different code"):
            validate("stable","1.12.35","1.12.35",
                     ["v1.12.34","v1.12.35"],{"v1.12.35":"elsewhere"},"sha")

    def test_unrelated_tags_ignored(self):
        self.assertEqual(set(tagged_versions(["v1.12.34","other","v1.12.36-beta.1","v1.12.36-rc.1"])),
                         {"v1.12.34","v1.12.36-beta.1"})


if __name__=="__main__":unittest.main()
