# ComBase Scraper

Simple ComBase data scraper with English interface.

## Quick Start

1. Install dependencies:
```bash
pip install -r config/requirements.txt
```

2. Run the scraper:

**Single Thread (Simple):**
```bash
python simple_scraper.py
```

**Parallel (10 Threads - Faster):**
```bash
python parallel_scraper.py
```

3. Press `Ctrl+C` to stop safely

## Features

- **Parallel Processing**: 10 threads for 10x speed improvement
- **Search Delay**: 2-minute wait after search before scraping starts
- **Deduplication**: Removes duplicate food parts from organism names
- **Thread-Safe**: Real-time progress tracking across all threads

## Output

- Data saved to `data/` directory
- Each file contains 1,000 records
- Complete organism names with ID, name, and food description
