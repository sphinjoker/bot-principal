import os
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from flask import Flask
from threading import Thread

# Charger les variables d'environnement
load_dotenv()
token = os.getenv('TOKEN_BOT_DISCORD')

# Serveur Flask pour garder le bot actif
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# Lancer le keep_alive
keep_alive()

# Définir les intentions
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Constantes d'identifiants Discord
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
STAFF_EMBED_CHANNEL_ID = 1380988215984394320  

STAFF_ROLES = [
    {"name": "👑 Directeur", "id": 1380987816997032106, "color": 0x0c0c0c},
    {"name": "🛡️ Responsable Staff", "id": 1380987822194036786, "color": 0xf30101},
    {"name": "🟣 Administrateur", "id": 1380987825675042977, "color": 0x80088b},
    {"name": "🟢 Super Modérateur", "id": 1380987827441106955, "color": 0x0ed639},
    {"name": "🔵 Modérateur", "id": 1380987828724568154, "color": 0x4c0daf},
    {"name": "🔵 Helpeur", "id": 1380987829995311145, "color": 0x281dcc},
    {"name": "📣 Community Manager", "id": 1380987832369283234, "color": 0x0c0c0c},
    {"name": "💻 Développeur", "id": 1380987835250770002, "color": 0x0c0c0c}
]

# Événement de démarrage
@bot.event
async def on_ready():
    print(f"✅ Le bot est connecté en tant que {bot.user}")
    update_staff_embed.start()

# Tâche pour mettre à jour l'embed staff
@tasks.loop(minutes=5)
async def update_staff_embed():
    channel = bot.get_channel(STAFF_EMBED_CHANNEL_ID)
    if not channel:
        return
    guild = channel.guild
    embed = discord.Embed(
        title="📋 Liste des Membres du Staff",
        description="Mise à jour automatique toutes les 5 minutes.",
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
    messages = await channel.history(limit=10).flatten()
    existing_msg = None
    for msg in messages:
        if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "📋 Liste des Membres du Staff":
            existing_msg = msg
            break
    if existing_msg:
        await existing_msg.edit(embed=embed)
    else:
        await channel.send(embed=embed)

# Alerte vocale
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == CHANNEL_ID_VOCAL_ATTENDU and before.channel != after.channel:
        channel = bot.get_channel(CHANNEL_ID_TEXTE_ALERTE)
        if channel:
            await channel.send(f"🚨 {member.mention} a rejoint le vocal **{after.channel.name}**. Un douanier va bientôt intervenir.")

# Vue pour le bouton de ticket
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

# Commande staff
@bot.command()
async def staff(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title="📋 Liste des Membres du Staff",
        description="Voici les membres qui encadrent et assurent le bon fonctionnement du serveur.",
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

# Commande ping
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong ! Je suis bien en ligne et prêt à fonctionner.")

# Interaction bouton ticket
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data["custom_id"] == "open_ticket":
        existing = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name}")
        if existing:
            await interaction.response.send_message("🚫 Tu as déjà un ticket ouvert.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
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
            f"👋 Bienvenue {interaction.user.mention} ! Merci d'être là.\n\n"
            "📋 **Merci de répondre aux questions suivantes :**\n"
            "1️⃣ Pseudo Discord\n"
            "2️⃣ Âge\n"
            "3️⃣ Pourquoi veux-tu rejoindre ce serveur ?\n"
            "4️⃣ Quelle armée choisis-tu ? (Hexagonale ou Fédérale Ruzbeque)\n\n"
            "⏳ Un douanier va bientôt arriver.\n\n"
            "🛃 **Commandes disponibles pour les douaniers :**\n"
            "`!accepter @pseudo`\n"
            "`!secondechance @pseudo`\n"
            "`!refuser @pseudo`"
        )
        await interaction.followup.send(f"✅ Ton ticket a été créé : {ticket_channel.mention}", ephemeral=True)

# Commandes douaniers
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
        await ctx.send(f"🔒 Ticket fermé pour : {reason}")
        log_channel = bot.get_channel(CHANNEL_LOG_TICKET_ID)
        if log_channel:
            await log_channel.send(
                f"📁 Ticket `{ctx.channel.name}` fermé par {ctx.author.mention}.\n📄 Raison : {reason}"
            )
        await ctx.channel.delete()

# Commande pour envoyer le bouton de création de ticket
@bot.command()
async def setup_ticket(ctx):
    view = TicketButtonView()
    embed = discord.Embed(
        title="📜 Demande de Whitelist",
        description=(
            "Bienvenue sur le serveur ! 🚀\n\n"
            "**Lis bien le règlement avant de faire une demande. 📘**\n"
            "Clique sur le bouton ci-dessous pour créer un ticket.\n"
            "Un douanier viendra te voir rapidement ! 🛂"
        ),
        color=0x2f3136
    )
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_member_update(before, after):
    if not before.guild:
        return

    channel = bot.get_channel(STAFF_EMBED_CHANNEL_ID)
    if not channel:
        return

    guild = before.guild
    staff_role_ids = [r["id"] for r in STAFF_ROLES]

    # Vérifie si un rôle staff a été ajouté ou retiré
    added_roles = [r for r in after.roles if r not in before.roles and r.id in staff_role_ids]
    removed_roles = [r for r in before.roles if r not in after.roles and r.id in staff_role_ids]

    if added_roles or removed_roles:
        embed = discord.Embed(
            title="📋 Liste des Membres du Staff",
            description="Mise à jour automatique (rôle modifié).",
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

        messages = await channel.history(limit=10).flatten()
        for msg in messages:
            if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "📋 Liste des Membres du Staff":
                await msg.edit(embed=embed)
                break

keep_alive()
bot.run(token)
