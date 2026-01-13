# Botstars - Telegram Stars Exchange Bot

## Overview
A Telegram bot for exchanging Telegram Stars. Users can top up their balance using Stars, refer friends, and withdraw funds. Built with Python using aiogram framework.

## Project Structure
- `main.py` - Bot entry point and initialization
- `handlers.py` - Message and command handlers
- `keyboards.py` - Keyboard markup definitions
- `states.py` - FSM states for user flows
- `database.py` - SQLite database operations

## Configuration
The bot requires a Telegram Bot Token set as the `TELEGRAM_BOT_TOKEN` secret.

## Database
Uses SQLite (`botstars.db`) with tables:
- `users` - User data, balances, and referral relationships
- `withdrawals` - Withdrawal requests

## Running
The bot runs as a console application via the "Telegram Bot" workflow.
