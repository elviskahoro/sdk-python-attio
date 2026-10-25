(if (.diff.paths_added | length) > 0 then
  "\nNew endpoints:\n" + (.diff.paths_added | map("- " + .) | join("\n"))
else empty end),
(if (.diff.paths_removed | length) > 0 then
  "\nRemoved endpoints:\n" + (.diff.paths_removed | map("- " + .) | join("\n"))
else empty end),
(if (.diff.operations_added | length) > 0 then
  "\nNew operations:\n" + (.diff.operations_added | map("- " + .) | join("\n"))
else empty end),
(if (.diff.operations_removed | length) > 0 then
  "\nRemoved operations:\n" + (.diff.operations_removed | map("- " + .) | join("\n"))
else empty end),
(if (.diff.operations_changed | length) > 0 then
  "\nChanged operations:\n" + (.diff.operations_changed | keys | map("- " + .) | join("\n"))
else empty end),
(if (.diff.top_level_changed | length) > 0 then
  "\nChanged top-level keys:\n" + (.diff.top_level_changed | keys | map("- " + .) | join("\n"))
else empty end),
(if (.diff.description_only_changes | length) > 0 then
  "\n\(.diff.description_only_changes | length) description-only change(s)."
else empty end),
"\nGenerated with `ci/pipeline.py generate --no-fetch` + post-generation patches; pytest green."
