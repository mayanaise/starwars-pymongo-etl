import unittest
from unittest.mock import Mock, patch

from bson import ObjectId
from pymongo.errors import ServerSelectionTimeoutError

from main import get_starships, get_pilot_ids, save_starships, main


class TestStarships(unittest.TestCase):

    # Replace the real API call during this test.
    @patch("main.requests.get")
    def test_get_starships(self, mock_get):
        response = Mock()

        # Use one starship as our test data.
        response.json.return_value = {
            "results": [{"name": "Millennium Falcon"}],
            "next": None
        }
        mock_get.return_value = response

        starships = get_starships()

        # Check that we get the starship back.
        self.assertEqual(len(starships), 1)
        self.assertEqual(starships[0]["name"], "Millennium Falcon")

    @patch("main.requests.get")
    def test_get_pilot_id(self, mock_get):
        pilot_id = ObjectId()

        # Pretend the API returns Han Solo.
        response = Mock()
        response.json.return_value = {"name": "Han Solo"}
        mock_get.return_value = response

        # Pretend Han Solo already exists in the database.
        characters = Mock()
        characters.find_one.return_value = {
            "_id": pilot_id,
            "name": "Han Solo"
        }

        result = get_pilot_ids(
            ["https://swapi.dev/api/people/14/"],
            characters
        )

        # Check that we get his ObjectId instead of the URL.
        self.assertEqual(result, [pilot_id])

        # Check that we searched for the right character.
        characters.find_one.assert_called_once_with(
            {"name": "Han Solo"}
        )

    @patch("main.requests.get")
    def test_missing_pilot(self, mock_get):
        response = Mock()
        response.json.return_value = {"name": "Han Solo"}
        mock_get.return_value = response

        # None means the character was not found.
        characters = Mock()
        characters.find_one.return_value = None

        # A missing character should raise an error.
        with self.assertRaises(ValueError):
            get_pilot_ids(
                ["https://swapi.dev/api/people/14/"],
                characters
            )

    def test_no_pilots(self):
        characters = Mock()

        # Some starships do not have any pilots listed.
        result = get_pilot_ids([], characters)

        self.assertEqual(result, [])

        # There should be no character lookup if there are no pilots.
        characters.find_one.assert_not_called()

    def test_save_starship(self):
        collection = Mock()

        starship = {
            "name": "Millennium Falcon",
            "url": "https://swapi.dev/api/starships/10/",
            "pilots": []
        }

        save_starships([starship], collection)

        # Check the update sent to MongoDB.
        # Upsert lets it insert the starship if it is not there already.
        collection.update_one.assert_called_once_with(
            {"url": starship["url"]},
            {"$set": starship},
            upsert=True
        )

    @patch("main.print")
    @patch("main.MongoClient")
    def test_connection_failure(self, mock_client, mock_print):
        client = mock_client.return_value

        # Make the connection check fail without using the real database.
        client.admin.command.side_effect = ServerSelectionTimeoutError(
            "Cannot connect to MongoDB"
        )

        main()

        # Check that the program tried to ping MongoDB.
        client.admin.command.assert_called_once_with("ping")

        # Check that it displayed the error message.
        mock_print.assert_called_once_with(
            "\nProject stopped: Cannot connect to MongoDB"
        )

        # The client should still be closed when something goes wrong.
        client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()