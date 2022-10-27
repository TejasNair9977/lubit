from discord.ext import commands
from wavelink.ext import spotify
from discord.ext import commands
import discord
import os
import wavelink

GUILDS = [1027207617912782871, 1028379963721785504]
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


class ControlPanel(discord.ui.View):

  def __init__(self, vc, ctx):
    super().__init__()
    self.vc = vc
    self.ctx = ctx

  @discord.ui.button(label="Resume/Pause", style=discord.ButtonStyle.blurple)
  async def resume_and_pause(self, button: discord.ui.Button,
                             interaction: discord.Interaction):
    if not interaction.user == self.ctx.author:
      return await interaction.response.send_message(
        "You can't do that. Run the command yourself to use this buttons",
        ephemeral=True)
    for child in self.children:
      child.disabled = False
    if self.vc.is_paused:
      await self.vc.resume()
      await interaction.message.edit(content="Resumed", view=self)
    else:
      await self.vc.pause()
      await interaction.message.edit(content="Paused", view=self)

  @discord.ui.button(label="Queue", style=discord.ButtonStyle.blurple)
  async def queue(self, button: discord.ui.Button,
                  interaction: discord.Interaction):
    if not interaction.user == self.ctx.author:
      return await interaction.response.send_message(
        "You can't do that. Run the command yourself to use this buttons",
        ephemeral=True)
    for child in self.children:
      child.disabled = False
    button.disabled = True
    if self.vc.queue.is_empty:
      return await interaction.response.send_message("Queue is empty",
                                                     ephemeral=True)

    em = discord.Embed(title="Queue")
    queue = self.vc.queue.copy()
    song_count = 0
    for song in queue:
      song_count += 1
    em.add_field(name=f"Song Num {str(song_count)}", value=f"{song.title}")
    await interaction.message.edit(embed=em, view=self)


@bot.event
async def on_ready():
  print("Bot is up and ready!")
  bot.loop.create_task(node_connect())
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")
  except Exception as e:
    print(e)

  @discord.ui.button(label="Queue", style=discord.ButtonStyle.blurple)
  async def queue(self, button: discord.ui.Button,
                  interaction: discord.Interaction):
    if not interaction.user == self.ctx.author:
      return await interaction.response.send_message(
        "You can't do that. Run the command yourself to use this buttons",
        ephemeral=True)
    for child in self.children:
      child.disabled = False
    button.disabled = True
    if self.vc.queue.is_empty:
      return await interaction.response.send_message("Queue is empty",
                                                     ephemeral=True)

    em = discord.Embed(title="Queue")
    queue = self.vc.queue.copy()
    song_count = 0
    for song in queue:
      song_count += 1
    em.add_field(name=f"Song Num {str(song_count)}", value=f"{song.title}")
    await interaction.message.edit(embed=em, view=self)

  @discord.ui.button(label="Skip", style=discord.ButtonStyle.blurple)
  async def skip(self, button: discord.ui.Button,
                 interaction: discord.Interaction):
    if not interaction.user == self.ctx.author:
      return await interaction.response.send_message(
        "You can't do that. Run the command yourself to use this buttons",
        ephemeral=True)
    for child in self.children:
      child.disabled = False
    button.disabled = True
    if self.vc.queue.is_empty:
      return await interaction.response.send_message("Queue is empty",
                                                     ephemeral=True)
    try:
      next_song = self.vc.queue.get()
      await self.vc.play(next_song)
      await interaction.message.edit(content=f"Now Playing `{next_song}`",
                                     view=self)
    except Exception:
      return await interaction.response.send_message("Queue is empty",
                                                     ephemeral=True)

  @discord.ui.button(label="Disconnect", style=discord.ButtonStyle.blurple)
  async def Disconnect(self, button: discord.ui.Button,
                       interaction: discord.Interaction):
    if not interaction.user == self.ctx.author:
      return await interaction.response.send_message(
        "You can't do that. Run the command yourself to use this buttons",
        ephemeral=True)
    for child in self.children:
      child.disabled = True
    await self.vc.disconnect()
    await interaction.message.edit(content="Disconnect :P", view=self)


@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
  print(f"Node {node.identifier} is ready!")


async def node_connect():
  await bot.wait_until_ready()

  await wavelink.NodePool.create_node(
    bot=bot,
    host='lava.link',
    port=80,
    password='dismusic',
    spotify_client=spotify.SpotifyClient(
      client_id="caa96fa2517b40db8bbb482d1ee29880",
      client_secret="79010bc93a6c48a48f060e037e38a015"))


@bot.event
async def on_wavelink_track_end(player: wavelink.Player,
                                track: wavelink.YouTubeTrack, reason):
  try:
    guild = player.guild
    vc: player = guild.voice_client

  except discord.HTTPException:
    interaction = player.interaction
    vc: player = interaction.guild.voice_client

  if vc.loop:
    return await vc.play(track)
  if vc.queue.is_empty:
    return await vc.disconnect()

  next_song = vc.queue.get()
  await vc.play(next_song)
  try:
    await interaction.response.send_message(f"Now playing: {next_song.title}")
  except discord.HTTPException:
    await interaction.send(f"Now playing: {next_song.title}")


@bot.command()
async def panel(ctx: commands.Context):
  em=None
  if not ctx.voice_client:
    vc: wavelink.Player = await ctx.author.voice.channel.connect(
      cls=wavelink.Player)
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  # if vc.is_playing():
  #   em = discord.Embed(
  #   title="Music Panel",
  #   description="Control the bot by clicking the buttons below")
  # view = ControlPanel(vc, ctx)
  # await ctx.send(embed=em, view=view)

  em = discord.Embed(
    title="Music Panel",
    description="Control the bot by clicking the buttons below")
  view = ControlPanel(vc, ctx)
  await ctx.send(embed=em, view=view)


@bot.command()
async def play(ctx: commands.Context, search: str):
  search = await wavelink.YouTubeTrack.search(query=search, return_first=True)
  if not ctx.voice_client:
    vc: wavelink.Player = await ctx.author.voice.channel.connect(
      cls=wavelink.Player)
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  await vc.play(search)
  await ctx.send(f'Playing `{search.title}`....Nice Song btw')
  if vc.queue.is_empty and vc.is_playing():
    await vc.play(search)
    await ctx.send(f"Now playing: {search.title}")
  else:
    await vc.queue.put_wait(search)
    await ctx.send(f"Added `{search.title}` to the queue")
    vc.ctx = ctx
    # vc.interaction = interaction
  if vc.loop: return
  setattr(vc, "loop", False)


@bot.tree.command(name="play")
async def play(interaction: discord.Interaction, search: str):
  search = await wavelink.YouTubeTrack.search(query=search, return_first=True)
  if not interaction.guild.voice_client:
    vc: wavelink.Player = await interaction.user.voice.channel.connect(
      cls=wavelink.Player)
  elif not getattr(interaction.user.voice, "channel", None):
    return await interaction.response.send_message(
      "join a voice channel first lol")
  else:
    vc: wavelink.Player = interaction.guild.voice_client
  await vc.play(search)
  await interaction.response.send_message(
    f'Playing `{search.title}`....Nice Song btw')
  if vc.queue.is_empty and vc.is_playing():
    await vc.play(search)
    await interaction.response.send_message(f"Now playing: {search.title}")
  else:
    await vc.queue.put_wait(search)
    await interaction.response.send_message(
      f"Added `{search.title}` to the queue")
    # vc.ctx = ctx
    vc.interaction = interaction
  if vc.loop: return
  setattr(vc, "loop", False)


## Only god knows the error
# @bot.tree.command(name="play", description="Plays a music")
# async def play(interaction: discord.Interaction, ctx: commands.Context, *,
#                search: wavelink.YouTubeTrack):
#   search = await wavelink.YouTubeTrack.search(query=search, return_first=True)
#   if not interaction.guild.voice_client:
#     vc: wavelink.Player = await interaction.guild.voice.connect(
#       cls=wavelink.Player)
#   elif not getattr(interaction.author.voice, "channel", None):
#     return await interaction.send("join a voice channel first lol")
#   else:
#     vc: wavelink.Player = interaction.guild.voice_client
#     await vc.play(search)
#     await interaction.send(f'Playing `{search.title}`....Nice Song btw')
#   if vc.queue.is_empty and vc.is_playing():
#     await vc.play(search)
#     await interaction.send(f"Now playing: {search.title}")
#   else:
#     await vc.queue.put_wait(search)
#     await interaction.send(f"Added `{search.title}` to the queue")
#   # vc.ctx = ctx
#   vc.interaction = interaction
#   if vc.loop: return
#   setattr(vc, "loop", False)


@bot.command()
async def pause(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send(
      "You are not playing any music rn.... so what will i pause")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  await vc.pause()
  await ctx.send("paused your music :D")


@bot.command()
async def resume(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send(
      "You are not playing any music rn.... so what will i resume")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  await vc.resume()
  await ctx.send("Aaay your music is back again!")


@bot.command()
async def stop(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send(
      "You are not playing any music rn.... so what will i stop")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  await vc.stop()
  await ctx.send("stopped the song")


@bot.command()
async def disconnect(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send(
      "You are not playing any music rn.... so what will i pause")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  await vc.disconnect()
  await ctx.send("Disconnected....CYA later Bye")


@bot.command()
async def loop(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send(
      "You are not playing any music rn.... so what will i pause")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  try:
    vc.loop ^= True
  except Exception:
    setattr(vc, "loop", False)
  if vc.loop:
    return await ctx.send("loop is now enabled")
  else:
    return await ctx.send("Loop is now disabled")


@bot.command()
async def queue(ctx: commands.Context):
  if not ctx.voice_client:
    return await ctx.send(
      "You are not playing any music rn.... so what will i pause")
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  if vc.queue.is_empty:
    return await ctx.send("Queue is empty")

  em = discord.Embed(title="Queue")
  queue = vc.queue.copy()
  song_count = 0
  for song in queue:
    song_count += 1
    em.add_field(name=f"Song Num {song_count}", value=f"{song.title}")
  return await ctx.send(embed=em)


@bot.command()
async def splay(ctx: commands.Context, *, search: str):
  if not ctx.voice_client:
    vc: wavelink.Player = await ctx.author.voice.channel.connect(
      cls=wavelink.Player)
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
  # Useful for determining the type of search and the ID...


# If the URL decoded is an unusable type e.g artist, spotify.SpotifySearchType.unusable will be returned...
# If the URL is not a valid Spotify URL, None is returned.

  decoded = spotify.decode_url(search)
  if decoded is not None:
    print(decoded['type'], decoded['id'])

    # tracks = await spotify.SpotifyTrack.search(query=search)

    track = await spotify.SpotifyTrack.search(query=search, return_first=True)
    if vc.queue.is_empty and not vc.is_playing():
      try:
        await vc.play(track)
        await ctx.send(f"Now playing: `{track.title}`")
      except Exception as e:
        await ctx.send("Please enter a spotify **song url**")
        return print(e)
    else:
      await vc.queue.put_wait(track)
      await ctx.send(f"Added `{track.title}` to the queue")
    vc.ctx = ctx


@bot.command()
async def slist(ctx: commands.Context, *, search: str):
  decoded = None
  if not ctx.voice_client:
    vc: wavelink.Player = await ctx.author.voice.channel.connect(
      cls=wavelink.Player)
  elif not getattr(ctx.author.voice, "channel", None):
    return await ctx.send("join a voice channel first lol")
  else:
    vc: wavelink.Player = ctx.voice_client
    decoded = spotify.decode_url(search)
  if decoded is not None:
    print(decoded['type'], decoded['id'])
    async for track in spotify.SpotifyTrack.iterator(
        query=search, type=spotify.SpotifySearchType.album):
      if vc.queue.is_empty and not vc.is_playing():
        try:
          await vc.play(track)
          await ctx.send(f"Now playing: `{track.title}`")
        except Exception as e:
          await ctx.send("Please enter a spotify **song url**")
          return print(e)
    else:
      await vc.queue.put_wait(track)
      await ctx.send(f"Added `{track.title}` to the queue")
    vc.ctx = ctx


bot.run(os.environ['TOKEN'])
