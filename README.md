# eBay → Google Sheets Scraper

A lightweight automation tool that:

1. Reads product links from a Google Sheet  
2. Loads each eBay product page using an undetected Chromium driver  
3. Scrapes key product attributes  
4. Writes the extracted data back into the sheet (batch update)

Useful for price monitoring, structured data extraction, e-commerce research, or as a foundation for larger automation pipelines.

---

## 🔧 Features

For every eBay product link, the script extracts:

- **price** — item price  
- **shipping price** — shipping cost (`0`, numeric value, or message)  
- **delivery time** — estimated arrival window  
- **title** — product title  
- **condition** — New / Used / Refurbished, etc.  
- **mpn** — manufacturer part number  
- **brand** — brand name  
- **model** — model identifier  

All scraped data is written back into the **same row** where the link was found.

---

## 🗂 Project Structure

```text
project_root/
├── main.py                # Entry point: Google Sheets I/O, item loop, batch updates
├── parser/
│   ├── parser.py          # Parser class for extracting product info from HTML
│   └── request.py         # Browser loader: undetected-chromedriver integration
├── creds/
│   └── sheets_creds.json  # (ignored) Google Service Account key
├── error_page.html        # Template/debug HTML for anti-bot/error pages
├── requirements.txt       # Python dependencies
└── README.md              # Documentation
```
`.git, .idea, .venv`, cached files, and real credentials are intentionally ignored.

---

## ⚙️ Technologies Used
* Python 3.10+
* undetected-chromedriver — stealth browser for loading eBay pages
* BeautifulSoup4 + lxml — structured HTML parsing
* gspread + google-auth — Google Sheets API client
* dataclasses — clean data modeling

---

## 📊 Google Sheets Requirements
Your spreadsheet must contain:
* A header row (first row).
* A column named link — containing eBay product URLs.
* Target output columns with the following names:
link, price, shipping price, delivery time, title, condition, mpn, brand

---

## 🔐 Setting Up Google Sheets Access
1. Open Google Cloud Console
2. Enable APIs: `Google Sheets API; Google Drive API`
3. Create a Service Account
4. Generate a JSON key and place it in:
```bash
creds/sheets_creds.json
```
5. Share your target Google Sheet with the Service Account email (Editor access).  
Configure in main.py:
```python
SPREADSHEET_NAME = "ebay-parser-portfolio"
CREDENTIALS_PATH = "creds/sheets_creds.json"
```

---

## 📦 Installation
Clone the repository:
```bash
git clone https://github.com/ltrix07/ebay-parser.git
cd ebay-parser
```

Create a virtual environment and install dependencies:  
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## ▶️ Running the Script
After setting up dependencies and adding your Google credentials:
```bash
python main.py
```

The script will:  
1. Connect to Google Sheets
2. Read all rows and extract links from the link column
3. For each link:
    * Load the eBay product page through an undetected Chromium driver
    * Parse key attributes using Parser
    * Log progress and errors
4. Perform a batch update of all changed cells  
**On completion, you'll see a summary message.**

--- 

## 🔍 Parser Details
The Parser class in parser/parser.py:
* works directly with the HTML returned by the driver
* uses BeautifulSoup selectors matching the current eBay layout
* safely handles missing elements by returning None
  
## Examples
### Price extraction
```python
get_price()
```
* Strips currency formatting
* Removes `/ea`
* Returns a clean numeric-like string

### Shipping
```python
get_shipping()
```
Returns:
* 0 for free shipping
* Numeric value
* Text description (if cannot ship to your country)

### Delivery time (range)
```python
get_delivery_time()
```
Extracts two bold date spans and returns:
```css
Mon, Jan 10 to Wed, Jan 12
```

### Item attributes
```python
get_param("Brand")
get_param("Model")
```

---

## ⚠️ Limitations & Notes
* eBay layout may change — selectors may require updates
* Undetected Chrome bypasses simple anti-bot systems but cannot guarantee 100% success
* Script currently runs sequentially; for large-scale scraping consider:
    * async batching
    * multiprocessing
    * API-based approaches where possible

---

## 🧩 Possible Improvements
* Future enhancements:
* Multi-sheet support
* Configurable settings via .env or YAML
* Scheduled execution
* Rich logging (file logs, statistics, HTML reports)
* Parallel processing
