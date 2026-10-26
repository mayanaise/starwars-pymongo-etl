# Star Wars ETL Mini Project

For this project, I used Python to get starship data from the Star Wars API, replace the pilot links with references to characters already in MongoDB, and save the starships into the database.

I completed this as part of my Sparta Global data engineering training.

## Tools I used

- Python
- Requests
- MongoDB
- PyMongo
- MongoDB Compass
- unittest and unittest.mock

## What I did

### 1. Got the starship data

I used requests to get the starships from the API.

The API returns the data across several pages, so I used a while loop to follow the next page link and collect the results into one list.

### 2. Found the pilots

Each starship has a pilots field containing API URLs. Some ships have no pilots listed.

For each pilot URL, I requested the pilot's details and used their name to find the matching character in my MongoDB characters collection.

### 3. Replaced the pilot URLs

Once I found the matching character, I took their MongoDB ObjectId and used it to replace the pilot URL.

This links the starship to the existing character document without copying all the character's information into the starship.

### 4. Checked the references

Before saving, I checked that each pilot ObjectId pointed to a character that existed in the database.

If a character could not be found, the code raised an error so I could identify the problem.

### 5. Saved the starships

I saved the transformed data into the starships collection.

I used update_one with upsert=True and matched each starship by its API URL. This updates an existing starship or inserts it if it is not already there.

I checked the collection in MongoDB Compass and confirmed it contained 36 starships.

### 6. Checked the saved data

After saving, I read the starships back from MongoDB and checked their pilot references again.

I also added a query for the Millennium Falcon. The code uses its pilot ObjectIds to look up and print the character names, which helps demonstrate the links between the collections.

## Error handling

I added checks for:

- Failed API requests
- MongoDB connection and database errors
- An empty characters collection
- Missing characters or pilot references
- Missing dictionary keys

I also added request timeouts and used finally to close the MongoDB client when the program finishes.

## Unit tests

I created a separate test_main.py file with six tests:

- Getting starship data from an API response
- Finding the correct pilot ObjectId
- Raising an error when a pilot is missing
- Handling an empty pilot list
- Checking the update sent when saving a starship
- Handling a MongoDB connection failure

I used mocking to replace the API requests and database calls during testing. This means the tests do not need the live API or change my actual database.

All six tests passed.

## What I learned

This project helped me bring together the extract, transform and load stages in one Python program.

I practised working with a paginated API, using MongoDB references, handling errors and writing unit tests with mocks.
