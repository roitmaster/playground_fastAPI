# FastAPI Game API

This is a FastAPI application that provides a RESTful API for managing games and user authentication. It uses MongoDB as the database and supports JWT-based authentication.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
  - [Authentication](#authentication)
  - [User Management](#user-management)
  - [Game Management](#game-management)
- [Running the Application](#running-the-application)
- [Environment Variables](#environment-variables)

## Features

- User authentication with JWT tokens.
- CRUD operations for games.
- Sorting and filtering options for game listings.
- CORS support for frontend applications.

## Requirements

- Python 3.7 or later
- MongoDB
- FastAPI
- Motor (asynchronous MongoDB driver)
- Passlib (for password hashing)
- Jose (for JWT handling)
- Pydantic (for data validation)
- python-dotenv (for loading environment variables)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/roitmaster/playground_fastAPI.git
   cd playground_fastAPI

2. Create a virtual environment and activate it:

  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows use `venv\Scripts\activate`
  ```
3. Install the required packages:

  ```bash
  pip install -r requirements.txt
  ```

4. Create a .env file in the root directory and set the required environment variables (see below).

## USAGE

1. Start the FastAPI server:

   ```bash
   uvicorn main:app --reload
   ```
2. The API will be available at http://127.0.0.1:8000.
3. Access the interactive API documentation at http://127.0.0.1:8000/docs

## API Endpoints
### Authentication

* #### POST /token
  * #### Description: Log in to obtain an access token.
  * #### Request Body.

      ```
      {
        "username": "your_username",
        "password": "your_password"
      }
      ```
* #### GET /users/me
  * #### Description: Retrieve the current user's information.
  * #### Authorization: Bearer token required
 
### User Management

Currently, user management features are limited to login and fetching user info.

### Game Management

* #### POST /games/
  * #### Description: Create a new game.
  * #### Request Body: Game details.

* #### GET /games/
  * #### Description: Retrieve a list of games.
  * #### Query Parameters:
    * `limit`: Number of games to return.
    * `sort_by`: Field to sort by (`price`, `name`, or `ratings`).
    * `sort_order`: Order of sorting (`asc` or `desc`).
  * #### Authorization: Bearer token required.
    
* #### GET /games/{game_id}
  * #### Description: Retrieve a game by ID.
  * #### Authorization: Bearer token required.

* #### PUT /games/{game_id}
  * #### Description: Update a game by ID.
  * #### Request Body: Updated game details.
  * #### Authorization: Bearer token required.

* #### DELETE /games/{game_id}
  * #### Description: Delete a game by ID.
  * #### Authorization: Bearer token required.

## Running the Application
Ensure that MongoDB is running and accessible. Then, run the FastAPI application as described in the usage section.

## Environment Variables
Create a .env file in the root directory with the following variables:

  ```
  SECRET_KEY=your_secret_key
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30
  MONGO_DETAILS=mongodb://localhost:27017
  DATABEASE=your_database_name
  ```
Replace your_secret_key and your_database_name with your desired values.

## Screenshots

Here’s a screenshot of the game:

![Game Screenshot](images/games.png)
