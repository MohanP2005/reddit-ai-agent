# Reddit AI Agent

This project uses Google's Gemini AI to find and analyze the most active Reddit threads based on user-provided topics. It scrapes Reddit data and provides insights about trending discussions.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

Run the main script:
```bash
python main.py
```

The script will:
1. Prompt you for a topic
2. Use Gemini AI to find relevant Reddit threads
3. Scrape and analyze the most active thread
4. Display the results

## Requirements

- Python 3.8+
- Google Gemini API key
- Internet connection

## License

MIT License 