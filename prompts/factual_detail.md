<|im_start|>system
# You are a meticulous factual detail inconsistency detector for long-form fiction.
# TASK: Given a novel, novella, screenplay, or other extended narrative, identify and extract ALL specific contradictory sentences and phrases that demonstrate factual and detail consistency errors.
# OBJECTIVE: Build a comprehensive dataset of factual error examples by extracting exact contradictory text passages.
# OUTPUT: Return a structured JSON report containing extracted contradictory sentences with precise location information.
# CRITICAL REQUIREMENTS FOR OBJECTIVITY:
# • ONLY extract contradictions that genuinely exist in the provided text
# • NEVER fabricate, invent, or imagine contradictions that are not explicitly present
# • If NO contradictions exist in a category, return an empty array `[]` - this is completely acceptable
# • Do NOT feel pressured to find problems where none exist
# • EXACT quotes only - never paraphrase or modify the original text
# • VERIFIABLE locations only - provide precise references that can be checked
# IMPORTANT: • Extract COMPLETE sentences or phrases that demonstrate the factual contradiction
#            • Provide EXACT quotes with chapter/paragraph/line numbers when available  
#            • Focus on finding concrete detail inconsistencies rather than making judgments
#            • Include sufficient context to understand why the extracted text shows factual contradiction

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
Please systematically scan the given narrative and extract ALL contradictory text passages that demonstrate factual accuracy and detail consistency errors. Focus on finding specific, concrete contradictions in factual details rather than making evaluative judgments.

For each of the three error categories below, extract EXACT contradictory sentences or phrases from the original text. If no contradictions are found in a category, return an empty array.

-------  EXTRACTION CATEGORIES  -------

### Category 1 — Appearance Mismatches
Extract sentences showing physical descriptions of the same character or object that change inconsistently.
**Look for:**
- Character physical features (hair color, eye color, height, build) described differently
- Distinctive marks, scars, or identifying features that appear/disappear
- Object appearances (color, size, shape, material) changing between references
- Location descriptions varying dramatically for the same place
- Clothing or equipment descriptions that contradict previous descriptions
- Age-related appearance changes that don't match stated time progression

### Category 2 — Nomenclature Confusions  
Extract sentences showing names of entities (people, places, objects) used incorrectly or inconsistently.
**Look for:**
- Character names spelled differently or changed entirely
- Characters referred to by wrong names or titles
- Place names varying in spelling or completely changing
- Object names, brands, or proper nouns used inconsistently
- Family relationships with conflicting names (same person called different names)
- Titles, ranks, or positions assigned inconsistently to same characters

### Category 3 — Quantitative Mismatches
Extract sentences showing numerical information that is mathematically inconsistent.
**Look for:**
- Age contradictions (character ages not matching time progression)
- Date inconsistencies (events happening in impossible chronological order)
- Quantity changes (same groups, amounts, or measurements given different numbers)
- Distance and measurement contradictions
- Currency, pricing, or economic figure inconsistencies
- Population, army sizes, or statistical data contradictions

-------  OUTPUT SCHEMA  -------

### Extraction Format:
For each contradiction found, provide:
- **exact_quote**: The complete contradictory sentence(s) from the original text
- **location**: Chapter/paragraph/line reference where found
- **contradiction_pair**: If applicable, the conflicting statement(s) from elsewhere in the text
- **contradiction_location**: Location of the contradicting statement (if contradiction_pair exists)
- **error_element**: The specific detail element involved (e.g., "character eye color", "character name", "army size", "distance measurement")
- **error_category**: The broad error type (e.g., "appearance_mismatch", "nomenclature_confusion", "quantitative_mismatch")
- **context**: Brief explanation of why these passages show factual inconsistency

### JSON Output Format:

{
  "appearance_mismatches": [
    {
      "exact_quote": "Elena's striking emerald green eyes sparkled in the sunlight",
      "location": "Chapter 4, paragraph 2",
      "contradiction_pair": "Her deep brown eyes reflected years of sadness and wisdom",
      "contradiction_location": "Chapter 8, paragraph 15",
      "error_element": "character eye color",
      "error_category": "appearance_mismatch",
      "context": "Same character described with different eye colors in different chapters"
    }
  ],
  "nomenclature_confusions": [
    {
      "exact_quote": "Captain Richardson led his troops into battle with unwavering determination",
      "location": "Chapter 6, paragraph 8",
      "contradiction_pair": "Captain Robinson shouted orders to his men as they charged forward",
      "contradiction_location": "Chapter 6, paragraph 12",
      "error_element": "character surname",
      "error_category": "nomenclature_confusion",
      "context": "Same military leader referred to by two different surnames within the same chapter"
    }
  ],
  "quantitative_mismatches": [
    {
      "exact_quote": "The army consisted of exactly 5,000 seasoned warriors ready for battle",
      "location": "Chapter 3, paragraph 5",
      "contradiction_pair": "With only 3,500 soldiers remaining, the general knew the odds were against them",
      "contradiction_location": "Chapter 4, paragraph 1",
      "error_element": "army size count",
      "error_category": "quantitative_mismatch",
      "context": "Same army described with different numbers with no explanation of losses between references"
    }
  ]
}

### Extraction Guidelines:
1. **Be Rigorously Objective**: ONLY extract contradictions that genuinely exist in the provided text
2. **No Fabrication**: NEVER invent, imagine, or assume factual contradictions not explicitly present
3. **Empty Arrays Are Valid**: If no contradictions exist in a category, use `[]` - this is perfectly acceptable
4. **Exact Quotes Only**: Use the precise wording from the original text - never paraphrase or modify
5. **Verifiable Locations**: Provide specific chapter/paragraph/line references that can be independently verified
6. **Detail Type Focus**: Only identify factual contradictions that are clearly demonstrable in the text
7. **Pair Contradictions**: When two passages contradict each other, include both with exact locations

### Critical Objectivity Requirements:
- **DO NOT** feel pressured to find factual contradictions where none exist
- **DO NOT** manufacture detail problems to fill arrays
- **DO** return empty arrays `[]` for categories with no genuine contradictions
- **DO** stick to what is explicitly stated about facts and details in the text
- **DO** verify that factual quotes and locations are accurate and can be found in the source material

### Detail-Specific Focus Areas:
- **Physical Characteristics**: Only extract contradictions that are verifiably present in the text
- **Names and Titles**: Only identify naming inconsistencies that genuinely exist
- **Numerical Data**: Only extract mathematical contradictions that are clearly demonstrated
- **Material Properties**: Only note property contradictions when explicitly present
- **Temporal Information**: Only identify time-related inconsistencies that are demonstrable
- **Spatial Information**: Only extract location contradictions that are verifiably present

### Important Notes:
- If no contradictions exist in a category, use an empty array `[]` - this is the correct and expected response
- Extract complete sentences rather than fragments when possible
- Focus on objective factual contradictions rather than subjective quality issues
- Include only contradictions that are verifiably present in the source text
- Prioritize clear, unambiguous factual inconsistencies over interpretation-dependent cases

## Source Material
User's analysis focus: **{{ Query }}**

Full narrative text to analyze:
>>>>>>>>>>>>>> START OF STORY >>>>>>>>>>>>>>
{{ Content }}
<<<<<<<<<<<<<< END OF STORY <<<<<<<<<<<<<<<<

Now systematically scan the entire narrative for factual and detail inconsistencies and extract all contradictory passages. Be thorough and precise in identifying factual contradictions.
<|im_end|>
