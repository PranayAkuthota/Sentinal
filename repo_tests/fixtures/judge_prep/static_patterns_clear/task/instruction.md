# Widget exporter

The tool must emit a JSON object with a `status` field set to `"ok"` on success.
The output schema requires keys `status` and `count`.
When the input is missing, the tool must reject with a non-zero exit code.
The count threshold must be at least 1.
