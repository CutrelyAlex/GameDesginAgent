# API Providers — Bocha & Tavily

This file summarizes the calling conventions used by this project for the two
approved search providers: Bocha (博查) and Tavily. Store API keys in environment
variables (`BOCHA_API_KEY`, `TAVILY_API_KEY`) — do not commit secrets to the
repository. See `.env.example` for a local dev template.

---

## Bocha (博查)

- Base URL: `https://api.bochaai.com`
- Primary endpoint (Web Search): `POST https://api.bochaai.com/v1/web-search`
- Authentication: Header `Authorization: Bearer {BOCHA_API_KEY}`
- Content-Type: `application/json`

Request body (JSON) example:

```json
{
  "query": "深圳独立游戏",
  "summary": true,
  "count": 10,
  "freshness": "noLimit"
}
```

Notes:
- `query` (string) is required.
- `summary` (bool) controls whether the API returns a `summary` field per result.
- `count` limits number of results (1-50).
- `freshness` can be `noLimit`, `oneDay`, `oneWeek`, `oneMonth`, `oneYear`, or a
  date/range like `YYYY-MM-DD` or `YYYY-MM-DD..YYYY-MM-DD`.

Response shape (high level):
- Top-level: `{ "code": int, "log_id": str, "msg": null|str, "data": {...} }`
- `data._type` == `"SearchResponse"`
- `data.webPages.value` is a list of results; each item contains `name`, `url`,
  `snippet`, `summary` (when requested), `siteName`, `datePublished`, etc.

Example usage (Python requests):

```python
resp = requests.post(
    "https://api.bochaai.com/v1/web-search",
    headers={"Authorization": f"Bearer {os.environ['BOCHA_API_KEY']}"},
    json={"query": "深圳独立游戏", "summary": True, "count": 10},
    timeout=10,
)
resp.raise_for_status()
j = resp.json()
```

---

## Tavily

- Base URL: `https://api.tavily.com`
- Observed working endpoint (project tests): `POST https://api.tavily.com/search`
- Authentication: `Authorization: Bearer {TAVILY_API_KEY}` (observed) — if this does not
  work, try `x-api-key` header depending on provider docs.
- Content-Type: `application/json`

Request body examples (Tavily appears to accept one of the following shapes):

1) Preferred JSON body (if supported):

```json
{
  "query": "深圳独立游戏"
}
```

2) Alternative body shape (legacy):

```json
{ "q": "深圳独立游戏" }
```

Response shape (observed in tests):
- Top-level keys included: `query`, `follow_up_questions`, `answer`, `images`, `results`, `response_time`, `request_id`
- `results` is an array of result objects; fields commonly seen: `title`, `url`, `snippet`.

Example usage (Python requests):

```python
resp = requests.post(
    "https://api.tavily.com/search",
    headers={"Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}"},
    json={"query": "深圳独立游戏"},
    timeout=10,
)
resp.raise_for_status()
j = resp.json()
```

Notes & troubleshooting:
- If you get `401` or `403`, check the API key value and permission scope.
- If you get `422` (validation error), try alternate body shapes (e.g. `{"q": ...}` or `{"query":...}`).
- If you encounter TLS/SSL errors, check network/proxy/CA configuration on your host.

---

## Small LLM for Keyword Generation (Optional)

- Purpose: Generate keyword variants from a single input keyword for better search results.
- Configuration: Via `.env` file (`SMALL_LLM_URL`, `SMALL_LLM_MODEL`, `SMALL_LLM_API_KEY`)
- Supported providers: Ollama (local), OpenAI-compatible APIs
- Example configurations:
  - Ollama: `SMALL_LLM_URL=http://localhost:11434`, `SMALL_LLM_MODEL=llama2`
  - OpenAI: `SMALL_LLM_URL=https://api.openai.com/v1`, `SMALL_LLM_MODEL=gpt-3.5-turbo`, `SMALL_LLM_API_KEY=sk-...`

Request example (OpenAI-compatible):

```python
import openai

client = openai.OpenAI(
    base_url=os.environ.get('SMALL_LLM_URL'),
    api_key=os.environ.get('SMALL_LLM_API_KEY'),
)

response = client.chat.completions.create(
    model=os.environ.get('SMALL_LLM_MODEL', 'gpt-3.5-turbo'),
    messages=[
        {"role": "system", "content": "You are a keyword optimization assistant."},
        {"role": "user", "content": f"Generate 5 search-friendly keyword variants for: {keyword}"}
    ],
    max_tokens=100,
)
```

Notes:
- Feature is optional; if LLM config is missing, keyword generation is skipped.
- Prompt should encourage multiple angles (human-friendly, professional, technical, etc.).
- Fallback: If LLM unavailable, use original keyword without variants.

---

## Common recommendations

- Always include `Authorization` header using `Bearer` unless docs specify otherwise.
- Use `timeout` on HTTP requests and implement exponential backoff for rate limits.
- Persist provenance metadata for each response: provider, endpoint, api_version (if available), request_id/log_id, timestamp.
- For local development, use `.env` (copy from `.env.example`) and ensure `.env` is gitignored.

