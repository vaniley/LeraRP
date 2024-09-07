import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart
from aiogram.types import Message, reaction_type_emoji
from openai import OpenAI
from random import randint, choice

import json

DEFAULT_CONFIG = {
    "rolePrompt": "You are a helpful assistant.",
    "startMessage": "Hi! How can I help you?",
    "nameVariants": ["gpt"],
    "stickers": [],
    "openAIBaseUrl": "https://api.openai.com/v1",
    "openAIKey": "YOUR_OPENAI_API_KEY",
    "openAIModel": "gpt-4o-mini",
    "telegramBotToken": "YOUR_TELEGRAM_BOT_TOKEN",
}

try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # Проверяем, что все необходимые ключи присутствуют в конфиге
    for key in DEFAULT_CONFIG:
        if key not in config:
            print(f"Error: Missing key '{key}' in config.json. Using default value.")
            config[key] = DEFAULT_CONFIG[key]

except FileNotFoundError:
    print("Warning: config.json not found. Using default configuration.")
    config = DEFAULT_CONFIG
except json.JSONDecodeError:
    print("Error: config.json is not a valid JSON file. Using default configuration.")
    config = DEFAULT_CONFIG


messages = [
    {
        "role": "system",
        "content": config["rolePrompt"],
    }
]
stickers = config["stickers"]

dp = Dispatcher()
client = OpenAI(
    base_url=config["openAIBaseUrl"],
    api_key=config["openAIKey"],
)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Responds to the /start command.
    """
    await message.answer(config["startMessage"])


@dp.message(F.text)
async def echo_handler(message: Message, bot: Bot) -> None:
    global messages, stickers, users

    messages.append(
        {"role": "user", "content": f"{message.from_user.full_name}: {message.text}"}
    )

    if randint(1, 10) == 1:
        await message.react(
            [
                reaction_type_emoji.ReactionTypeEmoji(
                    emoji=choice(["❤", "💔", "👍", "🤗"])
                )
            ]
        )

    should_reply = False
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        should_reply = True
    elif message.chat.type == "private":
        should_reply = True
    elif randint(1, 20) == 1:
        should_reply = True
    else:
        for name in config["nameVariants"]:
            if (
                " " + name.lower() in message.text.lower()
                or message.text.lower().startswith(name.lower())
            ):
                should_reply = True

    if should_reply:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        completion = client.chat.completions.create(
            model=config["openAIModel"],
            messages=messages,
            stream=False,
            temperature=1.1,
            max_tokens=512,
        )
        response_text = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response_text})

        if randint(1, 9) == 1:
            await bot.send_sticker(message.chat.id, choice(stickers))

        response_parts = response_text.split("\n\n")
        for part in response_parts:
            if randint(1, 15):
                await message.reply(part)
            else:
                await message.answer(part)
            # Небольшая задержка между отправкой сообщений
            await asyncio.sleep(0.5)


async def main() -> None:
    bot = Bot(
        token=config["telegramBotToken"],
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
