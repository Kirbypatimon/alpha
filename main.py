import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from datetime import timedelta
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True
intents.guilds = True

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# --- ログ機能（常時実行） ---
@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    embed = discord.Embed(title="メッセージ編集", color=discord.Color.orange())
    embed.add_field(name="ユーザー", value=before.author.mention)
    embed.add_field(name="チャンネル", value=before.channel.mention)
    embed.add_field(name="編集前", value=before.content or "空")
    embed.add_field(name="編集後", value=after.content or "空")
    await before.channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    embed = discord.Embed(title="メッセージ削除", color=discord.Color.red())
    embed.add_field(name="ユーザー", value=message.author.mention)
    embed.add_field(name="チャンネル", value=message.channel.mention)
    embed.add_field(name="内容", value=message.content or "空")
    await message.channel.send(embed=embed)

# --- コマンド登録 ---
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot起動: {bot.user}")

# --- /ban コマンド ---
@tree.command(name="ban", description="ユーザーをBANします")
@app_commands.describe(userid="ユーザーID", reason="理由", delete_message_days="true / false / 日数(例: 1d)")
async def ban_user(interaction: discord.Interaction, userid: str, reason: str, delete_message_days: str):
    try:
        user = await bot.fetch_user(int(userid))
        delete_days = 0
        if delete_message_days.lower() == "true":
            delete_days = 1
        elif delete_message_days.lower().endswith("d"):
            delete_days = int(delete_message_days[:-1])
        elif delete_message_days.lower() == "false":
            delete_days = 0

        await interaction.guild.ban(user, reason=reason, delete_message_days=delete_days)
        await interaction.response.send_message(f"{user} をBANしました。理由: {reason}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"BANに失敗: {e}", ephemeral=True)

# --- /kick コマンド ---
@tree.command(name="kick", description="ユーザーをキックします")
@app_commands.describe(userid="ユーザーID")
async def kick_user(interaction: discord.Interaction, userid: str):
    try:
        member = await interaction.guild.fetch_member(int(userid))
        await member.kick(reason="Kickコマンドによる実行")
        await interaction.response.send_message(f"{member} をキックしました", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"キック失敗: {e}", ephemeral=True)

# --- /timeout コマンド ---
@tree.command(name="timeout", description="ユーザーをタイムアウトします")
@app_commands.describe(userid="ユーザーID", duration="例: 10s, 5m, 2h, 1d", reason="理由")
async def timeout_user(interaction: discord.Interaction, userid: str, duration: str, reason: str):
    try:
        member = await interaction.guild.fetch_member(int(userid))
        seconds = int(duration[:-1])
        unit = duration[-1]

        delta = {
            's': timedelta(seconds=seconds),
            'm': timedelta(minutes=seconds),
            'h': timedelta(hours=seconds),
            'd': timedelta(days=seconds)
        }.get(unit)

        if not delta:
            raise ValueError("時間形式が無効です (例: 10s, 5m, 2h, 1d)")

        await member.timeout(delta, reason=reason)
        await interaction.response.send_message(f"{member} を {duration} タイムアウトしました", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"タイムアウト失敗: {e}", ephemeral=True)

# --- /unban コマンド ---
@tree.command(name="unban", description="ユーザーのBANを解除します")
@app_commands.describe(userid="ユーザーID")
async def unban_user(interaction: discord.Interaction, userid: str):
    try:
        user = await bot.fetch_user(int(userid))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"{user} のBANを解除しました", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"BAN解除失敗: {e}", ephemeral=True)

# --- /user コマンド ---
@tree.command(name="user", description="ユーザー情報を表示します")
@app_commands.describe(userid="ユーザーID")
async def user_info(interaction: discord.Interaction, userid: str):
    try:
        member = await interaction.guild.fetch_member(int(userid))
        embed = discord.Embed(title="ユーザー情報", color=discord.Color.green())
        embed.add_field(name="名前", value=member.name, inline=True)
        embed.add_field(name="ユーザー名", value=member.display_name, inline=True)
        embed.add_field(name="ユーザーID", value=member.id, inline=False)
        embed.add_field(name="登録日", value=member.created_at.strftime('%Y/%m/%d %H:%M:%S'), inline=False)
        roles = [role.name for role in member.roles if ro
