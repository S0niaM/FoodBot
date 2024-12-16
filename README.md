# FoodBot

This is a food bot built using the Rasa framework. It can help users with food-related queries and provide information about recipes, ingredients, and more.

## Requirements

- Python 3.9.13
- Rasa  3.6.20

## Installation

1. Clone the repository:

```
git clone https://github.com/S0niaM/FoodBot.git
cd FoodBot
```

2. Create a virtual environment and activate it:

```
python -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate  # For Windows
```

3. Install the required packages:

```
pip install -r requirements.txt
```

## Usage

1. Train the Rasa model:

```
rasa train
```

2. Run the Rasa server with API enabled, CORS configuration and start action server:

```
rasa run --enable-api --cors "*"
rasa run actions
```


This command starts the Rasa server and enables the API with CORS support for all origins (`*`). This allows the frontend to communicate with the Rasa server.

3. Integrate the bot with your frontend application by making API calls to the Rasa server.

## Project Structure

- `actions/`: Contains custom action code
- `data/`: Contains NLU training data and stories
- `models/`: Contains trained models
- `config.yml`: Rasa configuration file
- `domain.yml`: Rasa domain file
- `endpoints.yml`: Rasa endpoint configuration
- `requirements.txt`: Python dependencies

## Additional Resources

- [Rasa Documentation](https://rasa.com/docs/)
- [Rasa Community Forum](https://forum.rasa.com/)
