import discord
from discord.ext import commands
import asyncio
from bs4 import BeautifulSoup
import traceback
import sys
import requests


bot = commands.Bot(command_prefix='.')
BASE_URL= 'https://www.goodreads.com'


# A simple on ready function
@bot.event
async def on_ready():
    print(
        f'\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    await bot.change_presence(status=discord.Status.idle, activity=discord.Game(name="Prefix = '.'"))
    print(f'Successfully logged in...!')
    
    
@bot.command(aliases=["s"])
@commands.guild_only()
async def search(ctx, *, bookname):
    user = ctx.author
    findingmsg = await ctx.send(f"{user.mention} Finding Book, just a sec. :alarm_clock:")
    
    # Defining some important variables
    name = bookname.split(" ")
    name = "+".join(name)
    source = f"https://www.goodreads.com/search?q={name}&qid="
    amzn_url = f"https://www.amazon.in/s?k={name}&ref=nb_sb_noss_2"
    strygrph_url = f"https://app.thestorygraph.com/browse?utf8=%E2%9C%93&button=&search_term={name}"
    google_url = f"https://www.google.com/search?tbm=bks&q={name}"
    
    #first request
    req = requests.get(source)    
    soup = BeautifulSoup(req.text,'lxml')  
    first_results = soup.find('a', class_='bookTitle')
    link = first_results.get('href')
    bookurl = BASE_URL + link
    
    #second request after getting the bookurl
    bookreq = requests.get(bookurl)
    bsoup = BeautifulSoup(bookreq.text, 'lxml')
    
    
    # Using try except block is necessary as it it check if the book objects is there or no there.
    try:
        booktitle = bsoup.find('h1', {'id' : 'bookTitle'}).text.strip()
    except:
        booktitle = "Unknown"
    try:
        authorname = bsoup.find('span', {'itemprop' : 'name'}).text.strip()
        authorname = bsoup.find(class_="authorName").text.strip()
    except:
        authorname = "Unknown"
    try:
        description = bsoup.find('div', {'id' : 'description'}).span.text
        description = bsoup.find(id="description").find_all("span")[-1].text.strip()
    except:
        description = "Unknown"
    try:
        imageurl = bsoup.find('img', {'id' : 'coverImage'}).get('src')
    except:
        imageurl = "https://i.imgur.com/1uy14A7.jpg"
    try:
        isbn = str(bsoup.find("meta", {"property": "books:isbn"}).get("content"))  
    except:
        isbn = "Unknown"
        
    # Some old classic books doesnt have isbn and its denoted as null in html, so we have check it!
    if isbn == 'null':
        isbn = "Unknown"
    try:
        ratings = bsoup.find('span', {'itemprop': 'ratingValue'}).text.strip()
    except:
        ratings = "Unknown"
    try:
        pages = bsoup.find('span', {'itemprop' : 'numberOfPages'}).text.strip()
    except:       
        pages = "Unknown"
    try:
        reviews = bsoup.find('meta', {'itemprop':'reviewCount'}).get('content')
    except:
        reviews = 'Unknown'
        
        
        
    # A simple embed with all the necessary items
    #============================================
    em = discord.Embed(
        title= f":books: {booktitle} by __{authorname}__",
        colour=user.colour,
        description=f"{description}..."
    )
    em.add_field(name="ISBN",
                 value=f"{isbn}",
                 inline=True)
    em.add_field(name="Rating",
                 value=f"{ratings} 🌟",
                 inline=True)
    em.add_field(name="Page Count",
                 value=f"{pages}",
                 inline=True)
    em.add_field(name="Total Reviews",
                 value=f"{reviews} :pencil:",)
    em.add_field(name="Book Links",
                 value=f"[Goodreads Link]({bookurl})\n[Amazon Link]({amzn_url})\n[The StoryGraph Link]({strygrph_url})\n[Google Play Books Link]({google_url})",
                 inline=False)
    em.set_thumbnail(url=imageurl)
    em.set_footer(text="Bot by Sedulous 💚")
    
    await findingmsg.edit(content=f"Found The Book {user.mention}", embed=em)
    #============================================
    

    
    
    # This is optional part.
    #=======================
    DELETE_EMOJI = "🗑️"
    PAGINATE_EMOJIS = [DELETE_EMOJI]
    for emoji in PAGINATE_EMOJIS:
        await asyncio.sleep(1)
        await findingmsg.add_reaction(emoji)

    def check(reaction_: discord.Reaction, user: discord.Member) -> bool:
        return (
            all((
                str(reaction_.emoji) in PAGINATE_EMOJIS,
                user.id != ctx.bot.user.id,
                reaction_.message.id == findingmsg.id
            )))

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", check=check)
        except asyncio.TimeoutError:
            break
        if user.id == ctx.message.author.id and str(reaction.emoji) == DELETE_EMOJI:
            print(f"Message was deleted by {user.name}")
            return await findingmsg.delete(), await ctx.message.delete()

        else:
            errmsg = await ctx.send(
                f"Sorry {user.mention},`Only the user who called the command can delete the message`")
            print(f"{user.name} tried to delete the command.")
            await errmsg.delete(delay=5.0)
    # ends here
    #=======================
    
    
    
# This is on_command_error function to avoid errors
#==================================================
@bot.event
async def on_command_error(ctx, error):

    # This prevents any commands with local handlers being handled here in on_command_error.
    if hasattr(ctx.command, 'on_error'):
        return

    ignored = (commands.CommandNotFound,)

    # Allows us to check for original exceptions raised and sent to CommandInvokeError.
    # If nothing is found. We keep the exception passed to on_command_error.
    error = getattr(error, 'original', error)

    # Anything in ignored will return and prevent anything happening.
    if isinstance(error, ignored):
        return

    elif isinstance(error, commands.NoPrivateMessage):
        try:
            errmsg1 = await ctx.author.send(f'`>{ctx.command}` command can not be used in Private Messages.')
            await errmsg1.delete(delay=5.0)
        except discord.HTTPException:
            pass
        
    elif isinstance(error, commands.MissingRequiredArgument):
        errmsg2 = await ctx.channel.send("You forgot the book name :blue_book: ")
        await errmsg2.delete(delay=5.0)
    
    elif isinstance(error, KeyError):
        errmsg3 = await ctx.channel.send("Unable to find that book :worried:")
        await errmsg3.delete(delay=5.0)
        
    elif isinstance(error, AttributeError):
        errmsg4 = await ctx.channel.send("Unable to find that book :worried:")
        await errmsg4.delete(delay=5.0)
        
    else:
        # All other Errors not returned come here. And we can just print the default TraceBack.
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
#==================================================

bot.run("Paste you token here!")