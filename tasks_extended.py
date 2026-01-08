"""
AiBookWriter4 - Extended Task Definitions
Complete task definitions for all agent types across project types.
Optimized for 40k+ context models with rich, detailed outputs.

DESIGN PHILOSOPHY:
- Each major entity (character, location, item) is generated INDIVIDUALLY
- Each task gets the FULL context window (30k+ tokens) to produce rich output
- The model is explicitly told about its context capacity
"""

from crewai import Task, Agent
from typing import Optional, List, Dict, Any

# Default context reminder (for backward compatibility)
CONTEXT_REMINDER = """
## IMPORTANT: USE YOUR FULL CONTEXT CAPACITY
You have a large context window. Use it! Do not abbreviate or summarize.
Write DETAILED, EXTENSIVE content. More detail is always better.
If you find yourself writing short responses, EXPAND them.
"""


def get_context_reminder(context_window: int = 40000) -> str:
    """
    Generate a context-aware reminder for prompts.

    This helps the LLM understand how much detail it can provide based on
    the actual context window available.

    Args:
        context_window: The context window size in tokens

    Returns:
        A formatted context reminder string
    """
    if context_window >= 100000:
        return f"""
## CONTEXT CAPACITY: VERY LARGE ({context_window:,} tokens)
You have access to an extremely large context window. This means:
- Write EXTENSIVELY detailed content with comprehensive coverage
- Include thorough background, history, and nuanced explanations
- Explore edge cases, exceptions, and subtle variations
- Provide rich examples and detailed descriptions
- Don't hold back - use the full capacity for maximum quality
- For chapters: Write 3000-5000 words of detailed prose
"""
    elif context_window >= 32000:
        return f"""
## CONTEXT CAPACITY: LARGE ({context_window:,} tokens)
You have access to a large context window. This means:
- Write detailed, comprehensive content
- Include good background information and examples
- Develop ideas thoroughly before moving on
- For chapters: Write 2500-4000 words of detailed prose
"""
    elif context_window >= 8000:
        return f"""
## CONTEXT CAPACITY: MODERATE ({context_window:,} tokens)
You have a moderate context window. This means:
- Write clear, focused content with key details
- Include essential examples but be efficient
- Prioritize the most important information
- For chapters: Write 2000-3000 words
"""
    else:
        return f"""
## CONTEXT CAPACITY: LIMITED ({context_window:,} tokens)
You have a limited context window. This means:
- Be concise but complete
- Focus on essential information
- Use brief but effective examples
- For chapters: Write 1500-2500 words
"""


# =============================================================================
# ENTITY EXTRACTION TASKS (First Pass)
# =============================================================================

def create_entity_extraction_task(
    agent: Agent,
    story_task: Task,
    project_type: str = "standard"
) -> Task:
    """
    First pass task: Extract lists of characters, locations, and items
    that need to be created based on the story architecture.

    This enables the two-pass generation approach where we first identify
    WHAT to create, then create each entity individually with full context.
    """

    scale_guidance = ""
    if project_type == "light_novel":
        scale_guidance = """
## LIGHT NOVEL SCALE
For a light novel, plan for:
- 6-10 MAIN characters (protagonist, core party, main antagonists)
- 15-30 SUPPORTING characters (recurring allies, enemies, mentors)
- 8-15 KEY locations (home base, major cities, dungeons, special areas)
- 15-25 SIGNIFICANT items (weapons, artifacts, quest items)
"""
    elif project_type == "epic_fantasy":
        scale_guidance = """
## EPIC FANTASY SCALE
For epic fantasy, plan for:
- 8-12 MAIN characters (multiple POV characters, major antagonists)
- 20-40 SUPPORTING characters (faction leaders, recurring NPCs)
- 12-20 KEY locations (kingdoms, cities, landmarks, battlefields)
- 20-30 SIGNIFICANT items (legendary weapons, artifacts, regalia)
"""
    else:
        scale_guidance = """
## STANDARD NOVEL SCALE
For a standard novel, plan for:
- 3-5 MAIN characters (protagonist, antagonist, key allies)
- 6-12 SUPPORTING characters (friends, family, minor antagonists)
- 4-8 KEY locations (major settings where scenes occur)
- 8-15 SIGNIFICANT items (plot-relevant objects)
"""

    return Task(
        description=f"""# Entity Extraction - Identify What To Create

## Your Task
Based on the story architecture you created, make a COMPLETE LIST of all characters,
locations, and items needed for this story. YOU MUST INVENT SPECIFIC NAMES for each.

This is the PLANNING phase - list WHAT needs to be created with REAL names.

{scale_guidance}

## CRITICAL INSTRUCTIONS

1. INVENT ACTUAL NAMES - Do not write "[NAME]" or "[TYPE]" or any brackets
2. Names must fit the story's setting and genre
3. Each entry needs a real name, not a placeholder

## OUTPUT FORMAT

Write your list EXACTLY like this example (but with YOUR story's characters):

===== MAIN CHARACTERS =====
1. Kira Shadowmend | Protagonist | A young thief who discovers she has magical abilities
2. Lord Varen Ashford | Antagonist | The corrupt noble hunting Kira for her powers
3. Master Eldric | Mentor | An elderly wizard living in exile who trains Kira

===== SUPPORTING CHARACTERS =====
1. Tomás Brightwater | Ally | Kira's loyal friend from the thieves guild
2. Sister Moira | Healer | A kind priestess who shelters refugees
3. Captain Blackwood | Authority | The relentless guard captain pursuing Kira

===== KEY LOCATIONS =====
1. Dusthaven Slums | District | The poverty-stricken area where Kira grew up
2. The Gilded Palace | Building | Lord Ashford's opulent fortress
3. Whisperwood Forest | Wilderness | An enchanted forest where Eldric hides

===== SIGNIFICANT ITEMS =====
1. The Soulstone Ring | Artifact | Kira Shadowmend | Amplifies magical abilities but corrupts the user
2. Ashford's Seal | Symbol | Lord Varen Ashford | Grants authority over the city guard
3. Eldric's Grimoire | Book | Master Eldric | Contains forbidden spells

## ABSOLUTE RULES
- NEVER write [NAME], [TYPE], [ROLE], or any bracketed placeholders
- Every single entry must have a REAL invented name
- Names should sound like they belong in your story's world

## REQUIREMENTS

### For MAIN CHARACTERS, include:
- The protagonist(s)
- The main antagonist(s)
- Key allies/party members
- Love interests (if any)
- Mentors (if any)

### For SUPPORTING CHARACTERS, include:
- Recurring allies
- Secondary antagonists/minions
- Family members who appear
- Important NPCs
- Anyone who appears in multiple scenes

### For KEY LOCATIONS, include:
- Where the story begins
- The protagonist's home/base
- Major cities/towns
- Important landmarks
- Battle/confrontation sites
- The climax location
- Any location that appears 3+ times

### For SIGNIFICANT ITEMS, include:
- Weapons used by main characters
- Magical/special artifacts
- Plot MacGuffins
- Items of emotional significance
- Items that appear in key scenes
- Any item mentioned 3+ times

## IMPORTANT
- Give each character a DISTINCT name appropriate to the setting
- Each entity needs enough description to be developed later
- ROLE should be: Protagonist, Antagonist, Ally, Mentor, Love Interest, etc.
- TYPE for locations: City, Village, Building, Dungeon, Natural, etc.
- CATEGORY for items: Weapon, Artifact, Personal, Tool, Document, etc.
- OWNER should name the character who possesses it, or "Unknown/Lost/Contested"

Do NOT create detailed profiles here - just identify and list what needs to be created.""",
        expected_output="""A structured list with ACTUAL invented names (not placeholders) containing:

1. MAIN CHARACTERS section with 3-12 entries, each formatted as:
   Actual Name | Role | One-line description
   Example: "Elena Blackwood | Protagonist | A determined young woman searching for her missing brother"

2. SUPPORTING CHARACTERS section with 6-30 entries in the same format

3. KEY LOCATIONS section with 4-20 entries, each formatted as:
   Location Name | Type | Description
   Example: "The Obsidian Tower | Building | An ancient fortress hiding terrible secrets"

4. SIGNIFICANT ITEMS section with 8-30 entries, each formatted as:
   Item Name | Category | Owner | Description
   Example: "The Moonstone Pendant | Artifact | Elena Blackwood | A family heirloom that glows"

All names must be ACTUAL invented names appropriate to the story setting, NOT placeholders.""",
        agent=agent,
        context=[story_task]
    )


def parse_entity_extraction(extraction_output: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Parse the entity extraction output into structured data.

    Returns:
        {
            'main_characters': [{'name': str, 'role': str, 'description': str}, ...],
            'supporting_characters': [...],
            'locations': [{'name': str, 'type': str, 'description': str}, ...],
            'items': [{'name': str, 'category': str, 'owner': str, 'description': str}, ...]
        }
    """
    import re

    result = {
        'main_characters': [],
        'supporting_characters': [],
        'locations': [],
        'items': []
    }

    # Find sections
    sections = {
        'main_characters': r'===== MAIN CHARACTERS =====\s*(.*?)(?=====|$)',
        'supporting_characters': r'===== SUPPORTING CHARACTERS =====\s*(.*?)(?=====|$)',
        'locations': r'===== KEY LOCATIONS =====\s*(.*?)(?=====|$)',
        'items': r'===== SIGNIFICANT ITEMS =====\s*(.*?)(?=====|$)'
    }

    for key, pattern in sections.items():
        match = re.search(pattern, extraction_output, re.DOTALL | re.IGNORECASE)
        if match:
            section_text = match.group(1).strip()
            lines = [l.strip() for l in section_text.split('\n') if l.strip() and '|' in l]

            for line in lines:
                # Remove leading number and period
                line = re.sub(r'^\d+\.\s*', '', line)
                parts = [p.strip() for p in line.split('|')]

                if key in ['main_characters', 'supporting_characters']:
                    if len(parts) >= 3:
                        result[key].append({
                            'name': parts[0],
                            'role': parts[1],
                            'description': parts[2]
                        })
                    elif len(parts) == 2:
                        result[key].append({
                            'name': parts[0],
                            'role': parts[1],
                            'description': ''
                        })
                elif key == 'locations':
                    if len(parts) >= 3:
                        result[key].append({
                            'name': parts[0],
                            'type': parts[1],
                            'description': parts[2]
                        })
                    elif len(parts) == 2:
                        result[key].append({
                            'name': parts[0],
                            'type': parts[1],
                            'description': ''
                        })
                elif key == 'items':
                    if len(parts) >= 4:
                        result[key].append({
                            'name': parts[0],
                            'category': parts[1],
                            'owner': parts[2],
                            'description': parts[3]
                        })
                    elif len(parts) >= 3:
                        result[key].append({
                            'name': parts[0],
                            'category': parts[1],
                            'owner': 'Unknown',
                            'description': parts[2]
                        })

    return result


# =============================================================================
# PHASE 1: FOUNDATION TASKS
# =============================================================================

def create_story_architecture_task(
    agent: Agent,
    genre: str,
    num_chapters: int,
    story_prompt: str,
    additional_instructions: str = "",
    project_type: str = "standard"
) -> Task:
    """Create the story architecture task with rich output requirements."""

    arc_instruction = ""
    if project_type in ["light_novel", "epic_fantasy"]:
        num_arcs = max(1, num_chapters // 25)
        arc_instruction = f"""
## Arc Structure (Required for {num_chapters} chapters)

You MUST divide this story into {num_arcs} narrative arcs. For each arc provide:

**Arc Template (repeat for each arc):**
```
ARC [NUMBER]: [ARC TITLE]
Chapters: [start] - [end]
Arc Premise: [What this arc is about in 2-3 sentences]
Arc Antagonist/Conflict: [The main opposition in this arc]
Arc Goal: [What the protagonist must achieve]
Key Events:
  - [Event 1]
  - [Event 2]
  - [Event 3]
Arc Climax: [How this arc reaches its peak]
Arc Resolution: [How it ends and sets up the next arc]
Character Focus: [Which characters are central to this arc]
Power/Skill Progression: [What abilities are gained or improved]
```
"""

    scale_note = ""
    if num_chapters > 100:
        scale_note = f"""
## IMPORTANT: Large-Scale Story ({num_chapters} chapters)

This is a large-scale story. You must:
1. Plan for LONG-TERM plot threads that span 50+ chapters
2. Include multiple interconnected subplots
3. Plan character roster rotation (not all characters in every arc)
4. Include power progression milestones every 20-30 chapters
5. Plan for major status quo shifts every 50-100 chapters
"""

    return Task(
        description=f"""# Story Architecture Design

## Your Task
Design the COMPLETE narrative architecture for a {genre} novel with {num_chapters} chapters.

## Story Premise
{story_prompt}

{scale_note}

## Required Sections (You MUST include ALL of these)

### 1. LOGLINE (1-2 sentences)
Write a compelling logline that captures the core story.

### 2. STORY OVERVIEW (500+ words)
Write a detailed overview covering:
- The world and setting context
- The protagonist's starting situation
- The central conflict and what drives it
- The major turning points
- The ultimate resolution

### 3. CENTRAL CONFLICT
- Primary Conflict: [External struggle]
- Internal Conflict: [Protagonist's inner struggle]
- Thematic Conflict: [What ideas are in tension]
- Stakes: [What happens if the protagonist fails]

### 4. THEMES (3-5 themes, detailed)
For each theme:
- Theme Name
- How it manifests in the plot
- Which characters embody it
- How it evolves across the story

### 5. THREE-ACT STRUCTURE

**ACT 1 (Chapters 1-{int(num_chapters * 0.25)}): SETUP**
- Opening Hook: [How does the story grab attention]
- Status Quo: [Normal world before change]
- Inciting Incident: [What disrupts the status quo]
- First Plot Point: [Point of no return]

**ACT 2 (Chapters {int(num_chapters * 0.25)}-{int(num_chapters * 0.75)}): CONFRONTATION**
- Rising Action: [How challenges escalate]
- Midpoint: [Major revelation or shift]
- Complications: [What makes things harder]
- Crisis/Dark Moment: [Lowest point]

**ACT 3 (Chapters {int(num_chapters * 0.75)}-{num_chapters}): RESOLUTION**
- Climax Build: [How tension reaches peak]
- Climax: [The ultimate confrontation]
- Resolution: [How conflicts are resolved]
- Denouement: [Final state of the world/characters]

### 6. MAIN CHARACTERS OVERVIEW (Brief)
List 4-8 main characters with:
- Name and Role
- One-sentence description
- Arc summary (who they become)

### 7. POV AND VOICE
- POV Type: [First person / Third limited / Third omniscient / Multiple POV]
- Narrative Voice: [Describe the tone and style]
- Tense: [Past / Present]
{arc_instruction}
{f"### Additional Instructions: {additional_instructions}" if additional_instructions else ""}

{CONTEXT_REMINDER}

## Output Requirements
- Be DETAILED and SPECIFIC, not vague
- Use the full context available to you (30k+ tokens)
- Write at least 2000 words total
- Include ALL sections listed above
- Use markdown formatting for readability""",
        expected_output=f"""A comprehensive story architecture document of at least 2000 words containing:
1. A compelling logline
2. A detailed 500+ word story overview
3. Clearly defined central conflicts with stakes
4. 3-5 themes with manifestation details
5. Complete three-act structure with specific plot points for {num_chapters} chapters
6. Main characters overview
7. POV and voice specifications
{"8. " + str(max(1, num_chapters // 25)) + " detailed arc breakdowns" if project_type in ["light_novel", "epic_fantasy"] else ""}

The document should be detailed enough to guide the entire novel writing process.""",
        agent=agent
    )


# =============================================================================
# PHASE 2: WORLD BUILDING TASKS
# =============================================================================

def create_character_design_task(
    agent: Agent,
    story_task: Task,
    num_main_characters: int = 4,
    num_supporting: int = 8,
    project_type: str = "standard"
) -> Task:
    """Create the character design task with detailed output requirements."""

    scale_note = ""
    if num_main_characters > 6 or num_supporting > 20:
        scale_note = f"""
## LARGE CAST NOTE
With {num_main_characters} main and {num_supporting} supporting characters, you must:
- Ensure each character has DISTINCT speech patterns
- Create clear visual distinguishing features
- Establish unique motivations that don't overlap
- Plan character "screen time" distribution
- Group characters by faction/relationship for easier tracking
"""

    return Task(
        description=f"""# Character Design Document

## Your Task
Based on the story architecture provided, design {num_main_characters} MAIN characters and {num_supporting} SUPPORTING characters.

{scale_note}

## MAIN CHARACTERS (Full Profiles Required)

For EACH of the {num_main_characters} main characters, provide ALL of the following:

### Character Profile Template:
```
═══════════════════════════════════════════════════════════════
CHARACTER: [FULL NAME]
Role: [Protagonist / Antagonist / Deuteragonist / etc.]
═══════════════════════════════════════════════════════════════

BASIC INFORMATION
─────────────────
• Full Name:
• Nickname/Alias:
• Age:
• Gender:
• Occupation/Role:

PHYSICAL APPEARANCE (Be Specific!)
──────────────────────────────────
• Height/Build:
• Hair: [Color, style, length]
• Eyes: [Color, shape, distinctive features]
• Skin:
• Distinguishing Features: [Scars, tattoos, birthmarks, etc.]
• Typical Clothing:
• Overall Impression: [How do people perceive them at first glance]

PSYCHOLOGY
──────────
• Core Personality Traits: [List 4-5 specific traits]
• Strengths: [3-4 character strengths]
• Flaws: [3-4 genuine flaws that cause problems]
• Deepest Fear:
• Greatest Desire:
• Internal Conflict: [What they struggle with internally]
• How They Handle Stress:
• How They Handle Conflict:

BACKGROUND
──────────
• Birthplace:
• Family: [Parents, siblings, etc.]
• Key Formative Events: [2-3 events that shaped them]
• Education/Training:
• Current Situation at Story Start:

VOICE PROFILE (Critical for Dialogue!)
──────────────────────────────────────
• Speech Pattern: [Formal/casual, verbose/terse, etc.]
• Vocabulary Level: [Simple/educated/technical]
• Verbal Tics/Catchphrases: [Specific phrases they use]
• Dialect/Accent Notes:
• How They Express:
  - Anger:
  - Joy:
  - Fear:
  - Affection:
• Sample Dialogue Lines:
  1. "[A line showing their normal speech]"
  2. "[A line showing them under stress]"
  3. "[A line showing them being emotional]"

CHARACTER ARC
─────────────
• Starting State: [Who they are at the beginning]
• Key Growth Moments: [What changes them]
• Ending State: [Who they become]
• What They Learn:

RELATIONSHIPS
─────────────
[List their relationship to each other main character]
• [Character Name]: [Relationship type and dynamic]
```

## SUPPORTING CHARACTERS (Shorter Profiles)

For EACH of the {num_supporting} supporting characters, provide:

### Supporting Character Template:
```
───────────────────────────────────
SUPPORTING: [NAME]
───────────────────────────────────
• Role: [Their function in the story]
• Brief Description: [2-3 sentences covering appearance and personality]
• Key Trait: [One defining characteristic]
• Voice Note: [How they sound different from others]
• Connection to Main Characters: [Who they interact with and how]
• Arc (if any): [Do they change?]
```

## RELATIONSHIP MAP

After all character profiles, provide a relationship summary:
- Key alliances
- Key rivalries/conflicts
- Romantic connections (if any)
- Mentor/student relationships
- Family connections

{CONTEXT_REMINDER}

## Output Requirements
- Every main character needs a COMPLETE profile using the template above
- Every supporting character needs a filled template
- Include SPECIFIC details, not vague descriptions
- Include sample dialogue for main characters
- Make each character's voice DISTINCT
- Write at least 3000 words total for all characters""",
        expected_output=f"""A comprehensive character document of at least 3000 words containing:
1. {num_main_characters} COMPLETE main character profiles with all sections filled
2. {num_supporting} supporting character profiles
3. Sample dialogue lines for each main character
4. A relationship map showing connections between characters

Each profile must include specific physical descriptions, psychology, voice patterns, and character arcs. No section should be left vague or generic.""",
        agent=agent,
        context=[story_task]
    )


def create_single_character_task(
    agent: Agent,
    story_task: Task,
    character_name: str,
    character_role: str,
    character_brief: str,
    is_main: bool = True,
    previous_characters: Optional[List[str]] = None
) -> Task:
    """Create a task for designing ONE character in full detail."""

    prev_chars_context = ""
    if previous_characters:
        prev_chars_context = f"""
## Previously Created Characters
These characters already exist in the story. Ensure {character_name} has DISTINCT traits:
{chr(10).join(f"- {c}" for c in previous_characters)}

Make sure {character_name}'s voice, personality, and appearance are CLEARLY DIFFERENT from all of these.
"""

    return Task(
        description=f"""# Complete Character Profile: {character_name}

{CONTEXT_REMINDER}

## Your Task
Create a COMPLETE, EXHAUSTIVE profile for this ONE character: **{character_name}**

Role: {character_role}
Brief: {character_brief}
{prev_chars_context}

## FULL CHARACTER PROFILE

You have 30,000+ tokens of context. Use it ALL for this single character.
This should be the most detailed character profile ever written.

### SECTION 1: BASIC IDENTITY (500+ words)
```
═══════════════════════════════════════════════════════════════
CHARACTER: {character_name.upper()}
Role: {character_role}
═══════════════════════════════════════════════════════════════

FULL NAME & MEANING
───────────────────
• Full Legal Name:
• Name Meaning/Origin: [Why this name? What does it mean?]
• Nicknames: [List all, with who uses each]
• How They Introduce Themselves:
• Names They Hate Being Called:

DEMOGRAPHICS
────────────
• Age (Exact):
• Birthday:
• Birthplace:
• Current Residence:
• Nationality/Ethnicity:
• Social Class:
• Education Level:
• Occupation/Role:
• Income/Wealth Status:
```

### SECTION 2: PHYSICAL APPEARANCE (800+ words)
```
BODY
────
• Exact Height:
• Exact Weight:
• Body Type: [Detailed - not just "slim" or "muscular"]
• Posture: [How they carry themselves]
• Gait: [How they walk]
• Physical Fitness Level:
• Health Issues:
• Scars: [Location, origin, appearance]
• Birthmarks:
• Tattoos: [If any, describe in detail]

FACE
────
• Face Shape:
• Skin Tone: [Specific]
• Skin Texture: [Smooth, weathered, freckled, etc.]
• Forehead:
• Eyebrows: [Shape, thickness, color]
• Eyes:
  - Color: [Be specific - not just "blue" but "pale arctic blue with darker rings"]
  - Shape:
  - Size:
  - Expression at Rest:
  - How they change with emotion:
• Nose: [Shape, size, any distinctive features]
• Cheekbones:
• Lips: [Shape, color, fullness]
• Chin/Jaw:
• Ears:

HAIR
────
• Natural Color:
• Current Color:
• Texture:
• Length:
• Style: [How they typically wear it]
• Facial Hair (if applicable):
• Hair Rituals: [How they care for it]

HANDS
─────
• Size:
• Calluses: [Where, why]
• Nails: [Kept how]
• Rings/Jewelry:
• Dominant Hand:
• Gestures: [How they use their hands when talking]

VOICE
─────
• Pitch:
• Volume (typical):
• Accent/Dialect:
• Speech Speed:
• Speech Patterns:
• Verbal Tics:
• Laugh Description:
• Voice When Angry:
• Voice When Happy:
• Voice When Lying:
```

### SECTION 3: CLOTHING & STYLE (400+ words)
```
EVERYDAY WEAR
─────────────
• Preferred Colors:
• Preferred Fabrics:
• Typical Outfit: [Describe a complete outfit in detail]
• Shoes:
• Accessories:

FORMAL WEAR
───────────
• [Describe what they'd wear to a formal event]

SLEEPWEAR
─────────
• [What they sleep in]

DISTINGUISHING ITEMS
───────────────────
• Signature Item: [Something they're rarely without]
• Jewelry Always Worn:
• Weapons Carried (if any):
• Bag/Pockets Contents:
```

### SECTION 4: PSYCHOLOGY (1000+ words)
```
CORE PERSONALITY
────────────────
• In Three Words:
• Dominant Trait:
• Secondary Traits (5+):
  1. [Trait]: [How it manifests]
  2. [Trait]: [How it manifests]
  3. [Trait]: [How it manifests]
  4. [Trait]: [How it manifests]
  5. [Trait]: [How it manifests]

STRENGTHS (with examples)
────────────────────────
1. [Strength]: [Specific example of how this helps them]
2. [Strength]: [Specific example]
3. [Strength]: [Specific example]
4. [Strength]: [Specific example]

FLAWS (genuine, causing problems)
─────────────────────────────────
1. [Flaw]: [How this causes problems - be specific]
2. [Flaw]: [How this causes problems]
3. [Flaw]: [How this causes problems]
4. [Flaw]: [How this causes problems]

FEARS
─────
• Greatest Fear: [Deep psychological fear]
• Why They Fear This: [Origin]
• How Fear Manifests: [Physical/behavioral signs]
• Lesser Fears: [List 3-4]

DESIRES
───────
• Greatest Desire: [What they want most]
• Why: [Origin of this desire]
• What They'd Sacrifice For It:
• Secret Desire: [Something they won't admit]

BELIEFS & VALUES
────────────────
• Core Belief About The World:
• Core Belief About People:
• Moral Code: [What they will/won't do]
• Political Views:
• Religious/Spiritual Views:
• What Makes Someone Good:
• What Makes Someone Evil:

EMOTIONAL PATTERNS
──────────────────
• Default Mood:
• What Makes Them Happy:
• What Makes Them Angry:
• What Makes Them Sad:
• What Makes Them Afraid:
• How They Express Happiness:
• How They Express Anger:
• How They Express Sadness:
• How They Express Fear:
• How They Handle Stress:
• How They Handle Conflict:
• Coping Mechanisms (healthy):
• Coping Mechanisms (unhealthy):

MENTAL HEALTH
─────────────
• Overall Mental State:
• Any Disorders/Conditions:
• Trauma History:
• How Trauma Affects Them:
```

### SECTION 5: BACKGROUND (800+ words)
```
CHILDHOOD
─────────
• Born: [Date, place, circumstances]
• Parents: [Names, occupations, relationship with character]
• Siblings: [Names, ages, relationships]
• Childhood Home: [Describe in detail]
• Socioeconomic Status Growing Up:
• Happiest Childhood Memory:
• Worst Childhood Memory:
• Formative Experience 1: [What happened, how it shaped them]
• Formative Experience 2: [What happened, how it shaped them]
• Formative Experience 3: [What happened, how it shaped them]

ADOLESCENCE
───────────
• Where They Grew Up:
• Education:
• First Love/Crush:
• Biggest Mistake:
• Key Friendships:
• Defining Moment:

ADULTHOOD (up to story start)
─────────────────────────────
• Career Path:
• Major Relationships:
• Biggest Success:
• Biggest Failure:
• Where They Live Now:
• Current Situation at Story Start:
```

### SECTION 6: DIALOGUE & VOICE (600+ words)
```
SPEECH PATTERNS
───────────────
• Vocabulary Level: [Simple/Educated/Technical/Flowery]
• Sentence Structure: [Short and punchy? Long and complex?]
• Filler Words: ["Um," "Like," "You know," etc.]
• Favorite Expressions:
• Phrases They Overuse:
• Things They Never Say:
• How They Say Yes:
• How They Say No:
• Profanity Usage:
• Humor Style:

DIALOGUE SAMPLES (write at least 10)
────────────────────────────────────
1. Greeting someone they like:
   "[Actual dialogue]"

2. Greeting someone they dislike:
   "[Actual dialogue]"

3. Under stress:
   "[Actual dialogue]"

4. When happy:
   "[Actual dialogue]"

5. When angry:
   "[Actual dialogue]"

6. When lying:
   "[Actual dialogue]"

7. Giving advice:
   "[Actual dialogue]"

8. Asking for help:
   "[Actual dialogue]"

9. In combat/danger:
   "[Actual dialogue]"

10. Flirting (if applicable):
    "[Actual dialogue]"
```

### SECTION 7: CHARACTER ARC (400+ words)
```
AT STORY START
──────────────
• Who They Are:
• What They Believe:
• What They Want:
• What They Need (but don't know):
• Their Lie: [The false belief they hold]

TRANSFORMATION
──────────────
• Inciting Incident: [What starts their change]
• Key Moment 1: [What challenges their belief]
• Key Moment 2: [What forces growth]
• Key Moment 3: [What pushes them to change]
• Dark Night of the Soul: [Their lowest point]
• Epiphany: [When they realize the truth]

AT STORY END
────────────
• Who They Become:
• What They Now Believe:
• How They've Changed:
• What They Sacrificed:
• What They Gained:
```

## Output Requirements
- This is ONE character - give them your FULL attention
- Write at least 3500 words for this profile
- Fill out EVERY section completely
- Include at least 10 dialogue samples
- Make this character feel REAL and THREE-DIMENSIONAL
- NO section should be skipped or abbreviated""",
        expected_output=f"""A complete, exhaustive character profile for {character_name} containing at least 3500 words with:
1. Complete identity and demographics
2. Detailed physical appearance (body, face, hair, hands, voice)
3. Full clothing and style guide
4. Deep psychological profile (traits, fears, desires, emotions)
5. Complete background (childhood through story start)
6. At least 10 dialogue samples showing their voice
7. Full character arc from start to end of story

This must be the most detailed character profile possible - a complete guide for writing this character consistently.""",
        agent=agent,
        context=[story_task]
    )


def create_single_location_task(
    agent: Agent,
    story_task: Task,
    location_name: str,
    location_type: str,
    location_brief: str,
    previous_locations: Optional[List[str]] = None
) -> Task:
    """Create a task for designing ONE location in full detail."""

    prev_loc_context = ""
    if previous_locations:
        prev_loc_context = f"""
## Previously Created Locations
These locations already exist. Ensure {location_name} feels DISTINCT:
{chr(10).join(f"- {l}" for l in previous_locations)}
"""

    return Task(
        description=f"""# Complete Location Profile: {location_name}

{CONTEXT_REMINDER}

## Your Task
Create a COMPLETE, EXHAUSTIVE profile for this ONE location: **{location_name}**

Type: {location_type}
Brief: {location_brief}
{prev_loc_context}

Use your full 30,000+ token context for this SINGLE location.

### FULL LOCATION DOCUMENT (2500+ words minimum)

```
╔══════════════════════════════════════════════════════════════════════════╗
║  LOCATION: {location_name.upper()}
║  Type: {location_type}
╚══════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════
PART 1: OVERVIEW & GEOGRAPHY
═══════════════════════════════════════════════════════════════════════════

GENERAL DESCRIPTION (2-3 paragraphs)
────────────────────────────────────
[Write a vivid, immersive description of this place as if you're walking through it for the first time]

GEOGRAPHY & PLACEMENT
────────────────────
• Exact Location: [Coordinates or relation to other places]
• Surrounding Area: [What's nearby in each direction]
• Climate Zone:
• Elevation:
• Natural Features: [Rivers, hills, forests, etc.]
• Size: [Dimensions or area]
• Borders: [What defines the edges of this location]

LAYOUT & STRUCTURE
─────────────────
• Overall Shape/Plan:
• Main Areas/Zones:
  - [Zone 1]: [Description]
  - [Zone 2]: [Description]
  - [Zone 3]: [Description]
  - [Zone 4]: [Description]
• Entry Points: [How do you get in]
• Important Buildings/Features:
  - [Feature 1]: [Location and description]
  - [Feature 2]: [Location and description]
  - [Feature 3]: [Location and description]
• Hidden Areas: [Secret or overlooked spots]

═══════════════════════════════════════════════════════════════════════════
PART 2: SENSORY EXPERIENCE (Most Important!)
═══════════════════════════════════════════════════════════════════════════

👁️ SIGHT - VISUAL DETAILS
─────────────────────────
COLORS:
• Dominant Colors: [What colors define this place]
• Accent Colors: [Secondary colors]
• Color Variations: [How colors change by time/weather]

LIGHTING:
• Natural Light Sources:
• Artificial Light Sources:
• Light Quality: [Harsh, soft, dappled, etc.]
• Shadow Patterns:
• At Dawn: [How light looks]
• At Midday: [How light looks]
• At Dusk: [How light looks]
• At Night: [How light/darkness looks]
• In Rain: [How light changes]

TEXTURES & SURFACES:
• Ground: [What you walk on]
• Walls: [If applicable]
• Natural Surfaces: [Trees, rocks, water]
• Man-made Surfaces: [Buildings, roads]

MOVEMENT:
• What Moves Here: [People, animals, plants, machines]
• Movement Patterns: [Busy, still, rhythmic]

👂 SOUND - AUDIO DETAILS
────────────────────────
AMBIENT SOUNDS (always present):
• Background Hum:
• Natural Sounds:
• Man-made Sounds:

COMMON SOUNDS (frequent):
• [Sound 1]: [Description, how often]
• [Sound 2]: [Description, how often]
• [Sound 3]: [Description, how often]

OCCASIONAL SOUNDS:
• [Sound 1]: [When it occurs]
• [Sound 2]: [When it occurs]

SOUND AT DIFFERENT TIMES:
• Morning:
• Afternoon:
• Evening:
• Night:
• During Events/Activities:

SILENCE:
• When It's Quiet:
• Quality of Silence: [Peaceful, tense, eerie]

👃 SMELL - OLFACTORY DETAILS
────────────────────────────
PRIMARY SCENTS:
• What You Notice First:
• Strongest Smell:

BACKGROUND ODORS:
• Underlying Scents:
• Subtle Notes:

SMELL SOURCES:
• [Source 1]: [The smell it produces]
• [Source 2]: [The smell it produces]
• [Source 3]: [The smell it produces]

SMELL VARIATIONS:
• By Season:
• By Time of Day:
• By Weather:
• By Activity:

✋ TOUCH - TACTILE DETAILS
──────────────────────────
TEMPERATURE:
• General Temperature Range:
• Hot Spots:
• Cold Spots:
• Indoor vs Outdoor:

AIR QUALITY:
• Humidity:
• Air Movement:
• Dust/Particles:
• Freshness:

SURFACES TO TOUCH:
• [Surface 1]: [How it feels]
• [Surface 2]: [How it feels]
• [Surface 3]: [How it feels]

PHYSICAL SENSATIONS:
• Ground Underfoot:
• Wind on Skin:
• Sun/Shade Effects:

═══════════════════════════════════════════════════════════════════════════
PART 3: ATMOSPHERE & MOOD
═══════════════════════════════════════════════════════════════════════════

EMOTIONAL TONE
──────────────
• Default Mood: [How this place makes people feel]
• Energy Level: [Frantic, calm, tense, lazy, etc.]
• Comfort Level: [Welcoming, hostile, neutral]

MOOD BY TIME
────────────
• Dawn Mood:
• Morning Mood:
• Afternoon Mood:
• Evening Mood:
• Night Mood:

MOOD BY WEATHER
──────────────
• In Sunshine:
• In Rain:
• In Fog/Mist:
• In Wind:
• In Snow (if applicable):

PSYCHOLOGICAL EFFECTS
────────────────────
• How Newcomers Feel:
• How Regulars Feel:
• What This Place Represents:
• Subconscious Effects:

═══════════════════════════════════════════════════════════════════════════
PART 4: HISTORY & SIGNIFICANCE
═══════════════════════════════════════════════════════════════════════════

ORIGIN
──────
• How/When Created:
• By Whom:
• Original Purpose:
• Named After:

HISTORICAL TIMELINE
──────────────────
• [Year/Era 1]: [Event]
• [Year/Era 2]: [Event]
• [Year/Era 3]: [Event]
• [Recent]: [Recent changes]

SIGNIFICANT EVENTS HERE
──────────────────────
• [Event 1]: [What happened, when, who was involved]
• [Event 2]: [What happened]
• [Event 3]: [What happened]

CULTURAL SIGNIFICANCE
────────────────────
• What It Represents:
• Legends/Stories About It:
• Traditions Associated:
• How People Speak of It:

═══════════════════════════════════════════════════════════════════════════
PART 5: STORY ROLE
═══════════════════════════════════════════════════════════════════════════

PLOT SIGNIFICANCE
────────────────
• Why This Location Matters:
• Key Scenes Set Here:
• What Happens Here:

CHARACTER CONNECTIONS
────────────────────
• [Character]: [Their connection to this place]
• [Character]: [Their connection to this place]

THEMATIC RESONANCE
─────────────────
• What Themes It Reinforces:
• Symbolic Meaning:
• How It Changes Through Story:

═══════════════════════════════════════════════════════════════════════════
PART 6: PRACTICAL DETAILS
═══════════════════════════════════════════════════════════════════════════

INHABITANTS
───────────
• Who Lives/Works Here:
• Population (if applicable):
• Demographics:
• Daily Routines:

RESOURCES
─────────
• Available Resources:
• Scarcity:
• Economy:

DANGERS & HAZARDS
────────────────
• Physical Dangers:
• Environmental Hazards:
• Social Dangers:
• Hidden Threats:

SAFE AREAS
─────────
• [Safe Spot 1]: [Why it's safe]
• [Safe Spot 2]: [Why it's safe]

CONNECTIONS
──────────
• Routes To Other Locations:
• Travel Times:
• Transportation Available:
```

## Output Requirements
- This is ONE location - give it your FULL 30k+ token capacity
- Write at least 2500 words
- Fill EVERY section with specific, vivid details
- Make this place feel REAL and IMMERSIVE
- Include enough sensory detail that a reader could close their eyes and BE there""",
        expected_output=f"""A complete, immersive location profile for {location_name} containing at least 2500 words with:
1. Full geography and layout with specific dimensions and features
2. EXTENSIVE sensory details (sight, sound, smell, touch) with time/weather variations
3. Complete atmosphere and mood analysis
4. Historical background and significance
5. Story role and character connections
6. Practical details (inhabitants, resources, dangers)

This must make readers feel like they're actually standing in this location.""",
        agent=agent,
        context=[story_task]
    )


def create_single_item_task(
    agent: Agent,
    story_task: Task,
    item_name: str,
    item_category: str,
    item_brief: str,
    owner: str = "Unknown",
    previous_items: Optional[List[str]] = None
) -> Task:
    """Create a task for designing ONE significant item in full detail."""

    prev_items_context = ""
    if previous_items:
        prev_items_context = f"""
## Previously Created Items
These items already exist in the story:
{chr(10).join(f"- {i}" for i in previous_items)}
"""

    return Task(
        description=f"""# Complete Item Profile: {item_name}

{CONTEXT_REMINDER}

## Your Task
Create a COMPLETE profile for this ONE item: **{item_name}**

Category: {item_category}
Brief: {item_brief}
Associated with: {owner}
{prev_items_context}

Use your full 30,000+ token context for this SINGLE item.

### FULL ITEM DOCUMENT (1500+ words minimum)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ITEM: {item_name.upper()}
│ Category: {item_category}
└──────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
PART 1: PHYSICAL DESCRIPTION
═══════════════════════════════════════════════════════════════════════════

OVERVIEW
────────
[2-3 paragraphs describing this item as if you're holding it, examining it from all angles]

EXACT SPECIFICATIONS
───────────────────
• Type: [What kind of object this is]
• Size: [Exact dimensions]
• Weight: [Exact or approximate]
• Shape: [Detailed shape description]

MATERIALS
─────────
• Primary Material:
• Secondary Materials:
• Construction Method:
• Quality/Craftsmanship:

APPEARANCE
─────────
• Color(s):
• Finish: [Matte, glossy, worn, polished]
• Texture: [How it feels to touch]
• Decorations: [Any engravings, gems, patterns]
• Wear/Age Signs: [Scratches, patina, repairs]
• Distinctive Features: [What makes it recognizable]

SENSORY DETAILS
──────────────
• Touch: [How it feels in hand]
• Sound: [Does it make noise?]
• Smell: [Any scent?]
• Temperature: [Warm, cold, neutral?]
• Aura: [Any unusual feeling near it?]

═══════════════════════════════════════════════════════════════════════════
PART 2: FUNCTION & PROPERTIES
═══════════════════════════════════════════════════════════════════════════

PRIMARY FUNCTION
───────────────
• What It Does:
• How It's Used:
• Who Can Use It:

SPECIAL PROPERTIES (if any)
──────────────────────────
• Magical/Special Ability 1:
  - Effect: [What it does]
  - Activation: [How to activate]
  - Cost: [What it costs to use]
  - Limitation: [When it doesn't work]

• Magical/Special Ability 2:
  [Same format]

LIMITATIONS
──────────
• What It Cannot Do:
• Conditions That Prevent Use:
• Weaknesses:
• Side Effects:

═══════════════════════════════════════════════════════════════════════════
PART 3: HISTORY & ORIGIN
═══════════════════════════════════════════════════════════════════════════

CREATION
────────
• Created By: [Who made it]
• Created When: [Era/date]
• Created Where: [Location]
• Created Why: [Purpose/circumstances]
• Creation Process: [How it was made]

HISTORY TIMELINE
───────────────
• [Era/Year]: [Event in item's history]
• [Era/Year]: [Event]
• [Era/Year]: [Event]
• [Era/Year]: [How it came to current owner]

NOTABLE PAST OWNERS
──────────────────
• [Owner 1]: [Who, when, what they did with it]
• [Owner 2]: [Who, when, what they did with it]

LEGENDS & STORIES
────────────────
• Known Legends:
• Rumors:
• Truth Behind Legends:

═══════════════════════════════════════════════════════════════════════════
PART 4: OWNERSHIP & LOCATION
═══════════════════════════════════════════════════════════════════════════

CURRENT STATUS
─────────────
• Current Owner: {owner}
• Current Location:
• How Owner Acquired It:
• Owner's Relationship to It:

STORAGE & CARE
─────────────
• How It's Kept:
• Required Maintenance:
• Vulnerable To:

CONTESTED
─────────
• Who Else Wants It: [If anyone]
• Why They Want It:
• What They'd Do to Get It:

═══════════════════════════════════════════════════════════════════════════
PART 5: STORY SIGNIFICANCE
═══════════════════════════════════════════════════════════════════════════

CHEKHOV'S GUN
────────────
• Setup: [When/how it's introduced]
• Payoff: [When/how it becomes important]
• Why It Matters: [Plot significance]

PLOT ROLE
─────────
• Key Scenes:
  - [Scene 1]: [How item is used]
  - [Scene 2]: [How item is used]
• Turning Points Involving It:
• How It Affects Outcome:

SYMBOLIC MEANING
───────────────
• What It Represents:
• Thematic Connection:
• Character Growth Link:

LOCATION TRACKING
────────────────
• Story Start: [Where is it]
• Act 1 End: [Where is it]
• Midpoint: [Where is it]
• Act 2 End: [Where is it]
• Climax: [Where is it]
• Story End: [Where is it]
```

## Output Requirements
- This is ONE item - give it your FULL attention
- Write at least 1500 words
- Include complete physical description, history, and story role
- Make this item feel SIGNIFICANT and REAL
- Track its location throughout the story""",
        expected_output=f"""A complete item profile for {item_name} containing at least 1500 words with:
1. Detailed physical description (appearance, materials, sensory details)
2. Complete function and properties (including limitations)
3. Full history from creation to present
4. Ownership details and current location
5. Story significance with setup/payoff and symbolic meaning
6. Location tracking throughout the story

This item must feel significant and have a clear role in the narrative.""",
        agent=agent,
        context=[story_task]
    )


def create_location_design_task(
    agent: Agent,
    story_task: Task,
    num_locations: int = 6
) -> Task:
    """Create the location design task with rich sensory details."""
    return Task(
        description=f"""# Location Design Document

## Your Task
Based on the story architecture, design {num_locations} KEY LOCATIONS with rich, immersive detail.

## LOCATION PROFILE TEMPLATE

For EACH location, provide ALL of the following:

```
╔══════════════════════════════════════════════════════════════════╗
║  LOCATION: [NAME]                                                 ║
║  Type: [City / Village / Building / Natural Feature / etc.]       ║
╚══════════════════════════════════════════════════════════════════╝

OVERVIEW
────────
[2-3 paragraph description of this location]

PHYSICAL DETAILS
────────────────
• Size/Scale:
• Layout: [Describe the general arrangement]
• Key Features:
  - [Feature 1]
  - [Feature 2]
  - [Feature 3]
• Notable Landmarks:
• Architecture Style (if applicable):
• Natural Features (if applicable):

SENSORY EXPERIENCE
──────────────────
👁️ SIGHT:
  • Colors: [Dominant colors of this place]
  • Lighting: [Natural/artificial, bright/dim, etc.]
  • Visual Atmosphere: [What catches the eye]
  • Time of Day Variations:
    - Dawn:
    - Midday:
    - Dusk:
    - Night:

👂 SOUND:
  • Ambient Sounds: [Always-present background noise]
  • Common Sounds: [Sounds that occur regularly]
  • Unusual Sounds: [Sounds that would stand out]
  • Silence: [When is it quiet? What does that feel like?]

👃 SMELL:
  • Primary Scents: [What you'd notice first]
  • Background Odors: [Subtle, underlying smells]
  • Seasonal Variations: [How smells change]

✋ TOUCH/FEEL:
  • Temperature: [General climate/feel]
  • Textures: [What surfaces feel like]
  • Air Quality: [Humid/dry, clean/dusty, etc.]
  • Physical Sensations: [Wind, vibrations, etc.]

ATMOSPHERE & MOOD
─────────────────
• Emotional Tone: [How does this place make people feel]
• Energy Level: [Bustling/calm/tense/peaceful]
• Day vs Night Mood:
• Weather Effects: [How rain, snow, etc. change the feel]
• Seasonal Mood Shifts:

HISTORY & SIGNIFICANCE
──────────────────────
• Origin/How It Came To Be:
• Historical Events Here:
• Cultural Significance:
• Secrets or Hidden History:

STORY SIGNIFICANCE
──────────────────
• Role in the Plot: [Why does this location matter?]
• Scenes Set Here: [What kinds of scenes happen here]
• Thematic Connection: [What themes does it reinforce]
• Character Associations: [Who is connected to this place]

CONNECTIONS
───────────
• Connected Locations: [What's nearby or accessible from here]
• Travel Methods: [How do people get here/leave]
• Travel Times: [How long to reach from other key locations]

PRACTICAL DETAILS
─────────────────
• Population (if applicable):
• Economy/Resources (if applicable):
• Dangers/Hazards:
• Safe Areas:
```

## WORLD MAP CONTEXT

After all locations, provide:
1. How these locations relate geographically
2. Major travel routes between them
3. Any contested or border areas
4. Natural barriers (mountains, rivers, etc.)

## Output Requirements
- Complete ALL sections for EACH location
- Be SPECIFIC and VIVID with sensory details
- Make each location feel UNIQUE and memorable
- Include emotional atmosphere, not just physical description
- Write at least 2500 words total""",
        expected_output=f"""A comprehensive location document of at least 2500 words containing:
1. {num_locations} complete location profiles with ALL sections filled
2. Rich sensory details (sight, sound, smell, touch) for each location
3. Atmosphere and mood descriptions
4. Historical significance and story relevance
5. Geographic connections between locations

Each location must feel distinct and immersive, with specific sensory details that a writer could use to bring scenes to life.""",
        agent=agent,
        context=[story_task]
    )


def create_item_catalog_task(
    agent: Agent,
    story_task: Task,
    character_task: Task
) -> Task:
    """Create the item cataloging task."""
    return Task(
        description=f"""# Item & Object Catalog

## Your Task
Identify and catalog ALL significant items and objects in this story. These are items that:
- Play a role in the plot
- Have emotional significance to characters
- Are used as symbols or motifs
- Are weapons, tools, or magical objects
- Will be mentioned multiple times

## IMPORTANT: Chekhov's Gun Principle
Every significant item you create should be USED in the story. If you introduce an ancient sword, it must be drawn. If you mention a locket, it must matter.

## ITEM PROFILE TEMPLATE

For EACH significant item:

```
┌─────────────────────────────────────────────────────────────┐
│ ITEM: [NAME]                                                │
│ Category: [Weapon / Tool / Artifact / Personal Item / etc.] │
└─────────────────────────────────────────────────────────────┘

PHYSICAL DESCRIPTION
────────────────────
• Appearance: [Detailed visual description]
• Size: [Dimensions or relative size]
• Weight: [Heavy/light, specific if needed]
• Material: [What it's made of]
• Condition: [New/old, pristine/worn]
• Distinguishing Features: [What makes it recognizable]

PROPERTIES
──────────
• Function: [What it does or is used for]
• Special Abilities (if any): [Magical or unusual properties]
• Limitations: [What it can't do, costs, restrictions]
• How It's Activated/Used:

OWNERSHIP & LOCATION
────────────────────
• Original Owner/Creator:
• Current Owner:
• Current Location:
• Ownership History: [How has it changed hands]

HISTORY & ORIGIN
────────────────
• How It Was Created:
• Age:
• Notable Past Events: [Important moments in its history]
• Legends/Rumors About It:

STORY SIGNIFICANCE
──────────────────
• Plot Role: [How does it affect the story]
• First Appearance: [When/how is it introduced]
• Key Scenes Involving It:
• Symbolic Meaning: [What does it represent]
• Which Characters Interact With It:

TRACKING NOTES
──────────────
[For continuity - track where this item is at key story points]
• Start of Story: [Location]
• Midpoint: [Location]
• Climax: [Location]
• End: [Location]
```

## REQUIRED ITEM CATEGORIES

You must include items from these categories (at least 1-2 each):

1. **Weapons/Combat Items**: Swords, staffs, armor, etc.
2. **Personal Treasures**: Items of emotional significance
3. **Plot Devices**: Items that drive story events
4. **World-Building Items**: Items that reveal the world (technology, culture)
5. **Symbolic Objects**: Items that carry thematic weight

## ITEM RELATIONSHIP MAP

After cataloging items, provide:
1. Which items are connected to which characters
2. Any items that interact with each other
3. Items that are sought after (and by whom)
4. Items that are hidden or lost (and their locations)

## Output Requirements
- Catalog at least 10-15 significant items
- Complete ALL sections for each item
- Include at least 2 items per required category
- Track ownership and location throughout the story
- Write at least 1500 words total""",
        expected_output="""A comprehensive item catalog of at least 1500 words containing:
1. 10-15 fully detailed item profiles
2. Items from all required categories (weapons, personal treasures, plot devices, etc.)
3. Physical descriptions, properties, and history for each item
4. Story significance and symbolic meaning
5. Ownership/location tracking for continuity

Each item must have a clear purpose in the story and be tracked for continuity.""",
        agent=agent,
        context=[story_task, character_task]
    )


def create_timeline_task(
    agent: Agent,
    plot_task: Task
) -> Task:
    """Create the timeline management task."""
    return Task(
        description=f"""# Story Timeline Document

## Your Task
Create a COMPLETE timeline for this story, tracking:
- When every major event happens
- Where characters are at any given time
- How much time passes between events
- Seasonal and time-of-day consistency

## TIMELINE FORMAT

### MASTER TIMELINE

Create a day-by-day (or period-by-period for longer spans) timeline:

```
╔═══════════════════════════════════════════════════════════════════╗
║                        STORY TIMELINE                              ║
╚═══════════════════════════════════════════════════════════════════╝

STORY START DATE: [Establish when the story begins]
STORY END DATE: [When it concludes]
TOTAL DURATION: [How much time passes]

═══════════════════════════════════════════════════════════════════
PROLOGUE / BACKSTORY EVENTS (Before Story Start)
═══════════════════════════════════════════════════════════════════
[Date/Period] | [Event] | [Characters Involved] | [Location]
───────────────────────────────────────────────────────────────────
• [Years ago]: [Backstory event 1]
• [Years ago]: [Backstory event 2]
...

═══════════════════════════════════════════════════════════════════
ACT 1 TIMELINE
═══════════════════════════════════════════════════════════════════

DAY 1 - [Date if applicable]
─────────────────────────────
Morning:
  • [Time] - [Event] - [Characters] - [Location]
  • [Time] - [Event] - [Characters] - [Location]
Afternoon:
  • [Time] - [Event] - [Characters] - [Location]
Evening:
  • [Time] - [Event] - [Characters] - [Location]
Night:
  • [Time] - [Event] - [Characters] - [Location]

DAY 2 - [Date if applicable]
─────────────────────────────
[Continue pattern...]

[For time skips:]
═══════════════════════════════════════════════════════════════════
TIME SKIP: [Duration] passes
═══════════════════════════════════════════════════════════════════
What happens during this time:
• [Character 1]: [What they do during the skip]
• [Character 2]: [What they do during the skip]
• World changes: [Any relevant changes]

[Continue for Acts 2 and 3...]
```

### CHARACTER LOCATION TRACKER

For each main character, track where they are:

```
CHARACTER: [Name]
──────────────────────────────────────────────
Day 1: [Location] → [Location if they move]
Day 2: [Location]
Day 3: [Location] → [Location] → [Location]
...
```

### CONSISTENCY CHECKS

Flag and resolve:
1. **Travel Time Issues**: Can characters get from A to B in the stated time?
2. **Simultaneous Events**: Track what's happening at the same time in different places
3. **Character Conflicts**: Is anyone in two places at once?
4. **Seasonal Consistency**: Does weather/season match the timeline?
5. **Age/Time Consistency**: Do ages and time references match?

### KEY TIMELINE MOMENTS

List the most important moments with EXACT timing:
1. Inciting Incident: [When exactly]
2. First Plot Point: [When exactly]
3. Midpoint: [When exactly]
4. Crisis: [When exactly]
5. Climax: [When exactly]
6. Resolution: [When exactly]

## Output Requirements
- Create a COMPLETE day-by-day timeline for the main story events
- Track ALL main characters' locations throughout
- Note all time skips and what happens during them
- Verify there are no timeline contradictions
- Write at least 1500 words""",
        expected_output="""A comprehensive timeline document of at least 1500 words containing:
1. Complete master timeline with day-by-day events
2. Character location tracking for all main characters
3. Time-of-day details for key scenes
4. All time skips documented with what happens during them
5. Consistency verification (no characters in two places at once)
6. Key story moments with exact timing

The timeline must be detailed enough to prevent continuity errors during writing.""",
        agent=agent,
        context=[plot_task]
    )


# =============================================================================
# FANTASY-SPECIFIC TASKS
# =============================================================================

def create_magic_system_task(
    agent: Agent,
    story_task: Task,
    hardness: float = 0.5
) -> Task:
    """Create the magic system design task."""
    system_type = "hard (clear rules)" if hardness > 0.7 else "balanced" if hardness > 0.3 else "soft (mysterious)"

    return Task(
        description=f"""# Magic/Power System Design

## Your Task
Design a {system_type} magic or power system for this story.

## SANDERSON'S LAWS OF MAGIC (Follow These!)

1. **First Law**: The ability of magic to solve problems is proportional to how well the reader understands it.
2. **Second Law**: Limitations are more interesting than powers.
3. **Third Law**: Expand what you have before adding something new.

## MAGIC SYSTEM DOCUMENT

```
╔═══════════════════════════════════════════════════════════════════╗
║                    MAGIC SYSTEM: [NAME]                            ║
╚═══════════════════════════════════════════════════════════════════╝

OVERVIEW
────────
[2-3 paragraphs explaining the magic system]

SOURCE OF POWER
───────────────
• Where Magic Comes From: [Internal/external, divine/natural, etc.]
• Who Can Use It: [Everyone? Selected? Bloodlines?]
• How It's Accessed: [Innate? Learned? Granted?]
• Is It Finite or Renewable:

FUNDAMENTAL RULES
─────────────────
Rule 1: [State a clear rule]
  → Implications: [What this means for users]
  → Exceptions: [Any exceptions]

Rule 2: [State a clear rule]
  → Implications: [What this means for users]
  → Exceptions: [Any exceptions]

Rule 3: [State a clear rule]
  → Implications: [What this means for users]
  → Exceptions: [Any exceptions]

[Continue for 4-6 fundamental rules]

COSTS & LIMITATIONS (Most Important Section!)
─────────────────────────────────────────────
Physical Costs:
• [Cost 1]: [Description and severity]
• [Cost 2]: [Description and severity]

Mental/Emotional Costs:
• [Cost 1]: [Description and severity]
• [Cost 2]: [Description and severity]

Resource Costs:
• [Cost 1]: [What's consumed]
• [Cost 2]: [What's consumed]

Hard Limits (Things Magic CANNOT Do):
• Cannot: [Limitation 1]
• Cannot: [Limitation 2]
• Cannot: [Limitation 3]
• Cannot: [Limitation 4]

ABILITIES/POWERS CATALOG
────────────────────────
For each distinct ability:

ABILITY: [Name]
├── Effect: [What it does]
├── Cost: [What it costs to use]
├── Limitations: [When it doesn't work]
├── Skill Required: [Beginner/Intermediate/Expert/Master]
└── Who Has It: [Which characters]

[List 8-12 abilities]

POWER LEVELS/PROGRESSION
────────────────────────
Level/Rank System (if applicable):
• Rank 1 - [Name]: [Description, typical abilities]
• Rank 2 - [Name]: [Description, typical abilities]
• Rank 3 - [Name]: [Description, typical abilities]
[Continue as needed]

How Users Progress:
• [Method 1 for advancement]
• [Method 2 for advancement]
• [Time required]
• [Bottlenecks/challenges]

CHARACTER POWER ASSIGNMENTS
───────────────────────────
[Character 1]:
• Current Level:
• Abilities: [List]
• Unique Traits:
• Power Ceiling: [How strong can they become]

[Repeat for each magic-using character]

STORY APPLICATIONS
──────────────────
How Magic Solves Problems: [List ways magic can resolve conflicts]
How Magic Creates Problems: [List ways magic causes/complicates conflicts]
Magic in Combat: [How it's used in fights]
Magic in Daily Life: [How it affects normal activities]

```

## Output Requirements
- Design a complete, internally consistent magic system
- Include at least 4-6 fundamental rules
- Include more LIMITATIONS than powers
- Catalog at least 8-12 distinct abilities
- Assign powers to each relevant character
- Write at least 2000 words""",
        expected_output="""A comprehensive magic system document of at least 2000 words containing:
1. Clear source and nature of magic
2. 4-6 fundamental rules with implications
3. Detailed costs and limitations (more than powers)
4. Catalog of 8-12 abilities with costs and requirements
5. Power level/progression system
6. Character power assignments

The magic system must follow Sanderson's Laws and be internally consistent.""",
        agent=agent,
        context=[story_task]
    )


def create_faction_management_task(
    agent: Agent,
    story_task: Task,
    character_task: Task
) -> Task:
    """Create the faction management task."""
    return Task(
        description=f"""# Faction & Organization Document

## Your Task
Design all major factions, organizations, nations, or groups in this story.

## FACTION PROFILE TEMPLATE

For EACH faction:

```
╔═══════════════════════════════════════════════════════════════════╗
║  FACTION: [NAME]                                                   ║
║  Type: [Nation / Guild / Order / Corporation / Cult / etc.]        ║
╚═══════════════════════════════════════════════════════════════════╝

IDENTITY
────────
• Full Name:
• Common Name/Nickname:
• Symbol/Emblem: [Describe their insignia]
• Colors: [Official colors]
• Motto/Slogan:
• Public Image: [How they're perceived]
• True Nature: [What they're really like]

HISTORY
───────
• Founded: [When and by whom]
• Original Purpose:
• Key Historical Events:
  - [Event 1]
  - [Event 2]
  - [Event 3]
• Current Status: [Rising/stable/declining]

IDEOLOGY & GOALS
────────────────
• Core Beliefs: [What do they believe in]
• Ultimate Goal: [What they're working toward]
• Public Goals: [What they claim to want]
• Secret Goals (if any): [Hidden agenda]
• Methods: [How do they achieve goals - ethical/unethical]

STRUCTURE
─────────
• Leadership Type: [Democracy/Monarchy/Council/etc.]
• Current Leader(s): [Name and brief description]
• Hierarchy:
  - [Top Level]: [Title and role]
  - [Second Level]: [Title and role]
  - [Third Level]: [Title and role]
  - [Base Level]: [Regular members]
• How to Join:
• How to Advance:

RESOURCES
─────────
• Territory/Holdings: [What land/buildings they control]
• Military Strength: [How powerful are they in combat]
• Magical/Special Resources: [Unique capabilities]
• Wealth: [Rich/moderate/poor]
• Influence: [Political/social power]

KEY MEMBERS
───────────
• [Name]: [Role] - [Brief description]
• [Name]: [Role] - [Brief description]
• [Name]: [Role] - [Brief description]
[Connect to characters from character document]

RELATIONSHIPS WITH OTHER FACTIONS
─────────────────────────────────
• ALLIED with [Faction]: [Why and how strong]
• HOSTILE to [Faction]: [Why and history of conflict]
• NEUTRAL toward [Faction]: [Why]
• SECRETLY [relationship] with [Faction]: [Hidden dynamics]

ROLE IN STORY
─────────────
• How They Enter the Plot:
• What They Want from Protagonists:
• What They Offer:
• What They Threaten:
• Key Scenes Involving Them:
```

## REQUIRED FACTIONS

Include at least:
1. **Primary Allied Faction**: Group that helps the protagonist
2. **Primary Enemy Faction**: Main antagonistic group
3. **Neutral/Wild Card Faction**: Group that could go either way
4. **Background Factions**: 2-3 groups that provide world context

## FACTION RELATIONSHIP MAP

After all factions, provide:
```
FACTION RELATIONSHIPS
─────────────────────
[Faction A] ←──ALLIED──→ [Faction B]
[Faction A] ←──HOSTILE──→ [Faction C]
[Faction B] ←──NEUTRAL──→ [Faction C]
[etc.]

CURRENT CONFLICTS
─────────────────
• [Faction] vs [Faction]: [What they're fighting over]
• [Faction] vs [Faction]: [What they're fighting over]

POTENTIAL ALLIANCES
───────────────────
• [Faction] could ally with [Faction] if: [Condition]
```

## Output Requirements
- Create at least 5-6 distinct factions
- Complete ALL sections for each faction
- Show relationships between all factions
- Connect factions to story characters
- Write at least 2000 words""",
        expected_output="""A comprehensive faction document of at least 2000 words containing:
1. 5-6 fully detailed faction profiles
2. History, ideology, structure, and resources for each
3. Key members connected to story characters
4. Complete faction relationship map
5. Current conflicts and potential alliances

Each faction must feel distinct and have a clear role in the story.""",
        agent=agent,
        context=[story_task, character_task]
    )


def create_lore_document_task(
    agent: Agent,
    story_task: Task,
    location_task: Task
) -> Task:
    """Create the lore documentation task."""
    return Task(
        description=f"""# World Lore & History Document

## Your Task
Create the historical and mythological lore that forms the foundation of this world.

## LORE DOCUMENT STRUCTURE

```
╔═══════════════════════════════════════════════════════════════════╗
║                        WORLD LORE BIBLE                           ║
╚═══════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════
PART 1: CREATION & COSMOLOGY
═══════════════════════════════════════════════════════════════════

CREATION MYTH
─────────────
[Tell the world's creation story - how people believe the world began]
[2-3 paragraphs minimum]

COSMOLOGY
─────────
• The World's Structure: [Flat/round, continents, etc.]
• Other Planes/Realms (if any):
• The Afterlife (beliefs):
• Celestial Bodies and Their Meaning:

═══════════════════════════════════════════════════════════════════
PART 2: HISTORICAL TIMELINE
═══════════════════════════════════════════════════════════════════

THE AGES OF THE WORLD

FIRST AGE: [Name] (circa [dates])
─────────────────────────────────
• Overview: [What defined this era]
• Major Events:
  - [Event 1]: [Description]
  - [Event 2]: [Description]
• How It Ended:
• Legacy: [How it affects the present]

SECOND AGE: [Name] (circa [dates])
──────────────────────────────────
[Continue pattern...]

[Continue for 3-5 ages]

CURRENT AGE: [Name] (ongoing)
─────────────────────────────
• Overview:
• Recent History (last 100 years):
• Current State of the World:

═══════════════════════════════════════════════════════════════════
PART 3: MYTHOLOGY & RELIGION
═══════════════════════════════════════════════════════════════════

THE GODS/DIVINE BEINGS
──────────────────────
[For each deity or major divine being:]

[DEITY NAME]
• Domain: [What they're god of]
• Appearance: [How they're depicted]
• Personality: [How they're characterized]
• Worshippers: [Who prays to them]
• Symbols: [Sacred symbols]
• Holy Days: [Special days]
• Myths About Them: [Brief legendary story]

[Repeat for each deity]

MAJOR MYTHS & LEGENDS
─────────────────────
Legend 1: [Title]
[Tell the legend in 1-2 paragraphs]
• Moral/Lesson:
• How It Affects Current Beliefs:

[Include 3-5 significant legends]

RELIGIOUS PRACTICES
───────────────────
• Common Prayers/Blessings:
• Funeral Rites:
• Marriage Customs:
• Coming-of-Age Rituals:
• Taboos: [What's forbidden]
• Holy Places:

═══════════════════════════════════════════════════════════════════
PART 4: CULTURES & CUSTOMS
═══════════════════════════════════════════════════════════════════

NAMING CONVENTIONS
──────────────────
• [Culture 1]: [How names work - structure, meanings]
• [Culture 2]: [How names work]
• Titles and Honorifics:

COMMON CUSTOMS
──────────────
• Greetings: [How people greet each other]
• Hospitality: [Guest customs]
• Trade/Commerce: [How deals are made]
• Social Classes: [How society is stratified]

LANGUAGE
────────
• Common Tongue: [What most people speak]
• Other Languages: [Regional/racial languages]
• Key Phrases: [Useful phrases characters might use]
• Curses/Oaths: [How people swear]

═══════════════════════════════════════════════════════════════════
PART 5: KNOWLEDGE LEVELS
═══════════════════════════════════════════════════════════════════

What Different People Know:

COMMON KNOWLEDGE (Everyone knows)
─────────────────────────────────
• [Fact 1]
• [Fact 2]
• [Fact 3]

EDUCATED KNOWLEDGE (Scholars/nobles know)
─────────────────────────────────────────
• [Fact 1]
• [Fact 2]
• [Fact 3]

RARE KNOWLEDGE (Few know)
─────────────────────────
• [Fact 1]
• [Fact 2]

SECRET KNOWLEDGE (Hidden truths)
────────────────────────────────
• [Secret 1]: [Who knows this and why it's hidden]
• [Secret 2]: [Who knows this and why it's hidden]

```

## Output Requirements
- Create a comprehensive lore document
- Include creation myth and cosmology
- Provide 3-5 historical ages with major events
- Design at least 3-5 deities/divine beings with myths
- Include cultural customs and language notes
- Separate knowledge into what different people would know
- Write at least 2500 words""",
        expected_output="""A comprehensive lore document of at least 2500 words containing:
1. Creation myth and cosmology
2. Historical timeline with 3-5 ages
3. 3-5 deities with descriptions and myths
4. 3-5 major legends told in narrative form
5. Cultural customs, naming conventions, and language
6. Knowledge levels (common, educated, rare, secret)

The lore must feel cohesive and provide enough detail for consistent world-building.""",
        agent=agent,
        context=[story_task, location_task]
    )


# =============================================================================
# LIGHT NOVEL SPECIFIC TASKS
# =============================================================================

def create_arc_design_task(
    agent: Agent,
    story_task: Task,
    arc_number: int,
    chapters_in_arc: int,
    previous_arc_task: Optional[Task] = None
) -> Task:
    """Create an arc design task for light novels."""
    context = [story_task]
    if previous_arc_task:
        context.append(previous_arc_task)

    return Task(
        description=f"""# Story Arc {arc_number} Design

## Your Task
Design Arc {arc_number} spanning approximately {chapters_in_arc} chapters.

## ARC DOCUMENT

```
╔═══════════════════════════════════════════════════════════════════╗
║                     ARC {arc_number}: [TITLE]                      ║
║                    Chapters [X] - [Y]                              ║
╚═══════════════════════════════════════════════════════════════════╝

ARC PREMISE
───────────
[2-3 paragraphs describing what this arc is about]

THE HOOK
────────
[What makes readers excited for this arc - the promise/appeal]

ARC GOAL
────────
• What the protagonist must achieve:
• Why it matters:
• What happens if they fail:

ARC ANTAGONIST
──────────────
• Name/Identity:
• Motivation:
• Threat Level:
• Connection to Main Story:
• Their Plan:
• Their Weakness:

CHARACTER FOCUS
───────────────
Primary Focus Characters: [Who gets the most development]
• [Character 1]: [What happens with them this arc]
• [Character 2]: [What happens with them this arc]

Secondary Characters: [Who appears but isn't central]
• [Character]: [Their role this arc]

New Characters Introduced:
• [New Character]: [Brief intro and purpose]

Characters Absent/Reduced:
• [Character]: [Why they're not around]

POWER PROGRESSION
─────────────────
Skills/Abilities Gained:
• [Character]: [New ability] - [How they get it]

Level/Rank Changes:
• [Character]: [From X to Y] - [Chapter it happens]

Limitations Discovered:
• [What limitations are revealed about existing powers]

═══════════════════════════════════════════════════════════════════
CHAPTER BREAKDOWN
═══════════════════════════════════════════════════════════════════

OPENING SEQUENCE (Chapters 1-3 of arc)
──────────────────────────────────────
Chapter [X]: [Title]
• Summary: [2-3 sentences]
• Hook: [Why readers continue]
• Key Events: [Bullet points]

Chapter [X+1]: [Title]
• Summary:
• Escalation: [How stakes rise]
• Key Events:

Chapter [X+2]: [Title]
• Summary:
• Arc Goal Established: [When protagonist commits to goal]
• Key Events:

RISING ACTION (Middle chapters)
───────────────────────────────
[Continue pattern for each chapter with:]
• Summary
• Complication/escalation
• Key events
• Cliffhanger (for most chapters)

MIDPOINT TWIST (Middle of arc)
──────────────────────────────
Chapter [X]:
• The Twist: [Major revelation or shift]
• How It Changes Things:
• Character Reactions:

ESCALATION TO CLIMAX
────────────────────
[Continue chapter breakdowns]

ARC CLIMAX (Last 2-3 chapters)
──────────────────────────────
Chapter [X]: [Pre-Climax]
• Setup for finale:
• Final confrontation begins:

Chapter [X+1]: [Climax]
• The Confrontation: [What happens]
• Resolution: [How it ends]

Chapter [X+2]: [Resolution/Setup]
• Aftermath: [What the world looks like after]
• Setup for Next Arc: [What's teased]
• Cliffhanger: [Hook for next arc]

═══════════════════════════════════════════════════════════════════
CLIFFHANGER SCHEDULE
═══════════════════════════════════════════════════════════════════

Major Cliffhangers (Every 5-7 chapters):
• Chapter [X]: [Type - danger/mystery/revelation] - [What happens]
• Chapter [X]: [Type] - [What happens]

Minor Hooks (Every chapter):
• End each chapter with a reason to continue

═══════════════════════════════════════════════════════════════════
CONNECTION TO OVERALL STORY
═══════════════════════════════════════════════════════════════════

Plot Threads Advanced:
• [Thread]: [How it progresses]

Setups Paid Off (from previous arcs):
• [Setup]: [Payoff]

New Setups Planted (for future):
• [Setup]: [Intended payoff arc]

```

## Output Requirements
- Design a complete arc with all sections
- Provide chapter-by-chapter breakdown
- Include cliffhanger schedule
- Connect to overall story
- Write at least 2000 words""",
        expected_output=f"""A comprehensive Arc {arc_number} document of at least 2000 words containing:
1. Arc premise, hook, goal, and antagonist
2. Character focus with developments and new characters
3. Power progression details
4. Chapter-by-chapter breakdown for all {chapters_in_arc} chapters
5. Cliffhanger schedule (major and minor)
6. Connections to previous and future arcs

The arc must feel complete on its own while advancing the overall story.""",
        agent=agent,
        context=context
    )


def create_plot_structure_task(
    agent: Agent,
    story_task: Task,
    character_task,  # Can be Task or str
    location_task,   # Can be Task or str
    num_chapters: int
) -> Task:
    """Create the plot structure task with scene-level detail.

    Args:
        agent: The plot architect agent
        story_task: The story architecture task
        character_task: Either a Task object or a string summary of characters
        location_task: Either a Task object or a string summary of locations
        num_chapters: Number of chapters to plan
    """
    # Build context list - include strings directly in description if not Task objects
    context = [story_task]
    extra_context = ""

    if isinstance(character_task, Task):
        context.append(character_task)
    elif isinstance(character_task, str) and character_task:
        extra_context += f"\n\n## CHARACTER INFORMATION\n{character_task[:8000]}"

    if isinstance(location_task, Task):
        context.append(location_task)
    elif isinstance(location_task, str) and location_task:
        extra_context += f"\n\n## LOCATION INFORMATION\n{location_task[:6000]}"

    return Task(
        description=f"""# Plot Structure Document
{extra_context}

## Your Task
Create the detailed plot structure for all {num_chapters} chapters.

NOTE: For large chapter counts, group chapters into sections and provide representative detail.

## PLOT STRUCTURE FORMAT

For each chapter:

```
═══════════════════════════════════════════════════════════════════
CHAPTER [NUMBER]: [TITLE]
═══════════════════════════════════════════════════════════════════

CHAPTER OVERVIEW
────────────────
• One-Line Summary:
• Purpose in Story: [Why this chapter exists]
• POV Character:
• Timeline: [When it happens]
• Location(s):

SCENE BREAKDOWN
───────────────
SCENE 1:
├── Setting: [Location, time of day]
├── Characters: [Who's present]
├── Goal: [What POV character wants]
├── Conflict: [What opposes them]
├── Outcome: [What happens - success/failure/twist]
├── Key Dialogue: [Important conversation points]
└── Word Count Target: [Approximate]

SCENE 2:
[Same structure...]

[Continue for all scenes in chapter]

CHAPTER BEATS
─────────────
• Opening Hook: [First line/moment that grabs attention]
• Rising Tension: [How tension builds]
• Chapter Climax: [Peak moment of the chapter]
• Closing Hook: [Why readers turn the page]

PLOT THREADS
────────────
• Advanced: [Which plot threads move forward]
• Introduced: [New threads started]
• Referenced: [Threads mentioned but not advanced]

CHARACTER DEVELOPMENT
─────────────────────
• [Character]: [How they change/what we learn]

═══════════════════════════════════════════════════════════════════
```

## For {num_chapters} Chapters:

{"Provide FULL breakdowns for chapters 1-10, then summary breakdowns (overview + key scenes) for remaining chapters grouped by arc or act." if num_chapters > 20 else "Provide full breakdowns for all chapters."}

## PLOT THREAD TRACKER

At the end, provide:
```
ACTIVE PLOT THREADS
───────────────────
Thread 1: [Name]
├── Started: Chapter [X]
├── Status: [Active/Resolved/Dormant]
└── Key Chapters: [X, Y, Z]

[Continue for all threads]
```

## Output Requirements
- Create chapter structure for ALL {num_chapters} chapters
- Full detail for first 10 chapters
- Summary + key scenes for remaining chapters
- Track all plot threads
- Write at least 3000 words""",
        expected_output=f"""A comprehensive plot structure document of at least 3000 words containing:
1. Detailed breakdowns for the first 10 chapters (scenes, beats, hooks)
2. Summary breakdowns for remaining chapters
3. Scene goals, conflicts, and outcomes using scene-sequel structure
4. Complete plot thread tracking
5. Character development notes per chapter

The structure must be detailed enough to guide actual chapter writing.""",
        agent=agent,
        context=context  # Uses dynamically built context list
    )


def create_character_roster_task(
    agent: Agent,
    character_task: Task,
    current_chapter: int
) -> Task:
    """Create a character roster management task."""
    return Task(
        description=f"""# Character Roster Status - Chapter {current_chapter}

## Your Task
Review and update the character roster status.

## ROSTER REPORT

```
═══════════════════════════════════════════════════════════════════
CHARACTER ROSTER STATUS - CHAPTER {current_chapter}
═══════════════════════════════════════════════════════════════════

MAIN CHARACTERS
───────────────
[For each main character:]

[CHARACTER NAME]
├── Last Appearance: Chapter [X]
├── Chapters Since Seen: [Number]
├── Current Location: [Where they are]
├── Current Status: [Healthy/Injured/Missing/etc.]
├── Current Goal: [What they're working toward]
├── Relationship Changes: [Any recent shifts]
└── Reintro Needed: [Yes/No - Yes if 20+ chapters absent]

SUPPORTING CHARACTERS
─────────────────────
[Same format, briefer]

SCREEN TIME ANALYSIS
────────────────────
Most Featured (Last 20 Chapters):
1. [Character]: [X appearances]
2. [Character]: [X appearances]
...

Underutilized (Need more time):
• [Character]: [Last seen Chapter X]
• [Character]: [Last seen Chapter X]

REINTRODUCTION QUEUE
────────────────────
Characters needing reintroduction soon:

[CHARACTER NAME]
├── Last Seen: Chapter [X] ([Y] chapters ago)
├── What They've Been Doing: [Off-screen activities]
├── Suggested Return: Chapter [X]
└── Return Context: [How to bring them back naturally]

RELATIONSHIP STATUS UPDATE
──────────────────────────
Changed Relationships:
• [Char A] & [Char B]: [Old status] → [New status]

Developing Relationships:
• [Char A] & [Char B]: [Current trajectory]

```

## Output Requirements
- Track ALL characters from the character document
- Identify anyone missing for 20+ chapters
- Provide reintroduction plans for absent characters
- Analyze screen time distribution
- Write at least 1000 words""",
        expected_output=f"""A character roster status report of at least 1000 words containing:
1. Status of all main and supporting characters at Chapter {current_chapter}
2. Appearance tracking with chapters since last seen
3. Screen time analysis for the last 20 chapters
4. Reintroduction queue with plans for absent characters
5. Relationship status updates

The report must prevent any character from being forgotten.""",
        agent=agent,
        context=[character_task]
    )


# =============================================================================
# CHAPTER WRITING TASKS
# =============================================================================

def create_chapter_writing_task(
    agent: Agent,
    story_task: Task,
    plot_task: Task,
    chapter_number: int,
    chapter_outline: str,
    character_context: str = "",
    location_context: str = "",
    previous_chapter_summary: str = "",
    genre_config: Optional[Dict[str, Any]] = None,
    context_window: int = 40000
) -> Task:
    """
    Create a task for writing a complete chapter.

    This task produces actual prose - a full chapter of the novel.
    """
    genre_guidance = ""
    if genre_config:
        genre_guidance = f"""
## Genre Style: {genre_config.get('name', 'Literary Fiction')}
- Tone: {genre_config.get('tone', 'engaging')}
- Pacing: {genre_config.get('pacing', 'moderate')}
- Style Notes: {genre_config.get('style_notes', 'Clear, evocative prose')}
"""

    prev_chapter_context = ""
    if previous_chapter_summary:
        prev_chapter_context = f"""
## Previous Chapter Summary (for continuity)
{previous_chapter_summary}

IMPORTANT: Ensure continuity with the previous chapter. Characters should be where they were left off.
"""

    # Get dynamic context guidance
    context_guidance = get_context_reminder(context_window)

    # Determine word count requirements based on context window
    if context_window >= 100000:
        min_words = 3000
        target_words = "3000-5000"
        min_paragraphs = 60
    elif context_window >= 32000:
        min_words = 2500
        target_words = "2500-4000"
        min_paragraphs = 50
    else:
        min_words = 2000
        target_words = "2000-3000"
        min_paragraphs = 40

    return Task(
        description=f"""Write Chapter {chapter_number} as complete novel prose.

{context_guidance}

{genre_guidance}

CHAPTER OUTLINE:
{chapter_outline}

{prev_chapter_context}

CHARACTER REFERENCE:
{character_context[:4000] if character_context else "Use characters from the story context."}

LOCATION REFERENCE:
{location_context[:3000] if location_context else "Use locations from the story context."}

CRITICAL REQUIREMENTS:

1. MINIMUM {min_words} WORDS - This is mandatory. Target {target_words} words.
   Write at least {min_paragraphs} paragraphs of actual prose.

2. WRITE PROSE ONLY - No outlines, no scene labels, no "Scene 1:", no "ACT 1:", no meta-commentary.
   Just write the story as a reader would read it in a published novel.

3. NO REPETITION - Every paragraph must advance the story. Never repeat the same phrase or
   sentence. If you find yourself writing similar content, move forward in the plot.

4. SHOW DON'T TELL - Use sensory details, dialogue, and action. Avoid summary statements
   like "He felt sad" - instead show through behavior and physical reactions.

5. DIALOGUE - Include substantial dialogue between characters. Each character should sound
   different. Use "said" for most tags. Include action beats between dialogue lines.

6. STRUCTURE - Start with an engaging hook. Build tension through the middle. End with a
   hook that makes readers want to continue.

YOUR OUTPUT FORMAT:
Start with: Chapter {chapter_number}: [Your Title Here]

Then write continuous prose paragraphs. Use proper paragraph breaks. Include dialogue
formatted correctly with quotation marks. Do not use markdown headers within the chapter
except for the title. Do not include code blocks, scene numbers, or structural labels.

Write the chapter now. Remember: MINIMUM 2500 WORDS of actual story prose.""",
        expected_output=f"""Chapter {chapter_number} as complete prose containing:
- A title line
- At least 2500 words (approximately 50+ paragraphs)
- Multiple scenes with dialogue and action
- Sensory descriptions and atmosphere
- Character development through behavior
- An ending that hooks into the next chapter

The output must be pure prose suitable for publication, not an outline or summary.""",
        agent=agent,
        context=[story_task, plot_task]
    )


def create_scene_writing_task(
    agent: Agent,
    story_task: Task,
    scene_outline: str,
    scene_number: int,
    chapter_number: int,
    pov_character: str,
    location: str,
    characters_present: List[str],
    scene_goal: str,
    previous_scene_ending: str = ""
) -> Task:
    """
    Create a task for writing a single scene (for more granular control).
    """
    return Task(
        description=f"""# Write Scene {scene_number} of Chapter {chapter_number}

{CONTEXT_REMINDER}

## Scene Details
- POV Character: {pov_character}
- Location: {location}
- Characters Present: {', '.join(characters_present)}
- Scene Goal: {scene_goal}

## Scene Outline
{scene_outline}

{f"## Previous Scene Ended With: {previous_scene_ending}" if previous_scene_ending else ""}

## WRITING REQUIREMENTS

### Word Count: 800-1500 words

### Scene-Sequel Structure
SCENE (Goal → Conflict → Disaster) OR SEQUEL (Reaction → Dilemma → Decision)
- If this is a SCENE: Focus on action, dialogue, immediate conflict
- If this is a SEQUEL: Focus on character processing, planning, emotional beats

### POV Discipline
- Stay STRICTLY in {pov_character}'s POV
- Only describe what {pov_character} can see, hear, know
- Filter everything through their perspective and voice
- Show their internal reactions

### Sensory Immersion
For {location}, include:
- Visual details specific to this place
- Sounds (ambient and specific)
- Smells if relevant
- Physical sensations (temperature, texture)
- Atmosphere/mood

### Dialogue (if present)
- Give each character their unique voice
- Use subtext - what they DON'T say matters
- Include action beats between dialogue
- Dialogue should reveal character or advance plot

### Pacing
- Match pacing to scene type (action = fast, emotional = measured)
- Vary sentence structure
- Use white space effectively

## OUTPUT FORMAT

Write ONLY the scene prose. No meta-commentary, no notes.
Start directly with the scene and end at the scene's conclusion.

---

[Scene prose begins here...]""",
        expected_output=f"""A complete scene of 800-1500 words for Scene {scene_number} of Chapter {chapter_number} containing:
1. Strict POV from {pov_character}'s perspective
2. Immersive sensory details for {location}
3. Clear scene structure (goal-conflict-outcome or reaction-dilemma-decision)
4. Distinct dialogue voices for all characters
5. Appropriate pacing for the scene type

The scene should seamlessly connect to surrounding scenes.""",
        agent=agent,
        context=[story_task]
    )


def create_chapter_compilation_task(
    agent: Agent,
    scenes: List[str],
    chapter_number: int,
    chapter_title: str = ""
) -> Task:
    """
    Create a task for compiling multiple scenes into a cohesive chapter.
    """
    scenes_text = "\n\n---\n\n".join([f"### Scene {i+1}\n{scene}" for i, scene in enumerate(scenes)])

    return Task(
        description=f"""# Compile Chapter {chapter_number}

## Your Task
Combine the following scenes into a cohesive, polished chapter.

## Scenes to Compile
{scenes_text}

## COMPILATION REQUIREMENTS

### Smooth Transitions
- Ensure scene transitions flow naturally
- Add brief transitional phrases where needed
- Maintain consistent pacing across the chapter

### Continuity Check
- Verify character positions make sense
- Check time flow is logical
- Ensure no contradictions between scenes

### Polish
- Fix any awkward phrasings
- Ensure consistent tense
- Verify dialogue attribution is clear

### Format
```markdown
# Chapter {chapter_number}{f': {chapter_title}' if chapter_title else ''}

[Compiled chapter with smooth transitions...]

---
*End of Chapter {chapter_number}*
```

## OUTPUT
Provide the complete, polished chapter ready for publication.""",
        expected_output=f"""A polished, complete Chapter {chapter_number} containing:
1. All provided scenes integrated smoothly
2. Natural transitions between scenes
3. Consistent continuity throughout
4. Professional formatting
5. Approximately {len(scenes) * 1000} words total""",
        agent=agent
    )


def create_chapter_review_task(
    agent: Agent,
    chapter_content: str,
    chapter_number: int,
    story_task: Task,
    character_context: str = ""
) -> Task:
    """
    Create a task for reviewing and improving a written chapter.
    """
    return Task(
        description=f"""# Review Chapter {chapter_number}

## Your Task
Review this chapter for quality and provide specific improvements.

## Chapter Content
{chapter_content}

## CHARACTER REFERENCE
{character_context[:3000] if character_context else "Refer to story context."}

## REVIEW CHECKLIST

### Plot & Structure
- [ ] Does the chapter advance the plot?
- [ ] Is there a clear beginning, middle, end?
- [ ] Does it start with a hook?
- [ ] Does it end with a hook?

### Character
- [ ] Are characters acting consistently?
- [ ] Is dialogue distinct for each character?
- [ ] Is there character development?
- [ ] Are motivations clear?

### Pacing
- [ ] Does the pacing fit the content?
- [ ] Are there any slow/draggy sections?
- [ ] Are action scenes punchy enough?
- [ ] Are emotional scenes given enough space?

### Prose Quality
- [ ] Is the writing clear?
- [ ] Is there unnecessary repetition?
- [ ] Are descriptions vivid without being purple?
- [ ] Is the POV consistent?

### Continuity
- [ ] Any contradictions with previous events?
- [ ] Character positions make sense?
- [ ] Timeline is consistent?

## OUTPUT FORMAT

```
## Review Summary
[Overall assessment: STRONG / ACCEPTABLE / NEEDS WORK]

## Strengths
- [What works well]

## Issues Found
1. [Issue]: [Specific location/quote] - [Why it's a problem]
2. [Issue]: [Specific location/quote] - [Why it's a problem]

## Recommended Fixes
1. [Fix for issue 1 - specific rewrite suggestion]
2. [Fix for issue 2 - specific rewrite suggestion]

## Revised Sections (if needed)
[Provide rewritten versions of problematic sections]
```""",
        expected_output=f"""A thorough review of Chapter {chapter_number} containing:
1. Overall quality assessment
2. Specific strengths identified
3. Specific issues with locations cited
4. Concrete fix recommendations
5. Rewritten versions of any problematic sections""",
        agent=agent,
        context=[story_task]
    )


def parse_chapter_outline(plot_structure: str, chapter_number: int) -> Optional[str]:
    """
    Parse the plot structure to extract outline for a specific chapter.

    Args:
        plot_structure: The full plot structure document
        chapter_number: The chapter number to extract

    Returns:
        The chapter outline string, or None if not found
    """
    import re

    # Try to find the chapter section
    patterns = [
        rf'CHAPTER\s*{chapter_number}[:\s].*?(?=CHAPTER\s*{chapter_number + 1}|$)',
        rf'Chapter\s*{chapter_number}[:\s].*?(?=Chapter\s*{chapter_number + 1}|$)',
        rf'#{1,3}\s*Chapter\s*{chapter_number}.*?(?=#{1,3}\s*Chapter\s*{chapter_number + 1}|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, plot_structure, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0).strip()

    # If no specific chapter found, return a generic structure
    return f"""Chapter {chapter_number}:
- Follow the story structure from the plot document
- Maintain continuity with previous chapters
- Advance the main plot
- Include character development
- End with a hook for the next chapter"""


def create_power_tracking_task(
    agent: Agent,
    magic_task: Task,
    character_task: Task,
    current_chapter: int
) -> Task:
    """Create a power system tracking task."""
    return Task(
        description=f"""# Power System Status - Chapter {current_chapter}

## Your Task
Track and validate the power system status.

## POWER STATUS REPORT

```
═══════════════════════════════════════════════════════════════════
POWER SYSTEM STATUS - CHAPTER {current_chapter}
═══════════════════════════════════════════════════════════════════

CHARACTER POWER STATUS
──────────────────────
[For each combat-capable character:]

[CHARACTER NAME]
├── Current Rank/Level: [X]
├── Abilities:
│   ├── [Ability 1]: [Proficiency level]
│   ├── [Ability 2]: [Proficiency level]
│   └── [Ability 3]: [Proficiency level]
├── Recent Changes:
│   ├── Chapter [X]: [Gained/Lost what]
│   └── Chapter [Y]: [Improvement/Setback]
├── Known Limitations: [What they can't do]
└── Power Trajectory: [Getting stronger/weaker/stable]

PROGRESSION LOG
───────────────
Recent Power-Ups:
• Chapter [X]: [Character] gained [ability/level] by [method]
• Chapter [Y]: [Character] improved [ability] through [training/battle]

Recent Setbacks:
• Chapter [X]: [Character] lost/damaged [ability] due to [reason]

BALANCE CHECK
─────────────
Power Rankings (Current):
1. [Character]: [Level/Strength description]
2. [Character]: [Level/Strength description]
...

Upcoming Challenges vs Character Power:
• [Challenge]: [Can current characters handle it? Y/N/Needs growth]

CONSISTENCY FLAGS
─────────────────
⚠️ Potential Issues:
• [Issue 1]: [Character used ability beyond established limits in Ch X]
• [Issue 2]: [Power-up wasn't properly earned/explained in Ch Y]

✓ Confirmed Consistent:
• [What's working well with power balance]

SYSTEM RULE COMPLIANCE
──────────────────────
Rules Followed: ✓
• [Rule]: [How it was respected]

Rules Bent/Broken: ⚠️
• [Rule]: [How it was violated and where]

```

## Output Requirements
- Track ALL power-using characters
- Log all recent power changes
- Check for balance issues
- Flag any consistency problems
- Write at least 1000 words""",
        expected_output=f"""A power system status report of at least 1000 words containing:
1. Complete power status for all combat-capable characters
2. Progression log with recent changes
3. Balance analysis with power rankings
4. Consistency flags for any rule violations
5. System rule compliance check

The report must catch any power inconsistencies or balance issues.""",
        agent=agent,
        context=[magic_task, character_task]
    )


# =============================================================================
# SCENE PARSING AND BREAKDOWN
# =============================================================================

def parse_scenes_from_plot_structure(plot_structure: str) -> List[Dict[str, Any]]:
    """
    Parse scene breakdowns from plot structure output.

    Returns a list of scene dictionaries with:
    - chapter_number: int
    - chapter_title: str
    - scene_number: int
    - setting: str
    - characters: List[str]
    - pov_character: str
    - goal: str
    - conflict: str
    - outcome: str
    - word_count_target: int
    """
    import re
    scenes = []

    # Find all chapter sections
    chapter_pattern = r'CHAPTER\s+(\d+)[:\s]+([^\n═]+)'
    scene_pattern = r'SCENE\s+(\d+):\s*\n([^S]+?)(?=SCENE\s+\d+:|CHAPTER\s+BEATS|$)'

    # Track current chapter
    current_chapter = None
    current_title = ""

    lines = plot_structure.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for chapter header
        chapter_match = re.search(chapter_pattern, line)
        if chapter_match:
            current_chapter = int(chapter_match.group(1))
            current_title = chapter_match.group(2).strip()

        # Check for scene start
        scene_match = re.search(r'SCENE\s+(\d+):', line)
        if scene_match and current_chapter:
            scene_num = int(scene_match.group(1))

            # Parse scene details from following lines
            scene_data = {
                'chapter_number': current_chapter,
                'chapter_title': current_title,
                'scene_number': scene_num,
                'setting': '',
                'characters': [],
                'pov_character': '',
                'goal': '',
                'conflict': '',
                'outcome': '',
                'word_count_target': 1000,
                'key_dialogue': ''
            }

            # Look ahead for scene details
            j = i + 1
            while j < len(lines) and j < i + 15:
                detail_line = lines[j].strip()

                if 'Setting:' in detail_line:
                    scene_data['setting'] = detail_line.split('Setting:')[-1].strip()
                elif 'Characters:' in detail_line:
                    chars = detail_line.split('Characters:')[-1].strip()
                    scene_data['characters'] = [c.strip() for c in chars.split(',')]
                elif 'POV:' in detail_line or 'POV Character:' in detail_line:
                    scene_data['pov_character'] = re.split(r'POV[^:]*:', detail_line)[-1].strip()
                elif 'Goal:' in detail_line:
                    scene_data['goal'] = detail_line.split('Goal:')[-1].strip()
                elif 'Conflict:' in detail_line:
                    scene_data['conflict'] = detail_line.split('Conflict:')[-1].strip()
                elif 'Outcome:' in detail_line:
                    scene_data['outcome'] = detail_line.split('Outcome:')[-1].strip()
                elif 'Word Count' in detail_line:
                    wc_match = re.search(r'(\d+)', detail_line)
                    if wc_match:
                        scene_data['word_count_target'] = int(wc_match.group(1))
                elif 'Key Dialogue:' in detail_line:
                    scene_data['key_dialogue'] = detail_line.split('Key Dialogue:')[-1].strip()

                # Stop if we hit another scene or chapter
                if re.search(r'SCENE\s+\d+:|CHAPTER\s+\d+', detail_line):
                    break

                j += 1

            # Use first character as POV if not specified
            if not scene_data['pov_character'] and scene_data['characters']:
                scene_data['pov_character'] = scene_data['characters'][0]

            scenes.append(scene_data)

        i += 1

    return scenes


def get_chapter_scenes(all_scenes: List[Dict], chapter_number: int) -> List[Dict]:
    """Get all scenes for a specific chapter."""
    return [s for s in all_scenes if s['chapter_number'] == chapter_number]


def create_scene_breakdown_task(
    agent: Agent,
    story_task: Task,
    chapter_outline: str,
    chapter_number: int,
    character_context: str = "",
    location_context: str = "",
    context_window: int = 40000
) -> Task:
    """
    Create a task to break a chapter into detailed scenes.

    This task takes a chapter outline and creates a detailed scene-by-scene
    breakdown that can be used for individual scene generation.
    """
    context_reminder = get_context_reminder(context_window)

    return Task(
        description=f"""# Scene Breakdown for Chapter {chapter_number}

{context_reminder}

## Chapter Outline
{chapter_outline}

{f"## Available Characters\n{character_context[:3000]}" if character_context else ""}

{f"## Available Locations\n{location_context[:2000]}" if location_context else ""}

## Your Task

Break this chapter into 3-7 individual scenes. Each scene should be a self-contained
unit that can be written independently while connecting to the overall chapter flow.

## Scene Structure Requirements

For EACH scene, provide:

```
═══════════════════════════════════════════════════════════════════
SCENE [NUMBER]: [Brief Title]
═══════════════════════════════════════════════════════════════════

SCENE TYPE: [SCENE or SEQUEL]
- SCENE = Goal → Conflict → Disaster/Success
- SEQUEL = Reaction → Dilemma → Decision

POV CHARACTER: [Name]
- Why this POV: [Brief reason]

SETTING:
- Location: [Specific place]
- Time: [Time of day, how much time passes]
- Atmosphere: [Mood, lighting, weather if relevant]

CHARACTERS PRESENT:
1. [Character Name] - [Their role in this scene]
2. [Character Name] - [Their role in this scene]
...

SCENE GOAL: [What the POV character wants to achieve]

CONFLICT/TENSION: [What opposes them or creates tension]

OUTCOME: [How the scene ends - success/failure/twist/complication]

EMOTIONAL BEAT: [The key emotional moment or shift]

KEY DIALOGUE POINTS:
- [Topic 1 that must be discussed]
- [Topic 2 that must be discussed]
...

PLOT ADVANCEMENT:
- [What moves forward in this scene]
- [Information revealed or withheld]

TRANSITION TO NEXT SCENE:
- [Hook or bridge to the next scene]

WORD COUNT TARGET: [800-1500 words]
═══════════════════════════════════════════════════════════════════
```

## Important Guidelines

1. **Scene vs Sequel**: Alternate between action scenes (external conflict) and sequel scenes (internal processing)

2. **POV Consistency**: Each scene should have ONE clear POV character

3. **Location Changes**: New location = new scene (usually)

4. **Pacing Variety**: Mix short punchy scenes with longer developing scenes

5. **Scene Flow**: Each scene should have a clear beginning, middle, and end

6. **Chapter Arc**: Together, scenes should form a complete chapter arc with:
   - Opening hook
   - Rising tension
   - Chapter climax
   - Closing hook (page-turner)

## Output Format

Provide detailed breakdowns for ALL scenes in this chapter.
Be thorough - these breakdowns will guide the actual writing.""",
        expected_output=f"""A complete scene breakdown for Chapter {chapter_number} containing:

1. 3-7 fully detailed scene breakdowns
2. Clear scene types (SCENE vs SEQUEL)
3. Specific POV characters for each scene
4. Detailed setting and atmosphere
5. Character roles and dialogue points
6. Clear goals, conflicts, and outcomes
7. Word count targets per scene
8. Smooth transitions between scenes

The breakdown should be detailed enough to write each scene independently.""",
        agent=agent,
        context=[story_task]
    )


def create_enhanced_scene_writing_task(
    agent: Agent,
    story_task: Task,
    scene_data: Dict[str, Any],
    chapter_context: str,
    previous_scene_content: str = "",
    next_scene_preview: str = "",
    character_profiles: str = "",
    location_details: str = "",
    context_window: int = 40000
) -> Task:
    """
    Create an enhanced task for writing a single scene with full context.

    This task provides maximum context to the scene writer including:
    - Previous scene content for continuity
    - Next scene preview for setup
    - Full character profiles for voice consistency
    - Location details for immersion
    """
    context_reminder = get_context_reminder(context_window)

    chapter_num = scene_data.get('chapter_number', 1)
    scene_num = scene_data.get('scene_number', 1)
    pov_char = scene_data.get('pov_character', 'protagonist')
    setting = scene_data.get('setting', 'unspecified location')
    characters = scene_data.get('characters', [])
    goal = scene_data.get('goal', '')
    conflict = scene_data.get('conflict', '')
    outcome = scene_data.get('outcome', '')
    word_target = scene_data.get('word_count_target', 1000)
    key_dialogue = scene_data.get('key_dialogue', '')

    # Build continuity section
    continuity = ""
    if previous_scene_content:
        # Get last 500 words of previous scene
        prev_words = previous_scene_content.split()
        if len(prev_words) > 150:
            prev_excerpt = ' '.join(prev_words[-150:])
            continuity += f"""
## PREVIOUS SCENE ENDING
(Continue seamlessly from this...)

...{prev_excerpt}

---
"""
        else:
            continuity += f"""
## PREVIOUS SCENE
{previous_scene_content}

---
"""

    if next_scene_preview:
        continuity += f"""
## NEXT SCENE PREVIEW
(This scene must set up...)
{next_scene_preview}

---
"""

    # Build character context
    char_section = ""
    if character_profiles:
        char_section = f"""
## CHARACTER PROFILES
(Use these for voice and behavior consistency)

{character_profiles[:4000]}
"""

    # Build location context
    loc_section = ""
    if location_details:
        loc_section = f"""
## LOCATION DETAILS
{location_details[:2000]}
"""

    return Task(
        description=f"""# Write Scene {scene_num} of Chapter {chapter_num}

{context_reminder}

{continuity}

## SCENE DETAILS
- **POV Character**: {pov_char}
- **Setting**: {setting}
- **Characters Present**: {', '.join(characters) if characters else pov_char}
- **Scene Goal**: {goal}
- **Conflict/Tension**: {conflict}
- **Scene Outcome**: {outcome}
{f"- **Key Dialogue Points**: {key_dialogue}" if key_dialogue else ""}

## CHAPTER CONTEXT
{chapter_context[:2000]}

{char_section}

{loc_section}

## WRITING REQUIREMENTS

### Word Count: {word_target} words (aim for {word_target - 200} to {word_target + 300})

### Strict POV Discipline
- Stay EXCLUSIVELY in {pov_char}'s point of view
- Only describe what {pov_char} can directly perceive
- Filter all observations through {pov_char}'s personality and knowledge
- Show {pov_char}'s internal thoughts and reactions
- Never reveal what other characters are thinking

### Scene Structure
Use SCENE-SEQUEL structure:
- **If action scene**: Goal → Conflict → Disaster/Success
- **If reaction scene**: Reaction → Dilemma → Decision

### Sensory Immersion
For this scene in {setting}, include:
- Visual details (lighting, colors, movement)
- Sounds (ambient and specific)
- Physical sensations
- Smells if relevant
- Atmosphere/mood

### Dialogue Excellence
- Each character speaks with their unique voice
- Use subtext - what's NOT said matters
- Include action beats between dialogue
- Dialogue reveals character or advances plot
- Avoid "said bookisms" - use action instead

### Pacing
- Match pacing to scene type (action = short sentences, emotional = longer)
- Vary sentence structure for rhythm
- Use paragraph breaks strategically

### Continuity
{"- Start seamlessly from where the previous scene ended" if previous_scene_content else "- Start with a hook that draws readers in"}
{"- Set up elements that will pay off in the next scene" if next_scene_preview else "- End with a hook that makes readers want to continue"}

## OUTPUT FORMAT

Write ONLY the scene prose. No headers, no notes, no meta-commentary.
Start directly with the scene and end at the natural scene conclusion.

Remember: You are writing {word_target} words of polished, publishable fiction.

---

[Begin scene...]""",
        expected_output=f"""A complete scene of approximately {word_target} words containing:

1. Strict {pov_char} POV throughout
2. Rich sensory details for {setting}
3. Clear scene structure (goal-conflict-outcome)
4. Distinct character voices in dialogue
5. Appropriate pacing for the scene type
6. {"Seamless continuation from previous scene" if previous_scene_content else "Strong opening hook"}
7. {"Setup for the following scene" if next_scene_preview else "Compelling scene ending"}

The scene should read as polished, publishable prose.""",
        agent=agent,
        context=[story_task]
    )
