import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ui import View, Button
from flask import Flask
from threading import Thread

# Chargement des variables d'environnement
load_dotenv()
token = os.getenv('TOKEN_BOT_DISCORD')

# Flask pour le keep_alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# Intents et initialisation du bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Paramètres personnalisés (à ajuster selon ton serveur)
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

STAFF_ROLES = [
    {"name": "👑 Directeur", "id": 1380987816997032106, "color": 0x0c0c0c},
    {"name": "🛡️ Responsable Staff", "id": 1380987822194036786, "color": 0xf30101},
    {"name": "🟣 Administrateur", "id": 1380987825675042977, "color": 0x80088b},
    {"name": "🟢 Super Modérateur", "id": 1380987827441106955, "color": 0x0ed639},
    {"name": "🔵 Modérateur", "id": 1380987828724568154, "color": 0x4c0daf},
    {"name": "🔵 Helpeur", "id": 1380987829995311145, "color": 0x281dcc},
    {"name": "📣 Community Manager", "id": 1380987832369283234, "color": 0x0c0c0c},
    {"name": "💻 Développeur", "id": 1380987835250770002, "color": 0x0c0c0c},
]

@bot.event
async def on_ready():
    print(f"✅ Le bot est connecté en tant que {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == CHANNEL_ID_VOCAL_ATTENDU and before.channel != after.channel:
        channel = bot.get_channel(CHANNEL_ID_TEXTE_ALERTE)
        if channel:
            await channel.send(f"🚨 {member.mention} a rejoint le vocal **{after.channel.name}**. Un douanier va bientôt intervenir.")

class TicketButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            Button(
                label="📩 Faire une demande de Whitelist",
                style=discord.ButtonStyle.primary,
                custom_id="open_ticket"
            )
        )

@bot.command()
async def staff(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title="📋 Liste des Membres du Staff",
        description="Voici les membres qui encadrent le serveur.",
        color=0x2f3136
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)

    top_color = None

    for role_info in STAFF_ROLES:
        role = guild.get_role(role_info["id"])
        if role:
            members = [m.mention for m in role.members]
            if members:
                if not top_color:
                    top_color = role_info["color"]
                embed.add_field(
                    name=f"{role_info['name']} ・ {len(members)} membre(s)",
                    value="\n".join(members),
                    inline=False
                )

    if top_color:
        embed.color = top_color

    embed.set_footer(text="Affiché par le bot", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong ! Je suis bien en ligne et prêt à fonctionner.")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data["custom_id"] == "open_ticket":
        category = discord.utils.get(interaction.guild.categories, id=CATEGORY_TICKET_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.get_role(ROLE_DOUMANIERS_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        ticket_channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        log_channel = bot.get_channel(CHANNEL_LOG_TICKET_ID)
        if log_channel:
            await log_channel.send(f"📨 Ticket ouvert par {interaction.user.mention} dans {ticket_channel.mention}.")
        await ticket_channel.send(
            f"👋 Bienvenue {interaction.user.mention} !\n\n"
            "📋 **Réponds aux questions suivantes :**\n"
            "1️⃣ Pseudo Discord\n"
            "2️⃣ Âge\n"
            "3️⃣ Pourquoi veux-tu rejoindre ?\n"
            "4️⃣ Hexagonale ou Fédérale Ruzbeque ?\n\n"
            "⏳ Un douanier arrivera bientôt.\n\n"
            "🛃 Commandes douaniers :\n"
            "`!accepter @pseudo` – Accepter ✅\n"
            "`!secondechance @pseudo` – 2ème chance ⚠️\n"
            "`!refuser @pseudo` – Refuser ❌"
        )
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {ticket_channel.mention}", ephemeral=True)

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
        await ctx.send(f"🔒 Ticket fermé : {reason}")
        log_channel = bot.get_channel(CHANNEL_LOG_TICKET_ID)
        if log_channel:
            await log_channel.send(
                f"📁 Ticket `{ctx.channel.name}` fermé par {ctx.author.mention}.\n📄 Raison : {reason}"
            )
        await ctx.channel.delete()

@bot.command()
async def setup_ticket(ctx):
    view = TicketButtonView()
    embed = discord.Embed(
        title="📜 Demande de Whitelist",
        description=(
            "Bienvenue sur le serveur ! 🚀\n\n"
            "**Avant de faire une demande, lis bien le règlement ! 📘**\n\n"
            "Clique sur le bouton ci-dessous pour commencer ta demande."
        ),
        color=0x2f3136
    )
    await ctx.send(embed=embed, view=view)

# Lancement du bot
bot.run(token)
