import discord, os, requests, sqlite3
from dotenv import load_dotenv
load_dotenv()

bot = discord.Bot()
db = sqlite3.connect("db.db")
owner_ids = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id.isdigit()]
noPermEmbed = discord.Embed(title="No permission", description="You don't have permission to use this command.", color=discord.Color.red())
needToSetup = discord.Embed(title="Invalid token", description="You have not set a valid Pterodactyl token yet. To set the token, use the /setup command", color=discord.Color.red())
@bot.event
async def on_ready():
    print(f"Started running on {len(bot.guilds)} servers.")

list = bot.create_group("list", "Fetch datas from Pterodactyl")

@list.command(description="List all users")
async def users(ctx):
    await ctx.response.defer(ephemeral=True)
    if ctx.author.id not in owner_ids:
        await ctx.respond(embed=noPermEmbed, ephemeral=True)
        return
    try:
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/users", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY")})
        embed = discord.Embed(title="Users", description="List of all users", color=discord.Color.green())
        for user in r.json()["data"]:
            embed.add_field(name=user["attributes"]["username"], value=f"ID: {user['attributes']['id']}\nEmail: {user['attributes']['email']}\nFull name: {user['attributes']['first_name']} {user['attributes']['last_name']}", inline=True)
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
            await ctx.respond(embed=needToSetup, ephemeral=True)
            return
        else: 
            try:
                token = user[1]
                if not token:
                    await ctx.respond(embed=needToSetup, ephemeral=True)
                    return
                r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/client", headers={"Authorization":"Bearer " + token})
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
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/servers", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY")})
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
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/nodes", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_ADMIN_API_KEY")})
        embed = discord.Embed(title="Nodes", description=f"We found {len(r.json()['data'])} nodes", color=discord.Color.green())
        for node in r.json()["data"]:
            embed.add_field(name=node["attributes"]["name"], value=f"```FQDN: {node['attributes']['fqdn']}\nMemory: {node['attributes']['allocated_resources']['memory']}/{node['attributes']['memory']} MiB\nDisk: {node['attributes']['allocated_resources']['disk']}/{node['attributes']['disk']} MiB```", inline=False)
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception as e:
        errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
        await ctx.respond(embed=errorEmbed, ephemeral=True)
        return


bot.run(os.getenv("TOKEN"))