# Workflow Enhancements - Complete yWriter7 Field Integration

## Overview

The workflow has been completely redesigned to utilize ALL available yWriter7 fields for optimal story development. This ensures that the AI Book Writer takes full advantage of yWriter7's professional novel-writing structure.

## Enhanced Workflow Steps

### 1. Story Planning (Step 1)
**Agent**: Story Planner
**Output**: Comprehensive story arc with plot structure

No changes to this step - it remains the foundation for all subsequent work.

---

### 2. Character Creation with Full Profile Fields (Step 2)
**Agent**: Character Creator
**New yWriter7 Fields Utilized**:

#### Character Fields Now Populated:
- **title**: Character's primary name
- **fullName**: Complete formal name
- **aka**: Nicknames, alternate names, aliases (creative use for characters known by multiple names)
- **desc**: Brief character description
- **bio**: Detailed biography, background, personality traits
- **notes**: Character development notes, arc progression notes
- **goals**: What the character wants to achieve throughout the story
- **isMajor**: Boolean flag distinguishing major vs minor characters

#### Example Character Structure:
```python
character.title = "Elena"
character.fullName = "Elena Marie Thorne"
character.aka = "El, Dr. Thorne, The Professor"
character.desc = "A determined archaeologist seeking ancient truths"
character.bio = "Elena grew up in academic circles, daughter of two historians..."
character.notes = "Arc: From idealist to pragmatic realist. Learns to balance truth-seeking with protecting others."
character.goals = "Discover the truth about her mentor's death and protect the artifact from falling into wrong hands"
character.isMajor = True
```

#### Why This Matters:
- **aka** allows characters to be referred to by different names in different contexts (formal vs informal)
- **bio** vs **desc**: Short description for quick reference, detailed bio for deep character work
- **notes** tracks character development across the story
- **goals** ensures every character has clear motivation that Writer agent can reference
- **isMajor** helps agents prioritize character development and screen time

---

### 3. Location Creation with Alternate Names (Step 3)
**Agent**: Setting Builder
**New yWriter7 Fields Utilized**:

#### Location Fields Now Populated:
- **title**: Primary location name
- **aka**: Alternate names (historical names, colloquial names, nicknames)
- **desc**: Vivid description with atmosphere and mood

#### Example Location Structure:
```python
location.title = "The Ancient Temple"
location.aka = "Temple of the Ancients, The Forbidden Site, Lugar Sagrado"
location.desc = "A moss-covered stone structure hidden deep in the Amazon rainforest, shrouded in perpetual mist..."
```

#### Why This Matters:
- **aka** provides authentic alternate names (local language, historical, colloquial)
- Creates richer worldbuilding when locations have multiple cultural names
- Writer agent can use appropriate name based on POV character and context

---

### 4. Chapter Outlining (Step 4)
**Agent**: Outline Creator
**Fields Utilized**:

#### Chapter Fields:
- **title**: Chapter title
- **desc**: Summary of all scenes in the chapter (scene summaries at chapter level)
- **chLevel**: Chapter hierarchy (0 = normal chapter)
- **chType**: Chapter type (0 = normal)
- **srtScenes**: Ordered list of scene IDs

#### Why This Matters:
- **desc** provides chapter-level scene summaries as requested
- Allows readers/writers to quickly understand chapter contents without reading full scenes

---

### 5. Scene Structure Creation with Goal/Conflict/Outcome (Step 5) - NEW!
**Agent**: Outline Creator (reused for structure extraction)
**Scene Fields Now Populated**:

#### Core Scene Structure (Dwight Swain's Scene/Sequel Pattern):
- **goal**: What the POV character wants to accomplish in this scene
- **conflict**: Obstacles, opposition, tension preventing the goal
- **outcome**: How the scene resolves (usually failure or partial success leading to next scene)

#### Scene Classification:
- **isReactionScene**: Boolean distinguishing ACTION vs REACTION scenes
  - ACTION: Character pursues a goal (goal → conflict → outcome)
  - REACTION: Character processes consequences of previous scene (emotion → dilemma → decision)

#### Additional Scene Metadata:
- **scnMode**: Narrative mode (Dramatic action / Dialogue / Description / Exposition)
- **scnArcs**: Storylines the scene advances ("Main Plot;Character Arc;Subplot A")
- **notes**: Scene planning notes including POV character and location
- **tags**: Scene tags for organization (action, emotional, mystery, etc.)

#### Example Scene Structure:
```python
scene.title = "The Hidden Chamber"
scene.desc = "Elena must find the inner sanctum before Marcus seals the temple"

# Dwight Swain structure
scene.goal = "Elena must reach the inner chamber and retrieve the artifact before Marcus seals it"
scene.conflict = "Marcus has armed guards, a head start, and knows the temple layout. Traps activate as Elena pursues"
scene.outcome = "Elena finds a secret passage but Marcus triggers a cave-in trap. She gets through but is now trapped inside with Marcus"

# Scene classification
scene.isReactionScene = False  # This is an ACTION scene (pursuit of goal)
scene.scnMode = "Dramatic action"
scene.scnArcs = "Main Plot;Elena's Character Arc"

# Metadata
scene.notes = "POV: Elena Thorne\nLocation: The Ancient Temple - Inner Sanctum"
scene.tags = "high-stakes;action;midpoint"
```

#### Why This Matters:
- **goal/conflict/outcome** ensures every scene has clear structure and purpose
- **isReactionScene** enforces proper Action/Reaction alternation (prevents too many action scenes in a row)
- **scnMode** helps Writer agent choose appropriate narrative technique
- **scnArcs** tracks which storylines advance in each scene (prevents dropped plot threads)
- **notes** and **tags** provide quick reference for planning and organization

---

### 6. Prose Writing (Step 6) - NEW!
**Agent**: Writer
**Process**: Generates actual prose for each scene based on structure

#### What the Writer Agent Does:
1. Reads scene.goal, scene.conflict, scene.outcome
2. Checks scene.isReactionScene to determine scene type
3. Uses scene.scnMode to choose narrative approach
4. References scene.notes for POV character and location
5. Uses RAG tools to verify character details, location descriptions, and continuity
6. Writes 800-1200 words of polished prose
7. Populates scene.sceneContent with the generated prose

#### Input Example:
```
Title: The Hidden Chamber
Goal: Elena must reach the inner chamber and retrieve the artifact
Conflict: Marcus has guards and knows the layout. Traps activate.
Outcome: Elena finds a secret passage but gets trapped inside with Marcus
Type: ACTION scene
Mode: Dramatic action
POV: Elena Thorne
Location: The Ancient Temple
```

#### Output:
Full prose scene (800-1200 words) that dramatizes the goal pursuit, conflict, and outcome with vivid details and compelling dialogue.

#### Current Implementation Note:
- Limited to first 3 scenes for testing (configurable via `max_scenes_to_write`)
- Can be expanded to write full novel in production

---

### 7. Editorial Refinement (Step 7) - NEW!
**Agent**: Editor
**Process**: Refines generated prose for quality

#### What the Editor Agent Does:
1. Reviews scene.sceneContent (the prose)
2. Improves clarity, flow, and pacing
3. Refines dialogue naturalness
4. Enhances sensory details
5. Corrects grammar and style issues
6. Maintains character voice consistency
7. Updates scene.sceneContent with refined version

#### Currently Limited:
- Edits only the scenes that were written (first 3 by default)
- Skips placeholder scenes

---

## Complete Workflow Summary

```
1. Story Planner
   ↓ (story arc with themes, plot points, character arcs)

2. Character Creator
   ↓ (characters with title, fullName, aka, desc, bio, notes, goals, isMajor)

3. Setting Builder
   ↓ (locations with title, aka, desc)

4. Outline Creator
   ↓ (chapter outlines with chapter.desc summaries)

5. Scene Structure Builder (NEW!)
   ↓ (scenes with goal/conflict/outcome, isReactionScene, scnMode, scnArcs, notes, tags)

6. Writer (NEW!)
   ↓ (actual prose in scene.sceneContent using RAG for continuity)

7. Editor (NEW!)
   ↓ (refined, polished prose)

8. Final Output
   → Complete yWriter7 file with all fields populated
   → Automatic RAG sync for semantic search
```

---

## yWriter7 Fields Now Being Used

### Character Fields (11/23 total fields):
✅ title, fullName, aka, desc, bio, notes, goals, isMajor

### Location Fields (3/5 total fields):
✅ title, aka, desc

### Scene Fields (11/40+ total fields):
✅ title, desc, goal, conflict, outcome, isReactionScene, scnMode, scnArcs, notes, tags, sceneContent

### Chapter Fields (3/8 total fields):
✅ title, desc, chLevel, chType, srtScenes

---

## Key Benefits

1. **Professional Structure**: Uses yWriter7's Dwight Swain scene structure (goal/conflict/outcome)
2. **Action/Reaction Balance**: Tracks scene types to ensure proper pacing
3. **Character Depth**: Full profiles with bios, goals, nicknames
4. **Worldbuilding**: Location alternate names add authenticity
5. **Storyline Tracking**: scnArcs prevents dropped plot threads
6. **Continuity**: RAG integration during writing ensures consistency
7. **Chapter Summaries**: Quick reference via chapter.desc
8. **Actual Prose**: No more placeholder text - generates real content

---

## Testing Limitations

For initial testing and development, the workflow implements:
- **First 2 chapters only** for scene structure
- **First 3 scenes only** for prose writing
- **First 3 scenes only** for editorial refinement

These limits can be removed for production use by modifying:
```python
max_scenes_to_write = 3  # Increase or remove limit
for ch_id in yw7.novel.srtChapters[:2]:  # Remove [:2] to process all chapters
```

---

## Future Enhancements

Additional yWriter7 fields that could be utilized:
- **scene.date/time**: Timeline tracking
- **scene.lastsMinutes/Hours/Days**: Scene duration
- **scene.items**: Objects present in scene
- **scene.field1-4**: Custom ratings (tension, pacing, emotion, action)
- **character.tags**: Character categorization
- **location.tags**: Location categorization
- **novel.wordTarget**: Word count goals
- **novel.authorBio**: Author information

These can be added in future iterations based on user needs.

---

## Conclusion

The workflow now properly utilizes yWriter7's professional novel-writing structure, ensuring that every field serves a purpose in creating well-structured, consistent, and compelling narratives. The integration of goal/conflict/outcome scene structure, character goals, alternate names, and chapter summaries addresses all identified gaps in the previous workflow.
