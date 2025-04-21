# Joke Management Bot

A Telegram bot for managing a joke database with admin moderation features. The bot allows users to view, add, edit and delete jokes across multiple categories with administrative approval.

## Features

- **Browsing jokes by category**: Users can view jokes organized by categories
- **Adding new jokes**: Submit new jokes for moderation
- **Editing jokes**: Change existing jokes (requires admin approval)
- **Deleting jokes**: Remove jokes from the database (requires admin approval)
- **Admin moderation**: All content changes require approval from an administrator
- **Database management**: Admin-only commands for database maintenance
- **Duplicate detection**: AI-powered joke similarity checking using Google's Gemini API

## Setup

### Prerequisites

- Python 3.8+
- MySQL database
- Telegram Bot Token (from BotFather)
- Google Gemini API key (for duplicate detection)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/joke-management-bot.git
   cd joke-management-bot
   ```

2. Install required dependencies:
   ```
   pip install python-telegram-bot mysql-connector-python python-dotenv google-generativeai
   ```

3. Set up the database:
   ```
   python DB/create_db.py
   python DB/setup_jokes_database.py
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASS=your_mysql_password
   DB_NAME=jokes_db
   TG_TOKEN=your_telegram_bot_token
   ADMIN_ID=your_telegram_user_id
   GOOGLE_API_KEY=your_gemini_api_key
   ```

5. Start the bot:
   ```
   python Backend/telegram_bot.py
   ```

## Usage

### User Commands

- `/start` - Start the bot and see available commands
- `/show` - Browse jokes by category
- `/add` - Submit a new joke (will be sent for moderation)
- `/change` - Edit an existing joke (requires joke ID)
- `/delete` - Delete a joke (requires joke ID)

### Admin Commands

- `/clear` - Clear the entire joke database (hidden command)
- Approve or decline user submissions through the admin interface

## Project Structure

- `Backend/` - Core application logic
  - `telegram_bot.py` - Telegram bot implementation
  - `main.py` - Core joke management functionality
  - `gemini_kolobok.py` - AI-powered duplicate detection
- `DB/` - Database setup and utilities
  - `create_db.py` - Database creation script
  - `setup_jokes_database.py` - Schema setup
  - `view_database.py` - Utility to view database contents

## Technology Stack

- **Python** - Core programming language
- **python-telegram-bot** - Telegram Bot API wrapper
- **MySQL** - Database backend
- **Google Gemini API** - AI for duplicate detection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Project Description

The Joke Management Bot is designed to create a moderated platform for sharing and storing jokes. This project combines several technologies to provide a seamless user experience while maintaining content quality through administrative oversight.

### Purpose

The primary goal is to build a database of jokes across various categories while ensuring content appropriateness through a moderation system. The bot serves as both a content repository and a submission platform, allowing a community to contribute while maintaining quality standards.

### Technical Implementation

The bot is built on a three-tier architecture:
1. **Telegram Interface** - Handles user interactions through the Telegram Bot API
2. **Business Logic** - Processes requests, manages moderation workflows, and communicates with external services
3. **Database Layer** - Stores jokes and categories in a structured MySQL database

One of the unique features is the integration with Google's Gemini AI to detect similar jokes, helping prevent duplicates in the database. This demonstrates the combination of traditional database operations with modern AI capabilities.

### Use Cases

- Community-driven joke collection with quality control
- Educational tool for demonstrating moderation systems
- Template for content management bots on Telegram
- Showcase for integrating AI services into chat applications

The moderation workflow ensures all content meets administrator standards before being added to the database, making this suitable for various settings including educational environments. 