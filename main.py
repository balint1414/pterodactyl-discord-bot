import discord, os, requests, sqlite3
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

bot = discord.Bot()
db = sqlite3.connect("db.db")
owner_ids = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id.isdigit()]
setup_command_id = None
async def format_date(date_str):
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    unix = int(dt.timestamp())
    return f"<t:{unix}:f>"
@bot.event
async def on_ready():
    global setup_command_id
    print(f"Started running on {len(bot.guilds)} servers.")
    for cmd in bot.application_commands:
        if cmd.name == "setup":
            setup_command_id = cmd.id

def need_to_setup_embed():
    return discord.Embed(
        title="Invalid token",
        description=f"You have not set a valid Pterodactyl token yet. To set the token, use the </setup:{setup_command_id}> command",
        color=discord.Color.red()
    )
noPermEmbed = discord.Embed(title="No permission", description="You don't have permission to use this command.", color=discord.Color.red())

list = bot.create_group("list", "Fetch datas from Pterodactyl")

@list.command(description="List all users")
async def users(ctx):
    await ctx.response.defer(ephemeral=True)
    if ctx.author.id not in owner_ids:
        await ctx.respond(embed=noPermEmbed, ephemeral=True)
        return
    try:
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/users", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY"), "Accept": "Application/vnd.pterodactyl.v1+json"})
        embed = discord.Embed(title="Users", description="List of all users", color=discord.Color.green())
        for user in r.json()["data"]:
            embed.add_field(name=user["attributes"]["username"], value=f"ID: ```{user['attributes']['id']}\nEmail: {user['attributes']['email']}```", inline=True)
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception as e:
        errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
        await ctx.respond(embed=errorEmbed, ephemeral=True)
        return

@list.command(description="List all servers")
async def servers(ctx):
    await ctx.response.defer(ephemeral=True)
    if ctx.author.id not in owner_ids:
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE userid = ?", (ctx.author.id,))
        user = cur.fetchone()
        if not user:
            await ctx.respond(embed=need_to_setup_embed(), ephemeral=True)
            return
        else: 
            try:
                token = user[1]
                if not token:
                    await ctx.respond(embed=need_to_setup_embed(), ephemeral=True)
                    return
                r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/client", headers={"Authorization":"Bearer " + token, "Accept": "Application/vnd.pterodactyl.v1+json"})
                embed = discord.Embed(title="Servers", description=f"We found {len(r.json()['data'])} servers", color=discord.Color.green())
                for server in r.json()["data"]:
                    embed.add_field(name=server["attributes"]["name"], value=f"```{server['attributes']['identifier']}```", inline=True)
                await ctx.respond(embed=embed, ephemeral=True)
                return
            except Exception as e:
                errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
                await ctx.respond(embed=errorEmbed, ephemeral=True)
                return
    try:
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/servers", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY"), "Accept": "Application/vnd.pterodactyl.v1+json"})
        embed = discord.Embed(title="Servers", description=f"We found {len(r.json()['data'])} servers", color=discord.Color.green())
        embed.set_footer(text="You are an admin, so you can see all servers.")
        for server in r.json()["data"]:
            embed.add_field(name=server["attributes"]["name"], value=f"```{server['attributes']['identifier']}```", inline=True)
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception as e:
        errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
        await ctx.respond(embed=errorEmbed, ephemeral=True)
        return

@list.command(description="List all nodes")
async def nodes(ctx):
    await ctx.response.defer(ephemeral=True)
    if ctx.author.id not in owner_ids:
        await ctx.respond(embed=noPermEmbed, ephemeral=True)
        return
    try:
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/nodes", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY"), "Accept": "Application/vnd.pterodactyl.v1+json"})
        embed = discord.Embed(title="Nodes", description=f"We found {len(r.json()['data'])} nodes", color=discord.Color.green())
        for node in r.json()["data"]:
            embed.add_field(name=node["attributes"]["name"], value=f"```FQDN: {node['attributes']['fqdn']}\nMemory: {node['attributes']['allocated_resources']['memory']}/{node['attributes']['memory']} MiB\nDisk: {node['attributes']['allocated_resources']['disk']}/{node['attributes']['disk']} MiB```", inline=False)
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception as e:
        errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
        await ctx.respond(embed=errorEmbed, ephemeral=True)
        return

@bot.command(description="Setup your Pterodactyl token")
async def setup(ctx, token: str):
    await ctx.response.defer(ephemeral=True)
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE userid = ?", (ctx.author.id,))
    user = cur.fetchone()
    if user:
        await ctx.respond(embed=discord.Embed(title="Error", description="You have already set up your Pterodactyl token.", color=discord.Color.red()), ephemeral=True)
        return
    try:
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/client", headers={"Authorization":"Bearer " + token, "Accept": "Application/vnd.pterodactyl.v1+json"})
        if r.status_code == 200:
            cur = db.cursor()
            cur.execute("INSERT INTO users (userid, token) VALUES (?, ?)", (ctx.author.id, token))
            db.commit()
            await ctx.respond(embed=discord.Embed(title="Success", description="Your Pterodactyl token has been set up successfully.", color=discord.Color.green()), ephemeral=True)
        else:
            await ctx.respond(embed=discord.Embed(title="Error", description="You need to provide a valid token.", color=discord.Color.red()), ephemeral=True)
    except Exception as e:
        errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
        await ctx.respond(embed=errorEmbed, ephemeral=True)

async def is_valid_choice(type: str, user_id: int, choice: str):
    if type == 'server':
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE userid = ?", (user_id,))
        user = cur.fetchone()
        if not user:
            return False
        token = user[1]
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/client", headers={
            "Authorization": "Bearer " + token,
            "Accept": "Application/vnd.pterodactyl.v1+json"
        })
        if r.status_code != 200:
            return False
        servers = r.json()["data"]
        return any(str(server["attributes"]["identifier"]) == choice for server in servers)

    elif type == 'user':
        if user_id not in owner_ids:
            return False
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/users", headers={
            "Authorization": "Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY"),
            "Accept": "Application/vnd.pterodactyl.v1+json"
        })
        if r.status_code != 200:
            return False
        users = r.json()["data"]
        return any(str(user["attributes"]["id"]) == choice for user in users)

    return False

async def getUserOrServer(ctx: discord.AutocompleteContext):
    options = getattr(ctx, "options", None)
    type = options.get('type', None) if options else None
    print(type)
    if type == 'server':
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE userid = ?", (ctx.interaction.user.id,))
        user = cur.fetchone()
        if not user:
            return []
        token = user[1]
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/client", headers={"Authorization":"Bearer " + token, "Accept": "Application/vnd.pterodactyl.v1+json"})
        print(r.status_code)
        print(r.text)
        servers = r.json()["data"]
        return [discord.OptionChoice(name=str(server["attributes"]["name"]), value=str(server["attributes"]["identifier"])) for server in servers]
    elif type == 'user':
        if ctx.interaction.user.id not in owner_ids:
            return []
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/users", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY"), "Accept": "Application/vnd.pterodactyl.v1+json"})
        users = r.json()["data"]
        return [discord.OptionChoice(name=str(user["attributes"]["username"]), value=str(user["attributes"]["id"])) for user in users]

@bot.command(name="info", description="Get information about a user or server")
async def user(
    ctx,
    type: discord.Option(str, choices=['server', 'user']),
    choice: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(getUserOrServer))
):
    await ctx.response.defer(ephemeral=True)
    if not await is_valid_choice(type, ctx.author.id, choice):
        await ctx.respond(embed=discord.Embed(
            title="Invalid choice",
            description=f"Please select a valid option from the autocomplete list. Or maybe you need to set up your token first? Use the </setup:{setup_command_id}> command to set it up.",
            color=discord.Color.red()
        ), ephemeral=True)
        return

    if ctx.author.id not in owner_ids and type == 'user':
        await ctx.respond(embed=noPermEmbed, ephemeral=True)
        return
    if type == 'server':
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE userid = ?", (ctx.author.id,))
        user = cur.fetchone()
        if not user:
            await ctx.respond(embed=need_to_setup_embed(), ephemeral=True)
            return
        token = user[1]
        try:
            r = requests.get(os.getenv("PTERODACTYL_URL") + f"/api/client/servers/{choice}", headers={"Authorization":"Bearer " + token, "Accept": "Application/vnd.pterodactyl.v1+json"})
            print(r.status_code)
            print(r.text)
            if r.status_code != 200:
                await ctx.respond(embed=discord.Embed(title="Error", description="Server not found or invalid server ID.", color=discord.Color.red()), ephemeral=True)
                return
            server_data = r.json()["attributes"]
            embed = discord.Embed(title="Server Information", description=f"Information for server ID {choice}", color=discord.Color.green())
            embed.add_field(name="Name", value=server_data["name"], inline=True)
            embed.add_field(name="Identifier", value=server_data["identifier"], inline=True)
            embed.add_field(name="Node", value=server_data["node"], inline=True)
            embed.add_field(name="Description", value=server_data["description"] or "No description provided", inline=True)
            embed.add_field(name="UUID", value=server_data["uuid"], inline=True)
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
            await ctx.respond(embed=errorEmbed, ephemeral=True)
    elif type == 'user':
        try:
            r = requests.get(os.getenv("PTERODACTYL_URL") + f"/api/application/users/{choice}", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY"), "Accept": "Application/vnd.pterodactyl.v1+json"})
            if r.status_code != 200:
                await ctx.respond(embed=discord.Embed(title="Error", description="User not found or invalid user ID.", color=discord.Color.red()), ephemeral=True)
                return
            user_data = r.json()["attributes"]
            embed = discord.Embed(title="User Information", description=f"Information for user ID {choice}", color=discord.Color.green())
            embed.add_field(name="Username", value=user_data["username"], inline=True)
            embed.add_field(name="Email", value=user_data["email"], inline=True)
            embed.add_field(name="Full Name", value=f"{user_data['first_name']} {user_data['last_name']}", inline=True)
            embed.add_field(name="Created At", value=await format_date(user_data["created_at"]), inline=True)
            embed.add_field(name="Updated At", value=await format_date(user_data["updated_at"]), inline=True)
            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
            await ctx.respond(embed=errorEmbed, ephemeral=True)
bot.run(os.getenv("TOKEN"))