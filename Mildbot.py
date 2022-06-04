import mildom
import m3u8
import discord
from discord.ext import tasks
import asyncio
import collections

#Settings
liveID = 10105254
TOKEN = "Token"

PauseSign = 0

class VideoQueue:
    
    Audio_Queue = collections.deque([discord.AudioSource()])
    Audio_Uri_Queue = collections.deque([""])

    async def add(self):
        global liveID
        live_stream = mildom.LiveStream(liveID)
        video_stream_links = live_stream.dvr_videos
        playlist = m3u8.load(video_stream_links[0]["complete_url"])
        segment = playlist.segments[-1]
        uri = segment.absolute_uri
        if self.Audio_Uri_Queue[-1] != uri:
            self.Audio_Queue.append(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(uri, executable="ffmpeg"), volume = 10))
            self.Audio_Uri_Queue.append(uri)
            print(uri, len(self.Audio_Queue))
            if len(self.Audio_Uri_Queue) >= 4:
                self.Audio_Queue.popleft()
                self.Audio_Uri_Queue.popleft()
        return
    async def play(self, message, uri):
        global PauseSign
        x = self.Audio_Uri_Queue[0]
        if len(self.Audio_Queue) <= 1:
            print(len(self.Audio_Queue), "は再生するには短すぎます!音声の予備が蓄えられるまで放送を停止します。")
            await asyncio.sleep(2)
            await self.play(message, "")
            return
        elif PauseSign == 1:
            return
        self.Audio_Uri_Queue.popleft()
        message.guild.voice_client.play(
            self.Audio_Queue.popleft(),
            after=lambda ex:asyncio.run(self.play(message, x))
        )
        return

async def StreamSound(ID, message):
    await que.add()
    await que.play(message, "")
    


# 接続に必要なオブジェクトを生成
client = discord.Client()
que = VideoQueue()

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')

@tasks.loop(seconds=0.5)
async def loop():
    await que.add()

@client.event
async def on_message(message):
    global PauseSign
    if message.author.bot:
        return

    if message.content == ("help"):
        await message.channel.send("join でVCに接続し、play で再生を開始、pauseで一時停止します。最大で20秒程度の遅延が発生する場合があります。")

    if message.content == ("join"):
        await message.author.voice.channel.connect()
        await message.channel.send("接続しました。")

    if message.content == ("play"):
        await message.channel.send("流します。")
        await que.add()
        await que.play(message, "")

    if message.content == ("pause"):
        await message.channel.send("中断します。")
        PauseSign = 1

# Botの起動とDiscordサーバーへの接続
loop.start()
client.run(TOKEN)
