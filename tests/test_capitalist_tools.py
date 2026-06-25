import unittest

from capitalist_tools.client import calculate_signature, compact_json
from capitalist_tools.env import is_placeholder
from capitalist_tools.telegram_bot import BUTTON_TEXT, parse_allowed_users, should_answer


class CapitalistToolsTest(unittest.TestCase):
    def test_signature_hashes_timestamp_body_and_secret(self) -> None:
        timestamp = "1678901234567"
        body = (
            '{"type":"PAYONEER","accountFrom":"U0000000","payload":{"account":"some@mail.com"},'
            '"userRequestId":"1745844029437","callbackUrl":"https://example.com/callbacksFromCap","amount":100}'
        )

        self.assertEqual(
            calculate_signature(timestamp, body, "somePrivateApiSecret"),
            "271c56160ceff489254a62c9615f49a2ed5a29ed96eced286c7e94a37bf42342",
        )


    def test_compact_json_removes_spaces(self) -> None:
        self.assertEqual(
            compact_json({"amount": 100, "payload": {"type": "PAYONEER"}}),
            '{"amount":100,"payload":{"type":"PAYONEER"}}',
        )


    def test_parse_allowed_users_supports_ids_and_usernames(self) -> None:
        ids, usernames = parse_allowed_users("123, -10042, @Daniel, plain_name")

        self.assertEqual(ids, {123, -10042})
        self.assertEqual(usernames, {"daniel", "plain_name"})


    def test_bot_answers_only_start_and_button(self) -> None:
        self.assertTrue(should_answer("/start"))
        self.assertTrue(should_answer(BUTTON_TEXT))
        self.assertFalse(should_answer("hello"))

    def test_placeholder_detection(self) -> None:
        self.assertTrue(is_placeholder(None))
        self.assertTrue(is_placeholder(""))
        self.assertTrue(is_placeholder("replace_me"))
        self.assertTrue(is_placeholder("your_telegram_bot_token"))
        self.assertFalse(is_placeholder("real-looking-value"))


if __name__ == "__main__":
    unittest.main()
