import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True
intents.bans = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

@bot.event
async def on_ready():
    print(f"{bot.user} でログインしました")
    try:
        synced = await bot.tree.sync()
        print(f"スラッシュコマンドを {len(synced)} 個同期しました")
    except Exception as e:
        print(f"スラッシュコマンド同期失敗: {e}")

# /timeout コマンド
@bot.tree.command(name="timeout")
@app_commands.describe(user="タイムアウトするユーザー", duration="タイムアウト時間 (例: 10s, 5m, 1h, 1d)", reason="理由")
async def timeout(interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "理由なし"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return
    
    seconds = convert_to_seconds(duration)
    if seconds is None:
        await interaction.response.send_message("時間の形式が不正です（例: 10s, 5m, 1h, 1d）", ephemeral=True)
        return

    await user.timeout(discord.utils.utcnow() + discord.timedelta(seconds=seconds), reason=reason)
    await interaction.response.send_message(f"{user.mention} をタイムアウトしました（{duration}）: {reason}")

# /kick コマンド
@bot.tree.command(name="kick")
@app_commands.describe(user="キックするユーザー", reason="理由")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "理由なし"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return
    await user.kick(reason=reason)
    await interaction.response.send_message(f"{user.mention} をキックしました: {reason}")

# /ban コマンド
@bot.tree.command(name="ban")
@app_commands.describe(user="BANするユーザー", reason="理由", delete_message_days="過去メッセージ削除（0〜7日）")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "理由なし", delete_message_days: int = 0):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return
    await user.ban(reason=reason, delete_message_days=delete_message_days)
    await interaction.response.send_message(f"{user.mention} をBANしました（過去{delete_message_days}日分のメッセージ削除）: {reason}")

# /unban コマンド
@bot.tree.command(name="unban")
@app_commands.describe(user_id="BAN解除するユーザーID")
async def unban(interaction: discord.Interaction, user_id: str):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("権限がありません", ephemeral=True)
        return

    try:
        banned_users = await interaction.guild.bans()
        user = discord.utils.get(banned_users, user__id=int(user_id))
        if user:
            await interaction.guild.unban(user.user)
            await interaction.response.send_message(f"{user.user.name} をBAN解除しました")
        else:
            await interaction.response.send_message("そのユーザーはBANされていません", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)

# /user コマンド
@bot.tree.command(name="user")
@app_commands.describe(user_id="確認したいユーザーID")
async def user(interaction: discord.Interaction, user_id: str):
    try:
        member = await interaction.guild.fetch_member(int(user_id))
        roles = [role.name for role in member.roles if role.name != "@everyone"]
        embed = discord.Embed(title=f"ユーザー情報: {member.name}", color=discord.Color.blue())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="ユーザーネーム", value=member.global_name or "なし", inline=False)
        embed.add_field(name="登録日", value=member.created_at.strftime('%Y-%m-%d %H:%M:%S'), inline=False)
        embed.add_field(name="ロール", value=", ".join(roles) if roles else "なし", inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"ユーザー情報を取得できませんでした: {e}", ephemeral=True)

# /log コマンド
@bot.tree.command(name="log")
async def log(interaction: discord.Interaction):
    await interaction.response.send_message("このチャンネルがログ出力先です")
    global LOG_CHANNEL_ID
    LOG_CHANNEL_ID = interaction.channel.id

# メッセージ削除時ログ
@bot.event
async def on_message_delete(message):
    if message.author.bot or message.guild is None:
        return
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title="メッセージ削除", color=discord.Color.red())
        embed.add_field(name="ユーザー", value=f"{message.author} ({message.author.id})", inline=False)
        embed.add_field(name="内容", value=message.content or "（ファイル/埋め込みのみ）", inli
