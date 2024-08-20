import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import random
import os
import logging
# Use double backslashes `\\` or raw string `r` to avoid escape sequences issues
os.environ['SSL_CERT_FILE'] = r'C:\Users\horisont1\Desktop\coding\cacert.pem'
# Enable logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Enable all intents
intents = discord.Intents.all()

# Initialize bot with all intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Constants
SUPPORT_CATEGORY_ID = 1275234841331367997  # Replace with your support category ID
CLOSED_CATEGORY_ID = 1271828303845799999    # Replace with your closed tickets category ID
SUPPORT_ROLE_IDS = [1268321134139412665, 1268321261516488744, 1269100504080711781, 1268319677977858213]
SUPPORT_MESSAGE_ID = None  # To be set by the /setsupport command

# File paths
USER_DATA_FILE = 'user_data.json'

# Ensure the user data file exists
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({}, f)

# Function to get or create a user's economy entry
def get_or_create_user(user_id):
    with open(USER_DATA_FILE, 'r') as f:
        data = json.load(f)
    
    if str(user_id) not in data:
        data[str(user_id)] = {
            'balance': 0,
            'bank': 0,
            'loans': 0,
            'loan_due': None
        }
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data, f)
    
    return data[str(user_id)]

# Function to update a user's data
def update_user(user_id, user_data):
    with open(USER_DATA_FILE, 'r') as f:
        data = json.load(f)
    
    data[str(user_id)] = user_data
    
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

# Economy Commands
@bot.tree.command(name="balance", description="Check your balance")
async def balance(interaction: discord.Interaction):
    user = get_or_create_user(interaction.user.id)
    await interaction.response.send_message(f"Your balance is {user['balance']} Snowflakes.")

@bot.tree.command(name="bank", description="Deposit money into your bank")
@app_commands.describe(amount="The amount to deposit")
async def bank(interaction: discord.Interaction, amount: int):
    user = get_or_create_user(interaction.user.id)
    if user['balance'] < amount:
        await interaction.response.send_message("You don't have enough Snowflakes to deposit.")
    else:
        user['balance'] -= amount
        user['bank'] += amount
        update_user(interaction.user.id, user)
        await interaction.response.send_message(f"You deposited {amount} Snowflakes into your bank.")

@bot.tree.command(name="rob", description="Rob another user")
@app_commands.describe(user="The user to rob")
async def rob(interaction: discord.Interaction, user: discord.User):
    if user == interaction.user:
        await interaction.response.send_message("You can't rob yourself.")
        return

    target = get_or_create_user(user.id)
    if target['balance'] < 50:
        await interaction.response.send_message(f"{user.name} doesn't have enough Snowflakes to rob.")
        return

    amount = random.randint(1, target['balance'] // 2)
    target['balance'] -= amount
    update_user(user.id, target)

    robber = get_or_create_user(interaction.user.id)
    robber['balance'] += amount
    update_user(interaction.user.id, robber)
    
    await interaction.response.send_message(f"You successfully robbed {amount} Snowflakes from {user.name}.")

@bot.tree.command(name="tip", description="Tip another user")
@app_commands.describe(user="The user to tip", amount="The amount to tip")
async def tip(interaction: discord.Interaction, user: discord.User, amount: int):
    if user == interaction.user:
        await interaction.response.send_message("You can't tip yourself.")
        return

    giver = get_or_create_user(interaction.user.id)
    if giver['balance'] < amount:
        await interaction.response.send_message("You don't have enough Snowflakes to tip.")
    else:
        giver['balance'] -= amount
        update_user(interaction.user.id, giver)

        receiver = get_or_create_user(user.id)
        receiver['balance'] += amount
        update_user(user.id, receiver)
        
        await interaction.response.send_message(f"You tipped {amount} Snowflakes to {user.name}.")

@bot.tree.command(name="duel", description="Duel another user for Snowflakes")
@app_commands.describe(user="The user to duel", amount="The amount to duel for")
async def duel(interaction: discord.Interaction, user: discord.User, amount: int):
    if user == interaction.user:
        await interaction.response.send_message("You can't duel yourself.")
        return

    challenger = get_or_create_user(interaction.user.id)
    opponent = get_or_create_user(user.id)
    if challenger['balance'] < amount or opponent['balance'] < amount:
        await interaction.response.send_message("One of you doesn't have enough Snowflakes for the duel.")
    else:
        winner = random.choice([interaction.user, user])
        loser = user if winner == interaction.user else interaction.user

        winner_data = get_or_create_user(winner.id)
        loser_data = get_or_create_user(loser.id)

        loser_data['balance'] -= amount
        update_user(loser.id, loser_data)

        winner_data['balance'] += amount
        update_user(winner.id, winner_data)

        await interaction.response.send_message(f"{winner.name} won the duel and gained {amount} Snowflakes from {loser.name}.")

@bot.tree.command(name="loan", description="Take a loan")
@app_commands.describe(amount="The amount to loan")
async def loan(interaction: discord.Interaction, amount: int):
    user = get_or_create_user(interaction.user.id)
    if user['loans'] > 0:
        await interaction.response.send_message("You already have an outstanding loan.")
    else:
        user['balance'] += amount
        user['loans'] = amount
        # Here you would set a loan_due timestamp or equivalent value, which would be checked periodically
        update_user(interaction.user.id, user)
        await interaction.response.send_message(f"You took a loan of {amount} Snowflakes. You have 7 days to repay it.")

@tasks.loop(minutes=1)
async def check_loans():
    with open(USER_DATA_FILE, 'r') as f:
        data = json.load(f)
    
    for user_id, user_data in data.items():
        # Logic for checking overdue loans and updating user data
        # For now, we're just printing a reminder
        if user_data['loans'] > 0:
            logger.debug(f"User {user_id} has a loan of {user_data['loans']} Snowflakes.")
            # Example action: deduct the loan amount from balance
            # user_data['balance'] -= user_data['loans']
            # user_data['loans'] = 0
            # update_user(user_id, user_data)


@bot.event
async def on_ready():
    logger.debug(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="Snowy Extra"))
    try:
        synced = await bot.tree.sync()
        logger.debug(f"Synced {len(synced)} commands globally.")
        check_loans.start()  # Start the check_loans task here
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
bot.run('11111111111111111111111111111111111111111111111')
