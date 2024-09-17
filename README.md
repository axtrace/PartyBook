# PartyBook

PartyBook is a Telegram bot designed to help users track their reading progress and receive excerpts from books they are currently reading. The bot allows users to manage their reading lists and get daily notifications with book excerpts.

## Features

- Track the current book and reading progress for each user.
- Send excerpts from the current reading position.
- Daily notifications at 20:20 for users who have enabled this feature.
- User-friendly commands for easy interaction.

## Actual example

You can find actual example here: https://telegram.me/PartyBook_bot

## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.x installed on your machine.
- A Telegram account to create and interact with the bot.
- Access to a database (e.g., SQLite, PostgreSQL) to store user data and book information.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/axtrace/PartyBook.git
   cd PartyBook
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Telegram bot:
   - Create a new bot using [BotFather](https://core.telegram.org/bots#botfather) on Telegram.
   - Obtain your bot token.

4. Configure your database connection in the code.

5. Run the bot:
   ```bash
   python telebot_handler.py
   ```

## Usage

Once the bot is running, you can interact with it using the following commands:

- `/start`: Start interacting with the bot.
- `/help`: Get a list of available commands.
- `/current`: Check which book you are currently reading.
- `/set_progress <page_number>`: Update your reading progress.
- `/daily_excerpts`: Enable or disable daily excerpt notifications.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find bugs, please open an issue or submit a pull request.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
