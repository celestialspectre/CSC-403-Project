import unittest
from web import app

class TestLoading(unittest.TestCase):
    def setUp(self):
        app.config.update({"TESTING": True})
        self.client = app.test_client()
    
    def test_valid_json(self):
        response = self.client.get("/character", query_string={
            "nameField": "Moneta",
            "lvlField": "5"
        })

        self.assertEqual(response.status_code, 200) # correct json

        characterData = response.get_json()
        self.assertEqual(characterData["name"], "Moneta")
        self.assertEqual(characterData["level"], 5)

    def test_invalid_json(self):
        response = self.client.get("/character", query_string={
            "nameField": "    ",
            "lvlField": "5"
        })

        self.assertEqual(response.status_code, 400) # bad input (no name)

        response2 = self.client.get("/character", query_string={
            "nameField": "Moneta",
            "lvlField": "50"
        })

        self.assertEqual(response2.status_code, 400) # bad input (invalid level)

    def test_char_sheet_loads(self):
        response = self.client.get("/character", query_string={
            "nameField": "Moneta",
            "lvlField": "5",
            "sheetCheck": "on"
        })

        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)
        self.assertIn('<h1>Player Stats</h1>', html)
        self.assertIn('<p name="nameOut" class="inputRes">Moneta</p>', html)
        self.assertIn('<p name="lvlOut" class="inputRes">5</p>', html)


if __name__ == '__main__':
    unittest.main()