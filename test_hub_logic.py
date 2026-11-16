"""
test_hub_logic.py - unit tests for hub_logic.py

Run with:  python -m unittest test_hub_logic

The tests point REQUESTS_FILE at a temporary file, so the real
data/requests.json is never changed.

Written with AI assistance (GitHub Copilot).
"""

import os
import tempfile
import unittest

import hub_logic as logic


def make_valid_request(**changes):
    """Build a valid request (optionally changing some fields) for the tests."""
    details = {
        "environment": "sandbox", "name": "Andrea", "organization": "DLL",
        "email": "andrea@dll.com", "intended_use": "Testing quotes",
        "reviewed_guide": "yes", "technical_contact": "yes",
    }
    details.update(changes)
    return logic.build_credential_request("quote", ["Create quote"], details)


class TestCatalog(unittest.TestCase):
    """Tests for loading and searching the catalog."""

    def setUp(self):
        self.catalog, self.api_specs, _ = logic.load_hub_data()

    def test_empty_search_returns_everything(self):
        self.assertEqual(logic.search_catalog(self.catalog, ""), self.catalog)

    def test_search_is_case_insensitive(self):
        results = logic.search_catalog(self.catalog, "QUOTE")
        self.assertIn("quote", [p["id"] for p in results])

    def test_search_with_no_match(self):
        self.assertEqual(logic.search_catalog(self.catalog, "zzz-not-an-api"), [])

    def test_find_unknown_product(self):
        self.assertIsNone(logic.find_product("nope", self.catalog))

    def test_parse_operation_selection_skips_bad_values(self):
        ops = logic.get_operations("quote", self.api_specs)
        chosen = logic.parse_operation_selection("1, 1, 99, abc", ops)
        self.assertEqual(chosen, [ops[0]["operation"]])

    def test_missing_file_raises_data_file_error(self):
        with self.assertRaises(logic.DataFileError):
            logic.read_json_file(os.path.join(logic.DATA_DIR, "missing.json"))


class TestRequests(unittest.TestCase):
    """Tests for validating, saving, and reviewing credential requests."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_file = logic.REQUESTS_FILE
        logic.REQUESTS_FILE = os.path.join(self.tmp.name, "requests.json")
        self.requests_list = []

    def tearDown(self):
        logic.REQUESTS_FILE = self.original_file
        self.tmp.cleanup()

    def test_valid_request_has_no_problems(self):
        self.assertEqual(logic.validate_request(make_valid_request()), [])

    def test_bad_email_and_environment_are_reported(self):
        problems = logic.validate_request(make_valid_request(email="andrea", environment="test"))
        self.assertTrue(any("email" in p for p in problems))
        self.assertTrue(any("environment" in p for p in problems))

    def test_answers_are_normalized(self):
        request = make_valid_request(environment=" Sandbox ", reviewed_guide="YES")
        self.assertEqual(request["environment"], "sandbox")
        self.assertEqual(request["reviewed_guide"], "yes")

    def test_save_and_find_request(self):
        saved = logic.save_request(make_valid_request(), self.requests_list)
        self.assertEqual(saved["status"], logic.STATUS_SUBMITTED)
        found = logic.find_request(saved["request_id"].lower(), self.requests_list)
        self.assertIs(found, saved)
        self.assertEqual(len(logic.read_json_file(logic.REQUESTS_FILE)), 1)

    def test_approve_adds_credential(self):
        saved = logic.save_request(make_valid_request(), self.requests_list)
        logic.approve_request(saved, self.requests_list)
        self.assertEqual(saved["status"], logic.STATUS_AVAILABLE)
        self.assertTrue(saved["sample_credential"].startswith("sk_test_"))

    def test_cannot_approve_twice(self):
        saved = logic.save_request(make_valid_request(), self.requests_list)
        logic.approve_request(saved, self.requests_list)
        with self.assertRaises(ValueError):
            logic.approve_request(saved, self.requests_list)

    def test_needs_info_requires_a_note(self):
        saved = logic.save_request(make_valid_request(), self.requests_list)
        with self.assertRaises(ValueError):
            logic.request_more_info(saved, self.requests_list, "  ")

    def test_suggested_note_only_mentions_what_is_missing(self):
        note = logic.suggest_review_note(make_valid_request(reviewed_guide="no"))
        self.assertIn("API guide", note)
        self.assertNotIn("technical contact", note)

    def test_mask_credential(self):
        self.assertEqual(logic.mask_credential("sk_test_abc"), "sk_test****")

    def send_back_for_info(self, **changes):
        """Save a request and have the admin mark it Needs Information."""
        saved = logic.save_request(make_valid_request(**changes), self.requests_list)
        logic.request_more_info(saved, self.requests_list, logic.suggest_review_note(saved))
        return saved

    def test_resubmit_returns_request_to_submitted(self):
        saved = self.send_back_for_info(reviewed_guide="no")
        logic.resubmit_request(saved, self.requests_list, {"reviewed_guide": "YES"}, "Read it now")
        self.assertEqual(saved["status"], logic.STATUS_SUBMITTED)
        self.assertEqual(saved["reviewed_guide"], "yes")
        self.assertIn("API guide", saved["previous_review_note"])
        self.assertNotIn("review_note", saved)
        self.assertEqual(saved["requester_response"], "Read it now")
        self.assertEqual(saved["resubmission_count"], 1)

    def test_resubmit_only_allowed_for_needs_information(self):
        saved = logic.save_request(make_valid_request(), self.requests_list)
        with self.assertRaises(ValueError):
            logic.resubmit_request(saved, self.requests_list, {})

    def test_resubmit_needs_a_change_or_message(self):
        saved = self.send_back_for_info(reviewed_guide="no")
        with self.assertRaises(ValueError):
            logic.resubmit_request(saved, self.requests_list, {"reviewed_guide": "no"}, " ")
        self.assertEqual(saved["status"], logic.STATUS_NEEDS_INFO)

    def test_resubmit_rejects_invalid_answers_without_changing_request(self):
        saved = self.send_back_for_info(technical_contact="no")
        with self.assertRaises(ValueError):
            logic.resubmit_request(saved, self.requests_list, {"intended_use": "  "})
        self.assertEqual(saved["status"], logic.STATUS_NEEDS_INFO)
        self.assertEqual(saved["intended_use"], "Testing quotes")

    def test_get_product_name_falls_back_to_id(self):
        catalog, _, _ = logic.load_hub_data()
        self.assertNotEqual(logic.get_product_name("quote", catalog), "quote")
        self.assertEqual(logic.get_product_name("nope", catalog), "nope")


if __name__ == "__main__":
    unittest.main()
