# project-agent

A Python project that leverages the [agno](https://pypi.org/project/agno/) framework and Google Gemini models to analyze financial data and provide investment insights, with a focus on the Indian stock market.

## Features

- Uses Google Gemini models for advanced reasoning and data analysis.
- Integrates with Yahoo Finance via `YFinanceTools` for real-time stock data, analyst recommendations, company info, and news.
- Displays results in markdown tables for easy readability.
- Easily configurable via `.env` for API keys.

## Requirements

- Python 3.13+
- See [pyproject.toml](pyproject.toml) for dependencies.

## Setup

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd project-expt
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
   Or, if using a tool like [uv](https://github.com/astral-sh/uv):
   ```sh
   uv pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` and add your `GOOGLE_API_KEY` (already present in this repo).

4. **Run the agent:**
   ```sh
   python main.py
   ```

## Usage

The main script initializes an agent with the Gemini model and Yahoo Finance tools. It then asks the agent for the best stock to invest in the Indian market:

```python
agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    tools=[YFinanceTools(
        stock_price=True,
        analyst_recommendations=True,
        company_info=True,
        company_news=True
    )],
    instructions="Use tables to display data.",
    show_tool_calls=True,
    markdown=True,
)
agent.print_response("what is best the best stock to invest in indian market", stream=True)
```

## Configuration

- Edit `main.py` to change the prompt or agent configuration.
- Update `.env` with your API keys as needed.

## License

MIT License (add your license here if different).

---

*This