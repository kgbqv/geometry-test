import discord
from discord import app_commands
from discord.ext import commands
import matplotlib.pyplot as plt
import numpy as np
import io
import textwrap
GEMINI_API_KEY="idk man"

# GPT-5-mini placeholder: you can replace with actual API call
def geometry_problem_to_prompt(problem: str) -> str:
    """
    Converts a natural‑language geometry problem into a structured prompt
    for GPT / Gemini to generate Python / Matplotlib code, while grouping
    shapes by color (e.g. all triangles one color, circles another, lines altitudes another).
    """
    prompt = f"""
You are an AI that generates **Python** code using **Matplotlib** to draw geometry diagrams.

Problem description: {problem}

Guidelines for the generated code:
1. Use **distinct colors by type of geometric object**:
   - All **triangles or polygons** should share one color.
   - All **circles** should share a different color.
   - All **special lines** (altitudes, medians, angle bisectors, etc.) should share another color.
2. Label all points, intersection points, and important features (e.g., orthocenter, centroid) with clear text.
3. Draw each geometric element (triangles, circles, lines) precisely and only as needed.
4. Do **not** display axes, ticks, grid, or frame — the diagram should be clean.
5. Provide a `fig, ax = plt.subplots()` and return a `fig` object so that it can be saved.
6. Use reasonably thick lines for shapes (polygons, circles) and lighter or dashed style for special lines.
7. Add comments in the code to describe what's being drawn.
8. **Do NOT use** `if __name__ == "__main__"` or define a `main()` function. The code should be runnable by simply executing it (e.g. via `exec()`).
9. Again, this is not a full script. It is being `exec`'d.
10. **Only** use pyplot and np (if necessary). No other imports.

Return **only valid Python code** (with imports) that uses Matplotlib (and optionally NumPy) to produce the requested diagram.

Make sure the code is readable, modular if possible, and follows the color‑grouping rule above.
"""
    # Clean up leading/trailing whitespace
    return "\n".join(line.strip() for line in prompt.strip().splitlines())

from google import generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)
async def generate_geometry_code(prompt: str) -> str:
    engineered_prompt = geometry_problem_to_prompt(prompt)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = await model.generate_content_async(engineered_prompt)
    k = response.text.strip() if response.text else "No response from Gemini"
    #strip any leading/trailing whitespace and formatting
    if k[0] == "`":
        k = k.strip("```python")
        k = k.strip('`')
    return k

# Execute the code and return image bytes
def run_code_and_get_image(code: str) -> bytes:
    # Provide global environment with imports
    global_env = {
        "plt": plt,
        "np": np
    }
    local_env = {}
    exec(code, global_env, local_env)
    fig = local_env.get("fig")
    if fig is None:
        # Sometimes the code might just call plt.show() instead of storing fig
        fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf


# Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# Slash command
@bot.tree.command(name="geometry", description="Generate a geometry diagram from a prompt")
@app_commands.describe(prompt="Your geometry description")
async def geometry(interaction: discord.Interaction, prompt: str):
    await interaction.response.send_message("Generating diagram…", ephemeral=False)
    msg = await interaction.original_response()

    # Step 1: Updating user on progress
    await msg.edit(content="Parsing prompt and generating code…")
    code = await generate_geometry_code(prompt)
    with open("last_generated_code.py", "w") as f:
        f.write(code)
    if code == "No response from Gemini":
        await msg.edit(content="Failed to generate code from the prompt.")
        return

    await msg.edit(content="Running code and creating diagram…")
    image_bytes = run_code_and_get_image(code)

    await msg.edit(content="Uploading results…")
    # Send image embed
    file_img = discord.File(fp=image_bytes, filename="diagram.png")
    file_code = discord.File(fp=io.BytesIO(code.encode()), filename="code.txt")
    embed = discord.Embed(title="Generated Geometry Diagram")
    embed.set_image(url="attachment://diagram.png")
    await msg.edit(content="Done!", attachments=[file_img, file_code], embed=embed)

bot.run("idk mate")
