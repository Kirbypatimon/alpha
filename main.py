import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import os
import re

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ログ送信チャンネルID（環境変数から取得）
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}!")

# 常時ログ：メッセージ編集
@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return
    if LOG_CHANNEL_ID == 0:
        return
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="📝 メッセージ編集", color=discord.Color.orange())
        embed.add_field(name="ユーザー", value=before.author.mention, inline=True)
        embed.add_field(name="チャンネル", value=before.channel.mention, inline=True)
        embed.add_field(name="編集前", value=before.content[:1024], inline=False)
        embed.add_field(name="編集後", value=after.content[:1024], inline=False)
        await channel.send(embed=embed)

# 常時ログ：メッセージ削除
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    if LOG_CHANNEL_ID == 0:
        return
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="🗑️ メッセージ削除", color=discord.Color.red())
        embed.add_field(name="ユーザー", value=message.author.mention, inline=True)
        embed.add_field(name="チャンネル", value=message.channel.mention, inline=True)
        embed.add_field(name="内容", value=message.content[:1024], inline=False)
        await channel.send(embed=embed)

# /ban
@tree.command(name="ban", description="指定ユーザーをBANします")
@app_commands.describe(user_id="BANするユーザーID", reason="BAN理由", delete_messages="メッセージ削除: false/true/1dなど")
async def ban(interaction: discord.Interaction, user_id: str, reason: str, delete_messages: str = "false"):
    await interaction.response.defer(ephemeral=True)
    try:
        user = await bot.fetch_user(int(user_id))
        delete_days = 0
        if delete_messages.lower() == "true":
            delete_days = 1
        elif re.match(r"^\d+d$", delete_messages.lower()):
            delete_days = int(delete_messages[:-1])
        elif delete_messages.lower() != "false":
            await interaction.followup.send("❌ `delete_messages` は true / false / 1d の形式で指定してください。")
            return
        await interaction.guild.ban(user, reason=reason, delete_message_days=delete_days)
        await interaction.followup.send(f"✅ ユーザー {user} をBANしました（理由: {reason}）")
    except Exception as e:
        await interaction.followup.send(f"❌ エラーが発生しました: {e}")

# /unban
@tree.command(name="unban", description="BANを解除します")
@app_commands.describe(user_id="BAN解除するユーザーID")
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ ユーザー {user} のBANを解除しました")
    except Exception as e:
        await interaction.response.send_message(f"❌ エラーが発生しました: {e}")

# /kick
@tree.command(name="kick", description="ユーザーをキックします")
@app_commands.describe(user_id="キックするユーザーID")
async def kick(interaction: discord.Interaction, user_id: str):
    try:
        member = await interaction.guild.fetch_member(int(user_id))
        await member.kick()
        await interaction.response.send_message(f"✅ ユーザー {member} をキックしました")
    except Exception as e:
        await interaction.response.send_message(f"❌ エラーが発生しました: {e}")

# /timeout
@tree.command(name="timeout", description="ユーザーをタイムアウトします")
@app_commands.describe(user_id="対象ユーザーID", duration="タイムアウト時間 (例: 10s, 5m, 1h, 1d)", reason="理由")
async def timeout(interaction: discord.Interaction, user_id: str, duration: str, reason: str):
    try:
        member = await interaction.guild.fetch_member(int(user_id))
        match = re.match(r"(\d+)([smhd])", duration)
        if not match:
            await interaction.response.send_message("❌ 時間の形式が正しくありません（例: 10s, 5m, 1h, 1d）")
            return
        value, unit = int(match[1]), match[2]
        seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        timeout_duration = timedelta(seconds=value * seconds)
        await member.timeout_for(timeout_duration, reason=reason)
        await interaction.response.send_message(f"✅ ユーザー {member} を {duration} タイムアウトしました（理由: {reason}）")
    except Exception as e:
        await interaction.response.send_message(f"❌ エラーが発生しました: {e}")

# /user
@tree.command(name="user", description="ユーザー情報を表示します")
@app_commands.describe(user_id="表示するユーザーID")
async def user_info(interaction: discord.Interaction, user_id: str):
    try:
        member = await interaction.guild.fetch_member(int(user_id))
        roles = [role.name for role in member.roles if role.name != "@everyone"]
        embed = discord
