import requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError


def get_starships():
    # Start with the first page of starships.
    url = "https://swapi.dev/api/starships/"
    starships = []

    # Keep requesting pages until there is no next page.
    while url:
        response = requests.get(url, timeout=30)

        # Raise an error if the request was unsuccessful.
        response.raise_for_status()

        # I Convert the JSON response into a Python dictionary.
        data = response.json()

        # Add this page's starships to the list.
        starships.extend(data["results"])

        # Get the next page URL. This is None on the last page.
        url = data["next"]

    return starships


def get_pilot_ids(pilot_urls, characters):
    pilot_ids = []

    for pilot_url in pilot_urls:
        # Use the pilot's URL to get their details.
        response = requests.get(pilot_url, timeout=30)
        response.raise_for_status()

        pilot_data = response.json()
        pilot_name = pilot_data["name"]

        # Find the character with the same name in MongoDB.
        character = characters.find_one({"name": pilot_name})

        # Stop if there is no matching character.
        if character is None:
            raise ValueError(
                f"Cannot find '{pilot_name}' in the characters collection."
            )

        # Keep their MongoDB ID so the starship can reference them.
        pilot_ids.append(character["_id"])

    return pilot_ids


def replace_pilot_links(starships, characters):
    for starship in starships:
        # Replace each ship's pilot URLs with the matching ObjectIds.
        starship["pilots"] = get_pilot_ids(
            starship["pilots"],
            characters
        )

    return starships


def save_starships(starships, collection):
    for starship in starships:
        # Use the URL to find an existing starship.
        # Update it if found, or insert it if it is new.
        collection.update_one(
            {"url": starship["url"]},
            {"$set": starship},
            upsert=True
        )


def validate_pilots(starships, characters):
    references_checked = 0

    for starship in starships:
        for pilot_id in starship["pilots"]:
            # Check that the referenced character exists.
            character = characters.find_one({"_id": pilot_id})

            if character is None:
                raise ValueError(
                    f"Broken pilot reference in {starship['name']}: "
                    f"{pilot_id}"
                )

            references_checked += 1

    print(f"Validated {references_checked} pilot references.")


def main():
    # Connect to my local MongoDB server.
    # Allow five seconds to find an available server.
    client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000
    )

    try:
        # Check the connection before starting the project.
        client.admin.command("ping")

        db = client["starwars"]
        characters = db["characters"]
        starships_collection = db["starships"]

        # The characters need to be imported before linking the pilots.
        if characters.count_documents({}) == 0:
            raise ValueError(
                "The characters collection is empty. "
                "Check your database name and import the characters first."
            )

        # Extract the starships from the API.
        print("Getting starships from the API...")
        starships = get_starships()
        print(f"Downloaded {len(starships)} starships.")

        # Transform the pilot URLs into MongoDB references.
        print("Replacing pilot links with ObjectIds...")
        starships = replace_pilot_links(starships, characters)

        # Check the references before loading the data.
        validate_pilots(starships, characters)

        # Load the transformed starships into MongoDB.
        print("Saving starships to MongoDB...")
        save_starships(starships, starships_collection)
        print(f"Saved {len(starships)} starships.")

        # Read back the ships from this run using their URLs.
        saved_starships = list(
            starships_collection.find({
                "url": {"$in": [ship["url"] for ship in starships]}
            })
        )

        # Check the references stored in the database as well.
        validate_pilots(saved_starships, characters)

        # Use the Millennium Falcon to demonstrate the pilot links.
        falcon = starships_collection.find_one({
            "name": "Millennium Falcon"
        })

        if falcon:
            print("\nStarship:", falcon["name"])
            print("Pilot ObjectIds:", falcon["pilots"])

            # Look up each pilot's name using their stored ObjectId.
            for pilot_id in falcon["pilots"]:
                pilot = characters.find_one({"_id": pilot_id})
                print("Pilot:", pilot["name"])

        print("\nMini project completed successfully.")

    except (
        requests.RequestException,
        PyMongoError,
        ValueError,
        KeyError
    ) as error:
        # Show the error if a request, database call or data check fails.
        print(f"\nProject stopped: {error}")

    finally:
        # Close the client even if an error happens.
        client.close()


# Only run the project when this file is run directly.
# Importing functions into test_main.py will not start the project.
if __name__ == "__main__":
    main()