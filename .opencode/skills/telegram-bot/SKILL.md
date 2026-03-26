---
name: telegram-bot
description: Best practices for implementing Telegram bots using python-telegram-bot, including async handlers and conversation flows
---

# Telegram Bot Integration Skill

When implementing Telegram bots:

- Use python-telegram-bot library
- Keep bot logic separate from Flask app
- Never block the event loop
- Use async handlers when possible
- Store bot token in environment variables
- Validate all user inputs

Conversation flow should follow:

1. User sends a URL
2. Validate URL
3. Ask user for format (mp3/mp4)
4. Download media
5. Send file via Telegram
