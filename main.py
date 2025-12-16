import os
import discord
from discord.ext import commands
import asyncio

# ----------------- Intents Setup -----------------
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Prefix '/' ব্যবহার করা হয়েছে
bot = commands.Bot(command_prefix='/', intents=intents)

# ----------------- Music Control Buttons -----------------
class MusicControls(discord.ui.View):
    def __init__(self, voice_client):
        super().__init__(timeout=None)
        self.vc = voice_client

    # ⏯️ Pause / Resume
    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.primary, emoji="⏯️")
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_playing():
            self.vc.pause()
            await interaction.response.send_message("⏸️ Paused", ephemeral=True)
        elif self.vc.is_paused():
            self.vc.resume()
            await interaction.response.send_message("▶️ Resumed", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Nothing is playing.", ephemeral=True)

    # ⏹️ Stop
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_connected():
            await self.vc.disconnect()
            await interaction.response.send_message("⏹️ Stopped and disconnected.", ephemeral=True)
            self.stop()
        else:
            await interaction.response.send_message("⚠️ Not connected.", ephemeral=True)

    # 🔊 Volume Up
    @discord.ui.button(label="Vol +", style=discord.ButtonStyle.success, emoji="🔊")
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.source and isinstance(self.vc.source, discord.PCMVolumeTransformer):
            self.vc.source.volume = min(self.vc.source.volume + 0.1, 2.0)
            await interaction.response.send_message(
                f"🔊 Volume: {int(self.vc.source.volume * 100)}%", ephemeral=True
            )
        else:
            await interaction.response.send_message("⚠️ Volume adjust করা যাচ্ছে না.", ephemeral=True)

    # 🔉 Volume Down
    @discord.ui.button(label="Vol -", style=discord.ButtonStyle.secondary, emoji="🔉")
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.source and isinstance(self.vc.source, discord.PCMVolumeTransformer):
            self.vc.source.volume = max(self.vc.source.volume - 0.1, 0.0)
            await interaction.response.send_message(
                f"🔉 Volume: {int(self.vc.source.volume * 100)}%", ephemeral=True
            )
        else:
            await interaction.response.send_message("⚠️ Volume adjust করা যাচ্ছে না.", ephemeral=True)

# ----------------- /play Command -----------------
@bot.command(name="play")
async def play(ctx):
    # User voice channel check
    if not ctx.author.voice:
        return await ctx.send("❌ আপনি কোনো ভয়েস চ্যানেলে নেই!")

    voice_channel = ctx.author.voice.channel

    # Audio file detect (Attachment / Reply)
    file_url = None

    if ctx.message.attachments:
        file_url = ctx.message.attachments[0].url
    elif ctx.message.reference:
        ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if ref_msg.attachments:
            file_url = ref_msg.attachments[0].url

    if not file_url:
        return await ctx.send(
            "❌ কোনো অডিও ফাইল পাওয়া যায়নি!\nফাইল অ্যাটাচ করুন অথবা ফাইলের মেসেজে রিপ্লাই দিন।"
        )

    # Voice connect
    if ctx.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)

    if vc.is_playing():
        vc.stop()

    try:
        ffmpeg_opts = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn"
        }

        source = discord.FFmpegPCMAudio(file_url, **ffmpeg_opts)
        transformer = discord.PCMVolumeTransformer(source, volume=1.0)

        vc.play(transformer)

        view = MusicControls(vc)
        filename = file_url.split("/")[-1].split("?")[0]

        await ctx.send(
            f"🎶 **Playing:** `{filename}`\n🎛 **Controls:**",
            view=view
        )

    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

# ----------------- Ready Event -----------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ----------------- Token from Environment Variable -----------------
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN environment variable পাওয়া যায়নি!")

bot.run(TOKEN)
