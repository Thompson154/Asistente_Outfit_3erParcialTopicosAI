import dspy
import sqlite3
import json
from dotenv import load_dotenv

from tools import (
    analyze_clothing_image,
    save_clothing_item,
    query_wardrobe,
    generate_outfit_recommendation,
    save_outfit,
    get_all_clothes,
    get_saved_outfits,
    save_user_request
)


# --- DSPy Agent Definition ---
class OutfitAgentSignature(dspy.Signature):
    """
    You are an intelligent Outfit Assistant Agent that helps users manage their wardrobe
    and generate personalized outfit recommendations.
    
    Your task is to:
    1. Understand the user's requests in natural language about clothing and outfits.
    2. Use the available tools to manage the wardrobe and create outfit combinations.
    3. Provide clear, helpful, and fashion-conscious recommendations.
    
    Available Tools:
    - analyze_clothing_image: Analyzes a clothing image and suggests tags (type, color, category, occasion, style).
    - save_clothing_item: Saves a clothing item with its image path, name, and tags to the database.
    - query_wardrobe: Queries the wardrobe with optional filters (e.g., type="shirt", color="blue").
    - generate_outfit_recommendation: Finds clothes suitable for a specific occasion.
    - save_outfit: Saves an outfit combination with a name and occasion.
    - get_all_clothes: Retrieves all clothing items from the wardrobe.
    - get_saved_outfits: Retrieves all saved outfit combinations.
    
    Capabilities:
    - WARDROBE MANAGEMENT: Help users organize and view their clothing collection.
    - OUTFIT GENERATION: Create personalized outfit recommendations based on occasion, weather, style preferences.
    - SMART SEARCH: Find specific items or combinations using filters.
    - SAVE FAVORITES: Store outfit combinations for future use.
    
    Rules and Best Practices:
    - When analyzing images, extract all relevant tags (type, color, category, occasion, style).
    - For outfit recommendations, consider color coordination, style consistency, and occasion appropriateness.
    - Always check what's available in the wardrobe before making recommendations.
    - Provide outfit suggestions in logical order (e.g., top → bottom → shoes → accessories).
    - Be creative but practical with recommendations.
    - If the wardrobe is empty or lacks suitable items, inform the user politely.
    - When saving outfits, use descriptive names that reflect the occasion or style.
    
    CRITICAL: When recommending specific clothing items, ALWAYS include their ID in the format [ID:X] 
    immediately after mentioning each item. For example:
    "Te recomiendo la chaqueta negra [ID:5] con los jeans azules [ID:3] y zapatillas blancas [ID:8]."
    
    This is MANDATORY for every specific item you recommend so the system can display the images.
    """

    question = dspy.InputField(desc="The user's natural language question or request about outfits.")
    wardrobe_context = dspy.InputField(desc="Context about the current wardrobe state.")
    answer = dspy.OutputField(
        desc="The final, natural language answer with outfit recommendations or wardrobe information."
    )


class OutfitAgent(dspy.Module):
    """The Outfit Assistant Agent Module"""
    def __init__(self, tools: list[dspy.Tool]):
        super().__init__()
        # Initialize the ReAct agent for reasoning and acting
        self.agent = dspy.ReAct(
            OutfitAgentSignature,
            tools=tools,
            max_iters=10,  # Allow multiple steps for complex outfit generation
        )

    def forward(self, question: str, wardrobe_context: str) -> dspy.Prediction:
        """The forward pass of the module."""
        result = self.agent(question=question, wardrobe_context=wardrobe_context)
        return result


def configure_llm():
    """Configures the DSPy language model."""
    load_dotenv()
    
    # Use GPT-4 for better reasoning about fashion and outfits
    llm = dspy.LM(model="openai/gpt-4o", max_tokens=4000)
    dspy.settings.configure(lm=llm)

    print("[Agent] DSPy configured with gpt-4o model for outfit recommendations.")
    return llm


def create_agent(conn: sqlite3.Connection) -> dspy.Module | None:
    """Creates and configures the Outfit Assistant Agent."""
    if not configure_llm():
        return None

    # Tool 1: Analyze clothing image
    analyze_image_tool = dspy.Tool(
        name="analyze_clothing_image",
        desc="Analyzes a clothing image using GPT-4o-mini vision to extract tags. Input: image_path (str) - Path to the image file. Output: (str) - JSON string with suggested tags including type, color, category, occasion, and style. Use this when the user uploads a new clothing item.",
        func=analyze_clothing_image,
    )

    # Tool 2: Save clothing item
    save_clothing_tool = dspy.Tool(
        name="save_clothing_item",
        desc="Saves a clothing item with its metadata to the database. Input: image_path (str), name (str), tags_dict (dict) - Dictionary with tag types as keys and lists of values. Output: (str) - Success message with clothing ID. Use this after analyzing an image to save the item.",
        func=lambda image_path, name, tags_dict: save_clothing_item(conn, image_path, name, tags_dict),
    )

    # Tool 3: Query wardrobe
    query_wardrobe_tool = dspy.Tool(
        name="query_wardrobe",
        desc="Queries the wardrobe with optional filters. Input: filters (dict or None) - Dictionary with tag filters like {'type': 'shirt', 'color': 'blue'}. Output: (str) - List of matching clothing items with their tags. Use this to search for specific items or view filtered collections.",
        func=lambda filters=None: query_wardrobe(conn, filters),
    )

    # Tool 4: Generate outfit recommendation
    generate_outfit_tool = dspy.Tool(
        name="generate_outfit_recommendation",
        desc="Finds clothes suitable for a specific occasion. Input: occasion (str) - The event or situation (e.g., 'party', 'work', 'gym'), preferences (str, optional) - Additional style preferences. Output: (str) - List of suitable clothing items. Use this as a first step when creating outfit recommendations.",
        func=lambda occasion, preferences="": generate_outfit_recommendation(conn, occasion, preferences),
    )

    # Tool 5: Get all clothes
    get_all_tool = dspy.Tool(
        name="get_all_clothes",
        desc="Retrieves all clothing items from the wardrobe. Input: None. Output: (str) - Complete list of all clothing items with tags. Use this to show the user their complete wardrobe or when you need an overview of available items.",
        func=lambda: get_all_clothes(conn),
    )

    # Tool 6: Save outfit
    save_outfit_tool = dspy.Tool(
        name="save_outfit",
        desc="Saves an outfit combination to favorites. Input: name (str) - Descriptive name for the outfit, clothing_ids (list[int]) - List of clothing IDs in order, occasion (str, optional) - The occasion. Output: (str) - Success message with outfit ID. Use this when the user wants to save a recommended outfit.",
        func=lambda name, clothing_ids, occasion="": save_outfit(conn, name, clothing_ids, occasion),
    )

    # Tool 7: Get saved outfits
    get_outfits_tool = dspy.Tool(
        name="get_saved_outfits",
        desc="Retrieves all saved outfit combinations. Input: None. Output: (str) - List of saved outfits with their items. Use this to show the user their saved outfit collections.",
        func=lambda: get_saved_outfits(conn),
    )

    all_tools = [
        analyze_image_tool,
        save_clothing_tool,
        query_wardrobe_tool,
        generate_outfit_tool,
        get_all_tool,
        save_outfit_tool,
        get_outfits_tool,
    ]

    # Instantiate and return the agent
    agent = OutfitAgent(tools=all_tools)
    
    print("[Agent] Outfit Assistant Agent created successfully with 7 tools.")
    return agent
