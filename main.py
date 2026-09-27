import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher,F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, CommandObject
from conection import create_table
from service import *

load_dotenv()

token = os.getenv("BOT_TOKEN")

bot = Bot(token=token)
dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎟️ Мероприятия"),
        KeyboardButton(text="📋 Мои записи")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Hello 👋\n"
        "Wellcome to Event Bot.\n",
        reply_markup=keyboard
    )


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "📋Commands:\n\n"
        "/add_event Event name 10 2026-10-05 18:30\n"
        "/events\n"
        "/register 1\n"
        "/cancel 1\n"
        "/my_events",
        reply_markup=keyboard
    )

@dp.message(Command("add_event"))
async def add_event_command(message: Message,command: CommandObject):
    if not command.args:
        await message.answer(
            "Example:\n"
            "/add_event Event name 10 2026-10-05 18:30"
        )
        return
    
    parts = command.args.split()

    if len(parts) < 4:
        await message.answer(
            "Invalid format.\n"
            "Example:\n"
            "/add_event Event name 10 2026-10-05 18:30"
        )
        return

    title = " ".join(parts[:-3])

    try:
        capacity = int(parts[-3])
    except ValueError:
        await message.answer("❌ Capacity must be a number.")
        return
    date_text = parts[-2]
    time_text = parts[-1]

    try:
        event_date = datetime.strptime(
            f"{date_text} {time_text}",
            "%Y-%m-%d %H:%M"
        )
    except ValueError:
        await message.answer("❌ Date or time is invalid.")
        return

    await add_event(title,capacity,event_date)

    await message.answer(
        "✅ Event created succesfull!\n\n"
        f"📌 Name: {title}\n"
        f"👥 Capacity: {capacity}\n"
        f"📅 Day: {date_text}\n"
        f"🕐 Time: {time_text}"
    )

@dp.message(Command("events"))
async def events_command(message: Message):
    events = await get_events()

    if not events:
        await message.answer(
            "There are no events yet."
        )
        return

    text = "🎟️ Events:\n"

    for i in events:
        free_seats = i["capacity"] - i["confirmed"]
        text += (
            f"🆔 ID: {i['events_id']}\n"
            f"📌 {i['title']}\n"
            f"🪑Free seats : {free_seats}\n"
            f"📅 Date: {i['event_date'].strftime('%Y-%m-%d')}\n"
            f"🕐 Time: {i['event_date'].strftime('%H:%M')}\n\n"
        )
    await message.answer(text)


@dp.message(Command("register"))
async def register_command(message: Message,command: CommandObject):
    if not command.args:
        await message.answer(
            " Write ID of event.\n"
            "Example:\n"
            "/register 1"
        )
        return

    try:
        event_id = int(command.args.strip())
    except ValueError:
        await message.answer(
            "❌ ID must be a number."
        )
        return

    result = await register_user(message.from_user.id,event_id)

    if result == "Event not found":
        await message.answer(
            "❌ Event not found.")

    elif result == "Already registered":
        await message.answer(
            "⚠️ You are alreadi registered.")

    elif result == "confirmed":
        await message.answer(
            "✅ You have registered for the event.\n"
            "Статус: confirmed")
        
    elif result == "waitlist":
        await message.answer(
            "⏳ The event is fully booked.\n"
            "You have been added to the waitlist..")


@dp.message(Command("cancel"))
async def cancel_command(message: Message,command: CommandObject):
    if not command.args:
        await message.answer(
            "Write ID of event.\n"
            "Example:\n"
            "/cancel 1"
        )
        return

    try:
        event_id = int(command.args.strip())
    except ValueError:
        await message.answer(
            "❌ ID must be a number."
        )
        return

    result, promoted_user = await cancel_registration(message.from_user.id,event_id )

    if result == "Not registered":
        await message.answer(
            "❌You are not registered for this event."
        )
        return

    await message.answer(
        "✅ Your registration has been cancel."
    )



    if promoted_user:
        await bot.send_message(
            promoted_user,
            "🎉 A seat has become available!\n"
            "You have been moved from the waitlist to confirmed."
        )


@dp.message(Command("my_events"))
async def my_events_command(message: Message):
    events = await get_my_events(message.from_user.id)
    if not events:
        await message.answer(
            "📋 I have not registered now."
        )
        return

    text = ""
    for i in events:
        if i["status"] == "confirmed":
            status = "✅ confirmed"
        else:
            status = "⏳ waitlist"

        text += (
            f"📋 My events:\n"
            f"🆔 ID: {i['events_id']}\n"
            f"📌 {i['title']}\n"
            f"📅 {i['event_date'].strftime('%Y-%m-%d')}\n"
            f"🕐 {i['event_date'].strftime('%H:%M')}\n"
            f"📊 Status: {status}\n\n"
        )
    await message.answer(text)


@dp.message(F.text == "🎟️ Мероприятия")
async def events_button(message: Message):
    await events_command(message)


@dp.message(F.text == "📋 Мои записи")
async def my_events_button(message: Message):
    await my_events_command(message)


async def main():
    await create_table()
    print("Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

