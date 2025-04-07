
import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import datetime
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_CURRENCIES = ["USD", "EUR", "GBP", "JPY"]

def analyze_event(text):
    txt = text.lower()
    if "nfp" in txt or "non-farm" in txt or "emploi" in txt or "chômage" in txt:
        return "🔍 Important pour l'emploi : USD 📈 si positif"
    elif "cpi" in txt or "inflation" in txt:
        return "🔥 Inflation forte → devise 📈, OR 📉"
    elif "gdp" in txt or "pib" in txt:
        return "📈 PIB élevé → devise 📈, indices 📈"
    elif "rate" in txt or "intérêt" in txt:
        return "💰 Hausse des taux → devise 📈, OR 📉"
    elif "retail" in txt or "ventes" in txt:
        return "🛍️ Ventes fortes → devise 📈"
    else:
        return "ℹ️ Surveille la réaction du marché."

def get_forexfactory_events():
    url = "https://www.forexfactory.com/calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    events = soup.select(".calendar__row")
    today = datetime.datetime.utcnow().strftime("%a")
    results = []

    for row in events:
        impact = row.select_one(".impact--high")
        currency = row.select_one(".calendar__currency")
        title = row.select_one(".calendar__event-title")
        time = row.select_one(".calendar__time")
        day = row.select_one(".calendar__day")

        if not impact or not currency or not title or not time or not day:
            continue

        if day.text.strip() != today:
            continue

        curr = currency.text.strip()
        if curr not in TARGET_CURRENCIES:
            continue

        event = title.text.strip()
        hour = time.text.strip()
        analysis = analyze_event(event)
        results.append(f"🕒 {hour} | {curr} | 🔴 {event}\n💡 {analysis}")

    return results

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Erreur : Le salon avec CHANNEL_ID est introuvable.")
    else:
        send_daily_forex_news.start()
        print("🛠️ Scraping ForexFactory chaque jour à 00:01 activé")

@tasks.loop(minutes=1)
async def send_daily_forex_news():
    now = datetime.datetime.now()
    if now.hour == 0 and now.minute == 1:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Salon introuvable.")
            return
        news = get_forexfactory_events()
        if news:
            await channel.send("📊 **Forex Factory - Annonces économiques du jour**\n\n" + "\n\n".join(news))
        else:
            await channel.send("📊 Aucun événement économique à impact élevé trouvé pour aujourd’hui.")

@bot.command()
async def testnews(ctx):
    news = get_forexfactory_events()
    if news:
        await ctx.send("📊 **(Test)** Annonces économiques du jour :\n\n" + "\n\n".join(news[:5]))
    else:
        await ctx.send("📊 Aucun événement économique à impact élevé trouvé pour aujourd’hui.")

@bot.command()
async def analyse(ctx, *, event_text: str):
    await ctx.send(f"💡 Analyse : {analyze_event(event_text)}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong ! Le bot fonctionne.")

bot.run(TOKEN)
