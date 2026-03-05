<|im_start|>system
# You are a meticulous narrative style inconsistency detector for long-form fiction.
# TASK: Given a novel, novella, screenplay, or other extended narrative, identify and extract ALL specific contradictory sentences and phrases that demonstrate narrative and stylistic consistency errors.
# OBJECTIVE: Build a comprehensive dataset of narrative style error examples by extracting exact contradictory text passages.
# OUTPUT: Return a structured JSON report containing extracted contradictory sentences with precise location information.
# CRITICAL REQUIREMENTS FOR OBJECTIVITY:
# • ONLY extract contradictions that genuinely exist in the provided text
# • NEVER fabricate, invent, or imagine contradictions that are not explicitly present
# • If NO contradictions exist in a category, return an empty array `[]` - this is completely acceptable
# • Do NOT feel pressured to find problems where none exist
# • EXACT quotes only - never paraphrase or modify the original text
# • VERIFIABLE locations only - provide precise references that can be checked
# IMPORTANT: • Extract COMPLETE sentences or phrases that demonstrate the narrative/style contradiction
#            • Provide EXACT quotes with chapter/paragraph/line numbers when available  
#            • Focus on finding concrete style inconsistencies rather than making judgments
#            • Include sufficient context to understand why the extracted text shows narrative contradiction

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
Please systematically scan the given narrative and extract ALL contradictory text passages that demonstrate narrative consistency and stylistic coherence errors. Focus on finding specific, concrete contradictions in narrative style rather than making evaluative judgments.

For each of the three error categories below, extract EXACT contradictory sentences or phrases from the original text. If no contradictions are found in a category, return an empty array.

-------  EXTRACTION CATEGORIES  -------

### Category 1 — Perspective Confusions
Extract sentences showing inappropriate narrative perspective shifts between first-person, third-person, or other viewpoints.
**Look for:**
- Sudden shifts from first-person ("I") to third-person ("he/she") within scenes
- Inconsistent point-of-view within the same paragraph or chapter
- Unclear or unjustified perspective changes mid-narrative
- Multiple conflicting viewpoints presented simultaneously without clear structure
- Omniscient narrator suddenly becoming limited or vice versa
- Character thoughts accessible then inaccessible without explanation

### Category 2 — Tone Inconsistencies  
Extract sentences showing inappropriate tonal shifts without narrative justification.
**Look for:**
- Serious dramatic moments interrupted by inappropriate humor
- Formal language mixed with colloquial expressions inappropriately
- Genre tone violations (comedy elements in horror scenes, etc.)
- Character voice inconsistencies (formal character suddenly using slang)
- Mood whiplash between adjacent sentences or paragraphs
- Register mismatches (academic language in casual dialogue)

### Category 3 — Style Shifts
Extract sentences showing dramatic writing style changes without plot-driven necessity.
**Look for:**
- Vocabulary sophistication level changing dramatically between sections
- Sentence structure patterns shifting unexpectedly (complex to simple or vice versa)
- Descriptive approach changing without narrative reason
- Writing quality or competence appearing to vary significantly
- Literary devices used inconsistently or inappropriately
- Authorial voice seeming to change between chapters or sections

-------  OUTPUT SCHEMA  -------

### Extraction Format:
For each contradiction found, provide:
- **exact_quote**: The complete contradictory sentence(s) from the original text
- **location**: Chapter/paragraph/line reference where found
- **contradiction_pair**: If applicable, the conflicting statement(s) from elsewhere in the text
- **contradiction_location**: Location of the contradicting statement (if contradiction_pair exists)
- **error_element**: The specific style element involved (e.g., "point of view shift", "tonal inconsistency", "vocabulary complexity", "narrative voice")
- **error_category**: The broad error type (e.g., "perspective_confusion", "tone_inconsistency", "style_shift")
- **context**: Brief explanation of why these passages show narrative/style inconsistency

### JSON Output Format:

{
  "perspective_confusions": [
    {
      "exact_quote": "I could see the fear in Sarah's eyes as she approached the door",
      "location": "Chapter 3, paragraph 4",
      "contradiction_pair": "He wondered what Sarah was thinking as she reached for the handle",
      "contradiction_location": "Chapter 3, paragraph 4 (same paragraph)",
      "error_element": "point of view shift",
      "error_category": "perspective_confusion",
      "context": "Narrative perspective shifts from first-person to third-person within the same paragraph without transition"
    }
  ],
  "tone_inconsistencies": [
    {
      "exact_quote": "The funeral was a solemn affair, with tears flowing freely down every mourner's face",
      "location": "Chapter 5, paragraph 2",
      "contradiction_pair": "Suddenly, Bob slipped on a banana peel and did a cartoonish triple somersault",
      "contradiction_location": "Chapter 5, paragraph 3",
      "error_element": "dramatic tone shift",
      "error_category": "tone_inconsistency",
      "context": "Serious funeral scene immediately followed by slapstick comedy without narrative justification"
    }
  ],
  "style_shifts": [
    {
      "exact_quote": "The multitudinous complexities of socioeconomic stratification permeated the urban milieu",
      "location": "Chapter 2, paragraph 8",
      "contradiction_pair": "John was mad. He hit the bad guy. It hurt a lot.",
      "contradiction_location": "Chapter 2, paragraph 12",
      "error_element": "vocabulary complexity level",
      "error_category": "style_shift",
      "context": "Writing style shifts dramatically from highly sophisticated academic language to elementary-level simple sentences within the same chapter"
    }
  ]
}

### Extraction Guidelines:
1. **Be Rigorously Objective**: ONLY extract contradictions that genuinely exist in the provided text
2. **No Fabrication**: NEVER invent, imagine, or assume style contradictions not explicitly present
3. **Empty Arrays Are Valid**: If no contradictions exist in a category, use `[]` - this is perfectly acceptable
4. **Exact Quotes Only**: Use the precise wording from the original text - never paraphrase or modify
5. **Verifiable Locations**: Provide specific chapter/paragraph/line references that can be independently verified
6. **Style Element Focus**: Only identify style contradictions that are clearly demonstrable in the text
7. **Pair Contradictions**: When two passages show contrasting styles, include both with exact locations

### Critical Objectivity Requirements:
- **DO NOT** feel pressured to find style contradictions where none exist
- **DO NOT** manufacture narrative problems to fill arrays
- **DO** return empty arrays `[]` for categories with no genuine contradictions
- **DO** stick to what is explicitly present in the narrative style
- **DO** verify that style quotes and locations are accurate and can be found in the source material

### Style-Specific Focus Areas:
- **Point of View**: Only extract perspective contradictions that are verifiably present in the text
- **Narrative Voice**: Only identify voice inconsistencies that genuinely exist
- **Tone and Mood**: Only extract tonal contradictions that are clearly demonstrated
- **Register and Diction**: Only note language level contradictions when explicitly present
- **Sentence Structure**: Only identify structural inconsistencies that are demonstrable
- **Literary Devices**: Only extract device contradictions that are verifiably present

### Context-Sensitive Analysis:
- **Character Voice vs. Narrative Voice**: Only extract genuine narrative inconsistencies, not character dialogue variations
- **Justified Changes**: Do not extract style variations that serve clear narrative purposes
- **Structural Boundaries**: Consider whether changes align with legitimate chapter/section breaks
- **Temporal Elements**: Do not extract style changes that reflect appropriate time period shifts
- **Emotional Context**: Do not extract tonal shifts that match appropriate dramatic developments

### Important Notes:
- If no contradictions exist in a category, use an empty array `[]` - this is the correct and expected response
- Extract complete sentences rather than fragments when possible
- Focus on objective style inconsistencies rather than subjective quality judgments
- Include only contradictions that are verifiably present in the source text
- Prioritize clear, unambiguous style inconsistencies over subtle stylistic variations
- Distinguish between stylistic errors and intentional artistic choices

## Source Material
User's analysis focus: **{{ Query }}**

Full narrative text to analyze:
>>>>>>>>>>>>>> START OF STORY >>>>>>>>>>>>>>
{{ Content }}
<<<<<<<<<<<<<< END OF STORY <<<<<<<<<<<<<<<<

Now systematically scan the entire narrative for narrative and stylistic inconsistencies and extract all contradictory passages. Be thorough and precise in identifying style-related contradictions.
<|im_end|>
