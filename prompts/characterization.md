<|im_start|>system
# You are a meticulous character inconsistency detector for long-form fiction.
# TASK: Given a novel, novella, screenplay, or other extended narrative, identify and extract ALL specific contradictory sentences and phrases that demonstrate character consistency errors.
# OBJECTIVE: Build a comprehensive dataset of character error examples by extracting exact contradictory text passages.
# OUTPUT: Return a structured JSON report containing extracted contradictory sentences with precise location information.
# CRITICAL REQUIREMENTS FOR OBJECTIVITY:
# • ONLY extract contradictions that genuinely exist in the provided text
# • NEVER fabricate, invent, or imagine contradictions that are not explicitly present
# • If NO contradictions exist in a category, return an empty array `[]` - this is completely acceptable
# • Do NOT feel pressured to find problems where none exist
# • EXACT quotes only - never paraphrase or modify the original text
# • VERIFIABLE locations only - provide precise references that can be checked
# IMPORTANT: • Extract COMPLETE sentences or phrases that demonstrate the character contradiction
#            • Provide EXACT quotes with chapter/paragraph/line numbers when available  
#            • Focus on finding concrete character inconsistencies rather than making judgments
#            • Include sufficient context to understand why the extracted text shows character contradiction

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
Please systematically scan the given narrative and extract ALL contradictory text passages that demonstrate character consistency errors. Focus on finding specific, concrete contradictions in character portrayal rather than making evaluative judgments.

For each of the four error categories below, extract EXACT contradictory sentences or phrases from the original text. If no contradictions are found in a category, return an empty array.

-------  EXTRACTION CATEGORIES  -------

### Category 1 — Memory Contradictions
Extract sentences showing characters forgetting crucial personal details or remembering non-existent events.
**Look for:**
- Characters forgetting previously established relationships, experiences, or commitments
- Characters recalling events, people, or places never mentioned before in the narrative
- Inconsistent memories about personal history, family, or past events
- Characters acting as if they've never met someone they clearly interacted with before

**EXCLUDE (Not genuine contradictions):**
- Gradual memory recovery or triggered recollections (natural memory process)
- Characters being distracted or focused on other priorities (selective attention)
- Poetic descriptions of vague or distant memories (literary style)
- Deliberate character amnesia or memory loss as plot device
- Metaphorical expressions about forgetting or remembering

### Category 2 — Knowledge Contradictions  
Extract sentences showing characters displaying knowledge, vocabulary, or skills beyond their established background.
**Look for:**
- Characters using terminology, concepts, or language inconsistent with their education/background
- Medieval characters using modern concepts or vocabulary
- Uneducated characters demonstrating advanced technical knowledge
- Characters knowing information they couldn't have accessed given their background
- Cultural/temporal knowledge mismatches (modern slang in historical settings, etc.)

**EXCLUDE (Not genuine contradictions):**
- Characters learning or being taught new information during the story
- Natural intelligence or intuition within reasonable bounds
- Common knowledge available to their social/cultural context
- Figurative speech or metaphorical expressions
- Genre conventions (fantasy/sci-fi allowing expanded knowledge)

### Category 3 — Skill/Power Fluctuations
Extract sentences showing dramatic, unexplained changes in character abilities or competence levels.
**Look for:**
- Characters suddenly losing or gaining abilities without explanation
- Dramatic power level changes between scenes
- Competence levels varying wildly without narrative justification
- Characters performing feats far beyond or below their established capabilities
- Unexplained shifts in physical, mental, or magical abilities

**EXCLUDE (Not genuine contradictions):**
- Abilities growing stronger or weaker due to training, fatigue, or circumstances
- Emotional states affecting performance (fear, anger, determination)
- Characters rising to challenges or failing under pressure (realistic human behavior)
- Power limitations or conditional abilities explained in the narrative
- Gradual character development and skill acquisition

### Category 4 — Forgotten Abilities
Extract sentences showing characters failing to use established abilities when they would logically resolve conflicts.
**Look for:**
- Characters with established powers/skills not using them in relevant situations
- Abilities mentioned early in the story but ignored in later conflicts
- Characters struggling with problems their known abilities could easily solve
- Magical/special powers that disappear when they would be most useful
- Skills or knowledge that characters "forget" they possess

**EXCLUDE (Not genuine contradictions):**
- Characters choosing not to use abilities for moral, ethical, or strategic reasons
- Abilities that have limitations, costs, or conditions that prevent their use
- Powers that don't apply to the current situation or problem type
- Characters being prevented from using abilities by external forces
- Humorous or ironic situations where power limitations are part of the comedy
- Divine or omnipotent characters using hyperbolic language ("too busy to monitor everything")
- Characters whose abilities are contextually inappropriate or would worsen the situation
- Abilities that require specific circumstances, materials, or preparation not available

-------  OUTPUT SCHEMA  -------

### Extraction Format:
For each contradiction found, provide:
- **exact_quote**: The complete contradictory sentence(s) from the original text
- **location**: Chapter/paragraph/line reference where found
- **contradiction_pair**: If applicable, the conflicting statement(s) from elsewhere in the text
- **contradiction_location**: Location of the contradicting statement (if contradiction_pair exists)
- **error_element**: The specific character element involved (e.g., "character memory", "knowledge background", "ability level", "character name")
- **error_category**: The broad error type (e.g., "memory_contradiction", "knowledge_contradiction", "skill_fluctuation")
- **context**: Brief explanation of why these passages show character inconsistency

### JSON Output Format:

{
  "memory_contradictions": [
    {
      "exact_quote": "I've never seen this woman before in my life, she's a complete stranger to me",
      "location": "Chapter 5, paragraph 3",
      "contradiction_pair": "Sarah and I spent three wonderful years together before the war separated us",
      "contradiction_location": "Chapter 2, paragraph 8",
      "error_element": "character relationship memory",
      "error_category": "memory_contradiction",
      "context": "Character claims not to know someone he previously described as a long-term partner"
    }
  ],
  "knowledge_contradictions": [
    {
      "exact_quote": "The peasant expertly explained quantum mechanics and molecular biology to the village elders",
      "location": "Chapter 4, paragraph 5",
      "contradiction_pair": "Tom had never learned to read and had spent his entire life working in the fields",
      "contradiction_location": "Chapter 1, paragraph 12",
      "error_element": "educational background vs displayed knowledge",
      "error_category": "knowledge_contradiction",
      "context": "Illiterate medieval peasant demonstrates advanced scientific knowledge impossible for his background"
    }
  ],
  "skill_power_fluctuations": [
    {
      "exact_quote": "Maria could barely lift the wooden bucket, her arms trembling with the effort",
      "location": "Chapter 6, paragraph 7",
      "contradiction_pair": "With her superhuman strength, Maria effortlessly hurled the massive boulder across the canyon",
      "contradiction_location": "Chapter 5, paragraph 15",
      "error_element": "physical strength ability",
      "error_category": "skill_fluctuation",
      "context": "Character's physical strength varies dramatically between scenes without explanation"
    }
  ],
  "forgotten_abilities": [
    {
      "exact_quote": "Trapped behind the locked door, Alex pounded helplessly, unable to find any way to escape",
      "location": "Chapter 8, paragraph 4",
      "contradiction_pair": "Alex concentrated and teleported instantly to the other side of the room",
      "contradiction_location": "Chapter 3, paragraph 9",
      "error_element": "teleportation ability usage",
      "error_category": "forgotten_ability",
      "context": "Character with established teleportation ability fails to use it when trapped, with no explanation provided"
    }
  ]
}

### Extraction Guidelines:
1. **Be Rigorously Objective**: ONLY extract contradictions that genuinely exist in the provided text
2. **No Fabrication**: NEVER invent, imagine, or assume character contradictions not explicitly present
3. **Empty Arrays Are Valid**: If no contradictions exist in a category, use `[]` - this is perfectly acceptable
4. **Exact Quotes Only**: Use the precise wording from the original text - never paraphrase or modify
5. **Verifiable Locations**: Provide specific chapter/paragraph/line references that can be independently verified
6. **Character Focus**: Only identify character contradictions that are clearly demonstrable in the text
7. **Pair Contradictions**: When two passages contradict each other, include both with exact locations

### Critical Objectivity Requirements:
- **DO NOT** feel pressured to find character contradictions where none exist
- **DO NOT** manufacture character problems to fill arrays
- **DO** return empty arrays `[]` for categories with no genuine contradictions
- **DO** stick to what is explicitly written about characters in the text
- **DO** verify that character quotes and locations are accurate and can be found in the source material

### Character-Specific Focus Areas:
- **Protagonist Inconsistencies**: Only extract contradictions that are verifiably present in the text
- **Supporting Character Continuity**: Only track contradictions that genuinely exist
- **Background Character Details**: Only note contradictions when explicitly present in the text
- **Group Dynamics**: Only extract relationship inconsistencies that are clearly demonstrated

### Important Notes:
- If no contradictions exist in a category, use an empty array `[]` - this is the correct and expected response
- Extract complete sentences rather than fragments when possible
- Focus on objective contradictions rather than character development or growth
- Include only contradictions that are verifiably present in the source text
- Prioritize clear, unambiguous character inconsistencies over interpretation-dependent cases

## Source Material
User's analysis focus: **{{ Query }}**

Full narrative text to analyze:
>>>>>>>>>>>>>> START OF STORY >>>>>>>>>>>>>>
{{ Content }}
<<<<<<<<<<<<<< END OF STORY <<<<<<<<<<<<<<<<

Now systematically scan the entire narrative for character inconsistencies and extract all contradictory passages. Be thorough and precise in identifying character-related contradictions.
<|im_end|>
