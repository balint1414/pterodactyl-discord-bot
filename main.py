import discord, os, requests
from dotenv import load_dotenv
load_dotenv()

bot = discord.Bot()

owner_ids = [int(id) for id in os.getenv("OWNER_IDS", "").split(",") if id.isdigit()]
noPermEmbed = discord.Embed(title="No permission", description="You don't have permission to use this command.", color=discord.Color.red())

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
        r = requests.get(os.getenv("PTERODACTYL_URL") + "/api/application/users", headers={"Authorization":"Bearer " + os.getenv("PTERODACTYL_USER_API_KEY")})
        print(r.status_code)
        embed = discord.Embed(title="Users", description="List of all users", color=discord.Color.green())
        for user in r.json()["data"]:
            embed.add_field(name=user["attributes"]["username"], value=f"ID: {user['attributes']['id']}\nEmail: {user['attributes']['email']}\nFull name: {user['attributes']['first_name']} {user['attributes']['last_name']}", inline=True)
        await ctx.respond(embed=embed)
    except Exception as e:
        errorEmbed = discord.Embed(title="Error", description="An error occurred while processing your request. Maybe the token had a bad day?", color=discord.Color.red(), fields=[discord.EmbedField(name="Error", value=str(e))])
        await ctx.respond(embed=errorEmbed, ephemeral=True)
        return
bot.run(os.getenv("TOKEN"))