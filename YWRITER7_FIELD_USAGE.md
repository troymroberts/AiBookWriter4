# yWriter7 Field Usage Analysis

## Summary
This document identifies which yWriter7 fields we're currently using and which ones we should leverage for better storytelling.

---

## 🎬 Scene Fields

### ✅ Currently Using
- **title** - Scene title
- **desc** - Scene description
- **sceneContent** - The actual prose
- **characters** - Character IDs in scene
- **locations** - Location IDs in scene
- **status** - Scene status (Outline/Draft/etc.)

### ❌ NOT Using (But Should!)

#### **Critical for Storytelling Structure:**
- **goal** ⭐ - What the POV character wants to accomplish in this scene
- **conflict** ⭐ - What prevents them from achieving the goal
- **outcome** ⭐ - The result and how it leads to the next scene

#### **Scene Type & Pacing:**
- **isReactionScene** - Action vs Reaction scenes (essential for pacing!)
  - Action scenes: character pursues goal
  - Reaction scenes: character processes/responds to previous action
- **isSubPlot** - Main plot vs subplot flag
- **scnArcs** - Arc/storyline tags (e.g., "Romance;Mystery;Character Growth")
- **scnMode** - Mode of discourse:
  - Narration
  - Dramatic action
  - Dialogue
  - Description
  - Exposition

#### **Scene Management:**
- **notes** - Planning notes, reminders for revision
- **tags** - Scene tags (e.g., "high-tension", "romantic", "climax")
- **appendToPrev** - Join to previous scene without chapter break
- **items** - Item/object IDs relevant to scene (MacGuffins, weapons, etc.)

#### **Timeline & Duration:**
- **date** - Specific date (yyyy-mm-dd)
- **time** - Specific time (hh:mm:ss)
- **day/hour/minute** - Relative time markers
- **lastsDays/lastsHours/lastsMinutes** - Scene duration

#### **Custom Rating Fields:**
- **field1-4** - Could track:
  - Tension level (1-5)
  - Pacing (slow/medium/fast)
  - Emotional intensity
  - Importance to plot

#### **Other:**
- **image** - Image file path for visual reference
- **scType** - Normal/Notes/Todo/Unused
- **doNotExport** - Exclude from export

---

## 📚 Chapter Fields

### ✅ Currently Using
- **title** - Chapter title
- **desc** - Chapter description
- **chLevel** - Chapter level (0=chapter, 1=section/part)
- **chType** - Chapter type (Normal/Notes/Todo/Unused)
- **srtScenes** - Ordered list of scene IDs

### ❌ NOT Using
- **suppressChapterTitle** - Hide chapter heading in export
- **suppressChapterBreak** - Remove chapter break when exporting
- **isTrash** - Mark as trash bin

---

## 👤 Character Fields

### ✅ Currently Using
- **title** - Character name
- **desc** - Character description
- **fullName** - Full name
- **bio** - Biography
- **notes** - Character notes

### ❌ NOT Using
- **goals** - Character's overall story goals
- **isMajor** - Major vs minor character flag
- **aka** - Also known as / nickname (from WorldElement)
- **tags** - Character tags (from WorldElement)

---

## 📍 Location Fields

### ✅ Currently Using
- **title** - Location name
- **desc** - Location description
- **aka** - Alternate name

### ❌ NOT Using
- **tags** - Location tags
- Additional metadata from WorldElement

---

## 🎯 Recommendations

### High Priority (Implement First)
1. **Scene goal/conflict/outcome** - Essential for tight scene structure
2. **isReactionScene** - Critical for pacing (Dwight Swain's Scene/Sequel structure)
3. **scnArcs** - Track multiple storylines
4. **character.isMajor** - Distinguish major/minor characters
5. **character.goals** - Overall character arc goals

### Medium Priority
6. **scnMode** - Track narrative mode for variety
7. **scene.notes** - Planning/revision notes
8. **scene.tags** - Scene categorization
9. **scene.items** - Track important objects
10. **field1-4** - Custom metrics (tension, pacing, etc.)

### Low Priority (Nice to Have)
11. **Timeline fields** - For complex chronologies
12. **scene.image** - Visual references
13. **suppressChapterTitle/Break** - Export formatting

---

## 🔧 Implementation Plan

### Phase 1: Scene Structure (Critical)
```python
scene.goal = "What character wants to achieve"
scene.conflict = "What prevents them"
scene.outcome = "Result that leads to next scene"
scene.isReactionScene = False  # or True
scene.scnArcs = "Main Plot;Romance Subplot"
```

### Phase 2: Character Enhancement
```python
character.goals = "Overall character arc goal"
character.isMajor = True  # for protagonist/antagonist
```

### Phase 3: Advanced Features
```python
scene.scnMode = "Dramatic action"
scene.tags = ["high-tension", "climax"]
scene.field1 = 5  # Tension rating
scene.field2 = 4  # Pacing
scene.items = [magic_sword_id, ring_id]
```

---

## 📝 Example: Well-Structured Scene

```python
scene = Scene()
scene.title = "Confrontation at the Temple"
scene.desc = "Elena faces Marcus at the ancient temple entrance"

# Critical structure
scene.goal = "Elena must reach the inner chamber before Marcus seals it"
scene.conflict = "Marcus has armed guards and a head start"
scene.outcome = "Elena finds a secret passage but Marcus triggers a trap"

# Metadata
scene.isReactionScene = False  # This is an ACTION scene
scene.scnArcs = "Main Plot;Elena's Arc"
scene.scnMode = "Dramatic action"
scene.tags = ["high-stakes", "action", "midpoint"]

# Characters/Locations
scene.characters = [elena_id, marcus_id, guard_id]
scene.locations = [temple_entrance_id]
scene.items = [map_id, amulet_id]

# Ratings
scene.field1 = 5  # Tension: Very High
scene.field2 = 5  # Pacing: Very Fast
scene.field3 = 4  # Emotional Impact: High
scene.field4 = 5  # Plot Importance: Critical

# Timeline
scene.date = "2024-06-15"
scene.time = "14:30:00"
scene.lastsMinutes = "15"

# Content
scene.sceneContent = "Elena's heart pounded as she..."
scene.status = 2  # Draft
```

---

## 🎭 Scene/Sequel Pattern (Dwight Swain)

**Action Scene:**
```python
scene.isReactionScene = False
scene.goal = "Protagonist's immediate objective"
scene.conflict = "Opposition/obstacle"
scene.outcome = "Disaster/setback or qualified victory"
```

**Reaction Scene (Sequel):**
```python
scene.isReactionScene = True
scene.goal = "Process the previous disaster and make decision"
scene.conflict = "Internal conflict, limited options"
scene.outcome = "Decision that launches next action scene"
```

This creates the rhythm:
**Goal → Conflict → Disaster → Reaction → Dilemma → Decision → Goal**

---

## Notes

- yWriter7 XML spec: All fields map to `<FieldName>value</FieldName>` in XML
- Boolean fields use `-1` for True in XML
- The goal/conflict/outcome pattern is **yWriter7's native scene structure**
- We should use these fields to guide LLM generation, not just store output
