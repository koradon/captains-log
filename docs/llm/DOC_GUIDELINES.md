# Documentation Guidelines

## Language

- Write in clear, direct English unless the repository already uses another language consistently.
- Prefer short sections and concrete examples.

## Structure

- Start with context: what this document is for.
- Use `## Status` and `## Related` sections instead of YAML frontmatter.
- Explain decisions, not only outcomes.
- Include examples, commands, or diagrams when they reduce ambiguity.

## Consistency

- Match the tone and structure of nearby docs.
- Use the same terminology as the codebase and existing specs.
- Keep filenames and headings stable once published.

## Agent behavior

- Read before write.
- Update only what the current task requires.
- Leave unrelated docs unchanged.
- Make updates reviewable in Git with focused diffs.
- Extend the documentation tree only when the project genuinely needs a new section.

## Quality bar

A documentation update is good when another contributor can understand:

1. what changed,
2. why it changed,
3. how to work with the result.
