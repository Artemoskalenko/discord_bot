import pytz
import disnake
import datetime
import os

from dotenv import load_dotenv
from disnake.ext import commands, tasks


# Налаштування часу
default_timezone = pytz.timezone("Europe/Berlin")
mailing_time = datetime.time(18, 00)
report_time = datetime.time(20, 00)


def get_current_time() -> datetime:
    return datetime.datetime.now(default_timezone)


# Налаштування бота, сервера, каналу...
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = commands.Bot(command_prefix='.', help_command=None, intents=disnake.Intents.all())
report_answers = {}
guild = None
channel = None


@bot.event
async def on_ready():
    """Бот запускається, записує сервер та канал у змінні"""
    global guild
    global channel

    print(f'Logged in as {bot.user.name}')
    guild = bot.guilds[0]
    for channel in guild.channels:
        if channel.name == 'daily-report':
            channel = guild.get_channel(channel.id)


@bot.event
async def on_message(message):
    """
    Функція реагує на отримання повідомлення.
    За умови, що повідомлення було отримано в особистому чаті в проміжок часу між 18.00 та 20.00 за Берліном, воно записується в змінну report_answers.
    """
    if type(message.channel) == disnake.channel.DMChannel and mailing_time <= get_current_time().time() <= report_time:
        user_id = message.author.id
        user = await guild.fetch_member(user_id)

        for role in user.roles:
            if role.name != '@everyone':
                if role.name not in report_answers:
                    report_answers[role.name] = {user.name: message.content}
                else:
                    report_answers[role.name][user.name] = message.content


@tasks.loop(seconds=60)
async def send_scheduled_message():
    """
    Функція кожні 60 секунд перевіряє час.
    Якщо час 18.00, бот відправляє повідомлення кожному працівнику з проханням написати яку роботу вони зробили за сьогодні.
    Якщо час 20.00, бот формує звіт з отриманих відповідей та надсилає його до каналу daily report.
    """
    current_time = get_current_time()

    if current_time.hour == mailing_time.hour and current_time.minute == mailing_time.minute:
        for member in guild.members:
            if member.bot == False:
                await member.send("Ось і закінчився робочий день. Напишіть, будь ласка, яку роботу ви зробили за сьогодні.")
    elif current_time.hour == report_time.hour and current_time.minute == report_time.minute:
        report = f'**{datetime.date.today()}**\n'
        for department, answers in report_answers.items():
            report += f'**{str(department).upper()}**\n'
            for name, text in answers.items():
                report += f'{name}: {text}\n'
            report += '\n'

        await channel.send(report)


@send_scheduled_message.before_loop
async def before_send_scheduled_message():
    await bot.wait_until_ready()


send_scheduled_message.start()
bot.run(TOKEN)