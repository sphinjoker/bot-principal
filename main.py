import os
import discord
from discord.ext import commands
from discord.ui import View, Button

from flask import Flask
from threading import Thread

# KEEP ALIVE POUR REPLIT
app = Flask('')


@app.route('/')
def home():
    print("Ping reçu sur /"
          )  # Pour debug, montre que Uptimerobot ping bien la route
    return "Bot is running!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# APPEL DE KEEP_ALIVE POUR LANCER LE SERVEUR FLASK EN THREAD
keep_alive()

# Afficher l'URL dans la console Replit
print("➡️ Ouvre cette URL dans ton navigateur :")
print("https://" + os.environ['REPL_SLUG'] + "." + os.environ['REPL_OWNER'] +
      ".repl.co")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# IDs à remplacer par les tiens
CHANNEL_ID_VOCAL_ATTENDU = 1380993881641844777
CHANNEL_ID_TEXTE_ALERTE = 1380993843876593765
CHANNEL_ID_TICKET_BUTTON = 1380993796644409374
ROLE_DOUMANIERS_ID = 1380996565166194738
ROLE_WHITELIST_ID = 1380987873335054467
ROLE_ACCEPTE_ID = 1380987873335054467
ROLE_SECONDE_CHANCE_ID = 1380997181326102660
ROLE_REFUSE_ID = 1380987903760535633
ROLE_NON_WHITELIST_ID = 1380997110966784102
CATEGORY_TICKET_ID = 1380996255664312391
CHANNEL_LOG_TICKET_ID = 1380996350442864701


@bot.event
async def on_ready():
    print(f"✅ Le bot est connecté en tant que {bot.user}")


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == CHANNEL_ID_VOCAL_ATTENDU and before.channel != after.channel:
        channel = bot.get_channel(CHANNEL_ID_TEXTE_ALERTE)
        if channel:
            await channel.send(
                f"🚨 {member.mention} a rejoint le vocal **{after.channel.name}**. Un douanier va bientôt intervenir."
            )


class TicketButtonView(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            Button(label="📩 Faire une demande de Whitelist",
                   style=discord.ButtonStyle.primary,
                   custom_id="open_ticket"))


@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong ! Je suis bien en ligne et prêt à fonctionner.")


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data[
            "custom_id"] == "open_ticket":
        category = discord.utils.get(interaction.guild.categories,
                                     id=CATEGORY_TICKET_ID)
        overwrites = {
            interaction.guild.default_role:
            discord.PermissionOverwrite(view_channel=False),
            interaction.user:
            discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.get_role(ROLE_DOUMANIERS_ID):
            discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        ticket_channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites)
        log_channel = bot.get_channel(CHANNEL_LOG_TICKET_ID)
        if log_channel:
            await log_channel.send(
                f"📨 Ticket ouvert par {interaction.user.mention} dans {ticket_channel.mention}."
            )

        await ticket_channel.send(
            f"👋 Bienvenue {interaction.user.mention} ! Merci d'être là.\n\n"
            "📋 **Merci de répondre aux questions suivantes en copiant et collant tes réponses dans ce salon :**\n"
            "1️⃣ Pseudo Discord (ex: Jean#1234)\n"
            "2️⃣ Âge\n"
            "3️⃣ Pourquoi veux-tu rejoindre ce serveur ?\n"
            "4️⃣ Quelle armée choisis-tu ? (Hexagonale ou Fédérale Ruzbeque)\n\n"
            "⏳ Un douanier arrivera bientôt. En attendant, merci de patienter calmement.\n\n"
            "🛃 **Commandes disponibles pour les douaniers :**\n"
            "`!accepter @pseudo` – Accepter la whitelist ✅\n"
            "`!secondechance @pseudo` – Seconde chance ⚠️\n"
            "`!refuser @pseudo` – Refuser la demande ❌")
        await interaction.response.send_message(
            f"✅ Ton ticket a été créé : {ticket_channel.mention}",
            ephemeral=True)


@bot.command()
async def accepter(ctx, member: discord.Member):
    await member.add_roles(ctx.guild.get_role(ROLE_ACCEPTE_ID))
    await member.remove_roles(ctx.guild.get_role(ROLE_NON_WHITELIST_ID))
    await ctx.send(f"✅ {member.mention} a été accepté(e) dans la whitelist.")


@bot.command()
async def secondechance(ctx, member: discord.Member):
    await member.add_roles(ctx.guild.get_role(ROLE_SECONDE_CHANCE_ID))
    await member.remove_roles(ctx.guild.get_role(ROLE_NON_WHITELIST_ID))
    await ctx.send(f"⚠️ {member.mention} a une seconde chance.")


@bot.command()
async def refuser(ctx, member: discord.Member):
    await member.add_roles(ctx.guild.get_role(ROLE_REFUSE_ID))
    await member.remove_roles(ctx.guild.get_role(ROLE_NON_WHITELIST_ID))
    await ctx.send(f"❌ {member.mention} a été refusé(e).")


@bot.command()
async def close(ctx, *, reason="Aucune raison spécifiée"):
    if ctx.channel.category and ctx.channel.category.id == CATEGORY_TICKET_ID:
        await ctx.send(f"🔒 Ticket fermé pour la raison suivante : {reason}")
        log_channel = bot.get_channel(CHANNEL_LOG_TICKET_ID)
        if log_channel:
            await log_channel.send(
                f"📁 Ticket `{ctx.channel.name}` fermé par {ctx.author.mention}.\n📄 Raison : {reason}"
            )
        await ctx.channel.delete()


async def fermer_ticket(ctx):
    log_channel = bot.get_channel(CHANNEL_LOG_TICKET_ID)
    if log_channel:
        await log_channel.send(
            f"📁 Ticket `{ctx.channel.name}` traité et fermé par {ctx.author.mention}."
        )
    await ctx.channel.delete()


@bot.command()
async def setup_ticket(ctx):
    view = TicketButtonView()
    embed = discord.Embed(
        title="📜 Demande de Whitelist",
        description=
        ("Bienvenue sur le serveur ! 🚀\n\n"
         "**Avant de faire une demande, lis bien le règlement ! 📘**\n"
         "Assure-toi d’avoir bien compris les règles du serveur pour éviter tout malentendu. 🤝\n\n"
         "Clique sur le bouton ci-dessous pour commencer ta demande de whitelist. Un douanier viendra te voir rapidement ! 🛂"
         ),
        color=0x2f3136)
    await ctx.send(embed=embed, view=view)


pip > requirements.txt

keep_alive()
bot.run(os.environ['TOKEN_BOT_DISCORD'])
