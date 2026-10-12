---
name: translate
description: Use when text must be translated or a literal or machine translation improved - an email, a document, instructions, interface strings, a post - "translate this", "translate into German", "improve this translation", "keep the tone", "переклади", "переклади англійською", "зроби переклад", "покращ переклад", "як це буде англійською". Gives a natural translation with short notes. Not for rewriting text in the same language (humanizer).
---
Adapted from https://github.com/mohitagw15856/pm-claude-skills@d3897cee0eed skills/professional-translator (MIT) - see NOTICE.

**Core rule: meaning, tone and intent, not words.** The result reads as if it was written in the target language. Ambiguities are surfaced, never silently resolved.

## When
- Translating text between languages, or fixing a translation that reads literal.
- Not: same-language rewriting (`humanizer`). Not: a full product or market adaptation - flag it and ask the human how far to go.

## Steps
1. **Inputs (ask only what is missing):** the text; source -> target language, with the regional variant when it matters (e.g. European vs Latin American Spanish, Brazilian vs European Portuguese); the register and reader (formal / neutral / casual, who reads it); what the text is (email, contract, interface string, instructions, marketing) - it changes the choices.
2. **Glossary and do-not-translate terms.** Read them from the project profile when it has them (a glossary, product terms, names). If it has none and the text has fixed terms, ask once and offer to save the answer to the profile. Brand and product names, people's names, code, identifiers, commands, URLs, file paths and placeholders stay verbatim.
3. **Translate for meaning.** Match the register (formal vs informal "you" and politeness levels are a choice to note). Idioms -> the equivalent expression or the plain meaning. Dates, numbers, units and currency -> the target convention, or flagged when changing them would change the facts.
4. **Localisation flags.** Where a literal rendering would be wrong or odd (cultural references, examples, legal terms, jokes), adapt it and say so, or flag it for the human to decide.
5. **Ambiguities.** Anything in the source open to two readings: state the reading you chose. Ask first when the choice changes the meaning materially.
6. **Self-check:** read the translation alone, as a target-language reader - natural? same facts, numbers, names and links as the source? nothing added or dropped?
7. **Deliver.** Translation + notes (template). If it goes out to other people, run `humanizer` on the target-language text when you can judge that language well; otherwise say it was not run. NEVER overwrite the human's original document without a yes - give the translation alongside.
Privacy: do not paste the text into an outside translation service or a web search; translate it yourself. If a hosted service would help, ask first.

## Output template
```markdown
### <source> -> <target> (<variant>), register: <formal/neutral/casual>
<translation>

**Notes**
- Register: <how formality was handled>
- Adapted: <term/idiom> -> <rendering>, because <reason>
- Kept verbatim: <names, code, URLs>
- Localisation: <units/dates/references changed or flagged for you>
- Ambiguity: "<source phrase>" read as <reading> - say if you meant <other>
```
For a short text the notes may be one line, or none when nothing needed a choice.

## Red flags
| Thought | Reality |
|---|---|
| "Word for word is safer" | It changes the tone and often the meaning |
| "I'll translate the product name too" | Names, code, URLs and identifiers stay verbatim |
| "I'll pick the likely meaning" quietly | Surface it in the notes |
| "Close enough on the formality" | Wrong register can offend or undermine - choose and note it |
| "I'll replace the original file" | Only with the human's yes |

## Example
A support email from English to German for a business customer. Register: formal "Sie". "Hop on a call" -> a neutral formal phrasing for a short call. The product name and a URL kept verbatim; "12/03" flagged (December 3 or 12 March?) and rendered as the human confirmed. Notes: 3 lines.

LIVING: when a translation is corrected, add the term to the profile glossary (with the human's yes) or the pattern to step 3.
