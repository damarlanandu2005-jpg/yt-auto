# Your own scripts

Put a script here as a plain text file (for example `cartoon/scripts/volcano.txt`), then run
GitHub → Actions → "Stickman Short" → Run workflow with:

- **script_file**: `cartoon/scripts/volcano.txt`
- **writer**: `gemini`

The first line is the topic / question, for example `What if you fell into a volcano?`. Then the narration,
110-140 words, in the "What if...?" style: a hook question, what the stickman goes through, the true answer,
and a strong closing question.

What happens to it:
1. The plan and the Wikipedia sources are found for it.
2. It is split into scenes and **every factual sentence is checked** against Wikipedia. Sentences the sources do
   not support are fixed or removed (rule: no source, no claim).
3. The scenes are drawn, checked and rendered, and a release is made for your review.
4. The release has `owner_script_changes.md`: what was fixed or removed in your script, and why.
