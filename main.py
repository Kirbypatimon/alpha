import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))  # ログチャンネルID

@bot.event
async def on_ready():
    await tree.sync()
    print(f"{bot.user} がログインしました")

# /ban コマンド
@tree.command(name="ban", description="ユーザーをBANします")
@app_commands.describe(userid="ユーザーID", reason="BAN理由", delete_message_days="過去メッセージ削除（日数 0～7）")
async def ban(interaction: discord.Interaction, userid: str, reason: str = "なし", delete_message_days: int = 0):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    user = await bot.fetch_user(int(userid))
    await interaction.guild.ban(user, reason=reason, delete_message_days=delete_message_days)
    await interaction.response.send_message(f"{user} をBANしました。理由: {reason}")

# /kick コマンド
@tree.command(name="kick", description="ユーザーをキックします")
@app_commands.describe(userid="ユーザーID")
async def kick(interaction: discord.Interaction, userid: str):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    member = interaction.guild.get_member(int(userid))
    if member:
        await member.kick()
        await interaction.response.send_message(f"{member} をキックしました。")
    else:
        await interaction.response.send_message("メンバーが見つかりません。")

# /timeout コマンド
@tree.command(name="timeout", description="ユーザーをタイムアウトします")
@app_commands.describe(userid="ユーザーID", duration="1s/1m/1h/1d の形式", reason="理由")
async def timeout(interaction: discord.Interaction, userid: str, duration: str, reason: str = "なし"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return

    unit = duration[-1]
    value = int(duration[:-1])
    if unit == 's':
        delta = timedelta(seconds=value)
    elif unit == 'm':
        delta = timedelta(minutes=value)
    elif unit == 'h':
        delta = timedelta(hours=value)
    elif unit == 'd':
        delta = timedelta(days=value)
    else:
        await interaction.response.send_message("無効な時間形式です（例: 10m, 1h）", ephemeral=True)
        return

    member = interaction.guild.get_member(int(userid))
    if member:
        await member.timeout(delta, reason=reason)
        await interaction.response.send_message(f"{member} を {duration} タイムアウトしました。")
    else:
        await interaction.response.send_message("メンバーが見つかりません。")

# /unban コマンド
@tree.command(name="unban", description="BAN解除します")
@app_commands.describe(userid="ユーザーID")
async def unban(interaction: discord.Interaction, userid: str):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("権限がありません。", ephemeral=True)
        return
    banned_users = await interaction.guild.bans()
    for ban_entry in banned_users:
        if ban_entry.user.id == int(userid):
            await interaction.guild.unban(ban_entry.user)
            await interaction.response.send_message(f"{ban_entry.user} のBANを解除しました。")
            return
    await interaction.response.send_message("指定したユーザーはBANされていません。")

# /log コマンド（確認用）
@tree.command(name="log", description="ログ機能の動作確認")
async def log(interaction: discord.Interaction):
    await interaction.response.send_message("ログ機能は稼働中です。")

# メッセージ削除ログ
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    embed = discord.Embed(
        title="メッセージ削除",
        description=f"{message.author.mention} のメッセージが削除されました。",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.add_field(name="内容", value=message.content or "（埋め込み/ファイル等）", inline=False)
    embed.set_footer(text=f"ユーザーID: {message.author.id}")
    await log_channel.send(embed=embed)

# メッセージ編集ログ
@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    embed = discord.Embed(
        title="メッセージ編集",
        description=f"{before.author.mention} がメッセージを編集しました。",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    embed.add_field(name="編集前", value=before.content or "（なし）", inline=False)
    embed.add_field(name="編集後", value=after.content or "（なし）", inline=False)
    embed.set_footer(text=f"ユーザーID: {before.author.id}")
    await log_channel.send(embed=embed)

# /user コマンド
@tree.command(name="user", description="ユーザー情報を表示します")
@app_commands.describe(userid="ユーザーID")
async def user(interaction: discord.Interaction, userid: str):
    member = interaction.guild.get_member(int(userid))
    if member is None:
        await interaction.response.send_message("指定したユーザーはこのサーバーに存在しません。", ephemeral=True)
        return

    embed = discord.Embed(title=f"{member.name} の情報", color=discord.Color.blurple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="表示名", value=member.display_name, inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="ユーザーネーム", value=member.name, inline=True)
    embed.add_field(name="参加日", value=member.joined_at.strftime("%Y/%m/%d %H:%M"), inline=True)
    embed.add_field(name="登録日", value=member.created_at.strftime("%Y/%m/%d %H:%M"), inline=True)
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    embed.add_field(name="ロール", value=", ".join(roles) if roles else "なし", inline=False)
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
