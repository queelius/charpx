# csvcat -- CSV/TSV Viewer

View and visualize CSV and TSV data in the terminal. csvcat provides two
modes: a formatted table display with sorting and filtering, and chart
visualizations powered by vizlib and dapple renderers.

## Installation

```bash
pip install dapple[csvcat]
```

No additional dependencies are required. csvcat uses Python's stdlib `csv`
module for parsing and dapple's vizlib for charting.

## Usage

### Table Display

```bash
# View a CSV file as a formatted table
csvcat data.csv

# View a TSV file (delimiter auto-detected)
csvcat data.tsv

# Read from stdin
cat data.csv | csvcat
```

The table output includes ANSI-colored headers and type-based value coloring:
numeric values appear in cyan, booleans in yellow, and null/empty values are
dimmed.

### Column Selection

```bash
# Show only specific columns
csvcat data.csv --cols "name,revenue,date"
```

### Sorting

```bash
# Sort by a column (ascending)
csvcat data.csv --sort revenue

# Sort descending
csvcat data.csv --sort revenue --desc
```

Sorting is numeric-aware: columns containing numbers are sorted numerically,
while text columns sort alphabetically.

### Row Limiting

```bash
# Show first N rows
csvcat data.csv --head 10

# Show last N rows
csvcat data.csv --tail 5
```

### Delimiter Control

```bash
# Explicit delimiter (overrides auto-detection)
csvcat -d ";" data.csv
csvcat -d "\t" data.tsv

# Handle files without headers
csvcat --no-header data.csv
```

### Color Modes

```bash
# Default: color by value type (numbers=cyan, bools=yellow, nulls=dim)
csvcat data.csv

# Cycle colors by column instead
csvcat data.csv --cycle-color
```

### Output to File

```bash
csvcat data.csv -o output.txt
```

## Chart Visualization

csvcat includes five chart modes that render data using dapple. These modes
are mutually exclusive.

### Sparkline

A compact line chart of a numeric column:

```bash
csvcat data.csv --spark revenue
csvcat data.csv --spark temperature -r quadrants
```

### Line Plot

A line plot with optional zero-axis baseline:

```bash
csvcat data.csv --plot revenue
csvcat data.csv --plot price -w 100 -H 20
```

### Bar Chart

A bar chart of category counts (counts occurrences of each unique value):

```bash
csvcat data.csv --bar category
csvcat data.csv --bar status -r sextants
```

### Histogram

Distribution histogram of a numeric column:

```bash
csvcat data.csv --histogram age
csvcat data.csv --histogram salary -w 80 -H 15
```

### Heatmap

A heatmap from multiple numeric columns:

```bash
csvcat data.csv --heatmap "col1,col2,col3"
```

### Chart Options

All chart modes accept renderer, size, and output options:

```bash
# Renderer selection (default: braille)
csvcat data.csv --spark revenue -r quadrants
csvcat data.csv --bar category -r sextants

# Size control
csvcat data.csv --spark revenue -w 80 -H 15

# Output to file
csvcat data.csv --spark revenue -o chart.txt
```

## Examples

### Sales Dashboard

```bash
# View the data
csvcat sales.csv --cols "product,revenue,units" --sort revenue --desc --head 20

# Sparkline of revenue over time
csvcat sales.csv --spark revenue

# Bar chart of sales by product category
csvcat sales.csv --bar product
```

### Log Analysis

```bash
# Pipe from other tools
grep "ERROR" app.log | csvcat -d " " --bar 3

# Histogram of response times
csvcat access.csv --histogram response_time
```

## Python API

csvcat's data model can be used programmatically:

```python
from dapple.extras.csvcat.csvcat import (
    read_csv, select_columns, sort_by, head, tail,
    format_table, extract_numeric, extract_categories,
)

with open("data.csv") as f:
    data = read_csv(f)

# Filter and sort
data = select_columns(data, ["name", "revenue"])
data = sort_by(data, "revenue", reverse=True)
data = head(data, 10)

# Print formatted table
print(format_table(data))

# Extract numeric values for custom visualization
values = extract_numeric(data, "revenue")
```

## Entry Point

```
csvcat = dapple.extras.csvcat.cli:main
```

## Reference

```
usage: csvcat [-h] [--cols COLS] [--sort COLUMN] [--desc] [--head N] [--tail N]
              [--no-header] [-d DELIMITER] [--cycle-color]
              [--plot COLUMN | --spark COLUMN | --bar COLUMN | --histogram COLUMN | --heatmap COLUMNS]
              [-r RENDERER] [-w WIDTH] [-H HEIGHT] [-o FILE]
              [file]

Terminal CSV/TSV viewer with visualization modes

positional arguments:
  file                  CSV/TSV file to display (reads stdin if omitted)

table options:
  --cols                Comma-separated column names to select
  --sort                Sort by column
  --desc                Sort descending (use with --sort)
  --head N              Show first N rows
  --tail N              Show last N rows
  --no-header           Data has no header row
  -d, --delimiter       Explicit delimiter (default: auto-detect)
  --cycle-color         Color each column with a rotating palette

plot modes (mutually exclusive):
  --plot COLUMN         Line plot of a numeric column
  --spark COLUMN        Sparkline of a numeric column
  --bar COLUMN          Bar chart of category counts
  --histogram COLUMN    Histogram of a numeric column
  --heatmap COLUMNS     Heatmap of multiple numeric columns (comma-separated)

plot options:
  -r, --renderer        Renderer (default: braille)
  -w, --width           Chart width in terminal characters
  -H, --height          Chart height in terminal characters
  -o, --output          Write output to file instead of stdout
```
