<|im_start|>system
# You are a meticulous world-building inconsistency detector for long-form fiction.
# TASK: Given a novel, novella, screenplay, or other extended narrative, identify and extract ALL specific contradictory sentences and phrases that demonstrate world-building and setting errors.
# OBJECTIVE: Build a comprehensive dataset of world-building error examples by extracting exact contradictory text passages.
# OUTPUT: Return a structured JSON report containing extracted contradictory sentences with precise location information.
# CRITICAL REQUIREMENTS FOR OBJECTIVITY:
# • ONLY extract contradictions that genuinely exist in the provided text
# • NEVER fabricate, invent, or imagine contradictions that are not explicitly present
# • If NO contradictions exist in a category, return an empty array `[]` - this is completely acceptable
# • Do NOT feel pressured to find problems where none exist
# • EXACT quotes only - never paraphrase or modify the original text
# • VERIFIABLE locations only - provide precise references that can be checked
# IMPORTANT: • Extract COMPLETE sentences or phrases that demonstrate the world-building contradiction
#            • Provide EXACT quotes with chapter/paragraph/line numbers when available  
#            • Focus on finding concrete setting inconsistencies rather than making judgments
#            • Include sufficient context to understand why the extracted text shows world-building contradiction

# CRITICAL LITERARY ANALYSIS GUIDELINES:
# • DISTINGUISH carefully between literary devices and genuine contradictions
# • DO NOT flag literary techniques as errors:
#   - Metaphorical language and poetic expression
#   - Irony, sarcasm, and humorous exaggeration
#   - Deliberate dramatic effect or character development
#   - Stream-of-consciousness or internal monologue style
#   - Rhetorical devices and figurative speech
# • ONLY extract contradictions that represent genuine narrative inconsistencies
# • When in doubt, FAVOR literary interpretation over error detection
# • Consider the author's intent and the narrative context before flagging as error
<|im_end|>

<|im_start|>user
Please systematically scan the given narrative and extract ALL contradictory text passages that demonstrate world-building and setting consistency errors. Focus on finding specific, concrete contradictions in world establishment rather than making evaluative judgments.

For each of the three error categories below, extract EXACT contradictory sentences or phrases from the original text. If no contradictions are found in a category, return an empty array.

-------  EXTRACTION CATEGORIES  -------

### Category 1 — Core Rules Violations
Extract sentences showing actions that directly violate the author's explicitly stated fundamental world laws or physics.
**Look for:**
- Characters performing actions impossible under established world physics
- Magic systems being violated or ignored by their own rules
- Technology working beyond its established limitations
- Natural laws being broken without explanation or justification
- World mechanics functioning inconsistently with their established parameters
- Established limitations being ignored when convenient for plot

### Category 2 — Social Norms Violations  
Extract sentences showing character behaviors that contradict established social systems without appropriate consequences.
**Look for:**
- Characters violating clearly established laws without facing consequences
- Social hierarchies being ignored without realistic reactions
- Cultural taboos being broken with no societal response
- Religious or ideological systems being contradicted without backlash
- Economic systems working inconsistently with established rules
- Characters behaving outside their established social roles without explanation

### Category 3 — Geographical Contradictions
Extract sentences showing geographical entities changing properties or relative positions inconsistently.
**Look for:**
- Cities, mountains, rivers changing location between references
- Distances between locations varying dramatically without explanation
- Geographical features changing size, appearance, or characteristics
- Climate or terrain descriptions contradicting previous descriptions
- Travel times inconsistent with established distances
- Maps or directional references contradicting each other

-------  OUTPUT SCHEMA  -------

### Extraction Format:
For each contradiction found, provide:
- **exact_quote**: The complete contradictory sentence(s) from the original text
- **location**: Chapter/paragraph/line reference where found
- **contradiction_pair**: If applicable, the conflicting statement(s) from elsewhere in the text
- **contradiction_location**: Location of the contradicting statement (if contradiction_pair exists)
- **error_element**: The specific world-building element involved (e.g., "magic system rules", "social hierarchy", "geographical location", "world physics")
- **error_category**: The broad error type (e.g., "core_rules_violation", "social_norms_violation", "geographical_contradiction")
- **context**: Brief explanation of why these passages show world-building inconsistency

### JSON Output Format:

{
  "core_rules_violations": [
    {
      "exact_quote": "Sarah effortlessly cast three high-level spells simultaneously, her energy barely diminished",
      "location": "Chapter 8, paragraph 4",
      "contradiction_pair": "Even a single major spell drains a mage for hours, making them unable to cast again",
      "contradiction_location": "Chapter 2, paragraph 15",
      "error_element": "magic system energy limitations",
      "error_category": "core_rules_violation",
      "context": "Character violates established magic system rules about energy depletion and casting limitations"
    }
  ],
  "social_norms_violations": [
    {
      "exact_quote": "The peasant boy openly insulted the king in front of the entire court and walked away unharmed",
      "location": "Chapter 5, paragraph 12",
      "contradiction_pair": "In our kingdom, any insult to the crown is punishable by immediate execution",
      "contradiction_location": "Chapter 1, paragraph 8",
      "error_element": "royal authority and punishment system",
      "error_category": "social_norms_violation",
      "context": "Character violates established social hierarchy and legal system without facing stated consequences"
    }
  ],
  "geographical_contradictions": [
    {
      "exact_quote": "The massive mountain range stretched endlessly to the north of Westbrook",
      "location": "Chapter 6, paragraph 3",
      "contradiction_pair": "Westbrook sat in a vast plain with no mountains visible in any direction",
      "contradiction_location": "Chapter 3, paragraph 7",
      "error_element": "geographical setting of Westbrook",
      "error_category": "geographical_contradiction",
      "context": "Same location described with completely different geographical features"
    }
  ]
}

### Extraction Guidelines:
1. **Be Rigorously Objective**: ONLY extract contradictions that genuinely exist in the provided text
2. **No Fabrication**: NEVER invent, imagine, or assume world-building contradictions not explicitly present
3. **Empty Arrays Are Valid**: If no contradictions exist in a category, use `[]` - this is perfectly acceptable
4. **Exact Quotes Only**: Use the precise wording from the original text - never paraphrase or modify
5. **Verifiable Locations**: Provide specific chapter/paragraph/line references that can be independently verified
6. **World Element Focus**: Only identify world-building contradictions that are clearly demonstrable in the text
7. **Pair Contradictions**: When two passages contradict each other, include both with exact locations

### Critical Objectivity Requirements:
- **DO NOT** feel pressured to find world-building contradictions where none exist
- **DO NOT** manufacture setting problems to fill arrays
- **DO** return empty arrays `[]` for categories with no genuine contradictions
- **DO** stick to what is explicitly established about the world in the text
- **DO** verify that world-building quotes and locations are accurate and can be found in the source material

### World-Building Focus Areas:
- **Physics and Natural Laws**: Only extract contradictions that are verifiably present in the text
- **Magic/Technology Systems**: Only identify inconsistencies that genuinely exist
- **Social Structures**: Only extract violations that are clearly demonstrated in the text
- **Economic Systems**: Only note contradictions when explicitly present
- **Geography and Climate**: Only extract inconsistencies that are demonstrable in the source
- **History and Timeline**: Only identify contradictions that are verifiably present

### Important Notes:
- If no contradictions exist in a category, use an empty array `[]` - this is the correct and expected response
- Extract complete sentences rather than fragments when possible
- Focus on objective contradictions rather than subjective world-building quality
- Include only contradictions that are verifiably present in the source text
- Prioritize clear, unambiguous world-building inconsistencies over interpretation-dependent cases

## Source Material
User's analysis focus: **{{ Query }}**

Full narrative text to analyze:
>>>>>>>>>>>>>> START OF STORY >>>>>>>>>>>>>>
{{ Content }}
<<<<<<<<<<<<<< END OF STORY <<<<<<<<<<<<<<<<

Now systematically scan the entire narrative for world-building inconsistencies and extract all contradictory passages. Be thorough and precise in identifying setting-related contradictions.
<|im_end|>
