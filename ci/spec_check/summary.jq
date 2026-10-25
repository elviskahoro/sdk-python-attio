if .structural_changes then
  "**Structural drift detected** — regeneration recommended."
else
  "No structural changes."
end,
(if .overlay.healthy then
  "\nOverlay: healthy."
else
  "\n**Overlay problems** (fix overlay.yaml before regenerating):\n" +
  ((.overlay.dead_targets // []) | map("- dead target: " + .) | join("\n")) + "\n" +
  ((.overlay.uncovered_timestamp_values // []) | map("- uncovered timestamp value: " + .) | join("\n")) + "\n" +
  ((.overlay.misdirected_targets // []) | map("- fix action not on a timestamp value: " + .) | join("\n")) + "\n" +
  ((.overlay.dropped_error_codes // []) | map("- error-code enum out of sync: " + .) | join("\n"))
end),
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
(if (.diff.path_items_changed | length) > 0 then
  "\nChanged path items:\n" + (.diff.path_items_changed | keys | map("- " + .) | join("\n"))
else empty end),
(if (.diff.components_added | length) > 0 then
  "\nNew component definitions:\n" + (.diff.components_added | map("- " + .) | join("\n"))
else empty end),
(if (.diff.components_removed | length) > 0 then
  "\nRemoved component definitions:\n" + (.diff.components_removed | map("- " + .) | join("\n"))
else empty end),
(if (.diff.components_changed | length) > 0 then
  "\nChanged component definitions:\n" + (.diff.components_changed | keys | map("- " + .) | join("\n"))
else empty end),
(if (.diff.top_level_changed | length) > 0 then
  "\nChanged top-level keys:\n" + (.diff.top_level_changed | keys | map("- " + .) | join("\n"))
else empty end),
(if (.diff.description_only_changes | length) > 0 then
  "\n\(.diff.description_only_changes | length) description-only change(s) (no action needed)."
else empty end)
