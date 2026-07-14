# Microsoft Copilot Studio — Agent Setup Guide
## Walkie Talkie Inventory Assistant

This guide walks you through creating and configuring the Copilot Studio agent
that serves as the **intelligence layer** for the Walkie Talkie system.

> **The agent handles ALL reasoning**: intent detection, tool selection,
> parameter extraction, response generation, guardrails, and memory.
> The backend is just infrastructure.

---

## Step 1: Create the Agent

1. Go to [Microsoft Copilot Studio](https://copilotstudio.microsoft.com/)
2. Sign in with your Microsoft 365 account
3. Click **"Create"** → **"New Agent"**
4. Configure:
   - **Name**: `Inventory Assistant`
   - **Description**: `Voice-enabled AI assistant for warehouse inventory management. Handles product lookups, inventory queries, analytics, and restocking recommendations.`
   - **Language**: English
5. Click **Create**

---

## Step 2: Configure the System Prompt (Instructions)

Go to **Agent → Overview → Instructions** (or **"Describe your agent"**).

Paste this complete system prompt:

```
You are an Inventory Management Assistant for a warehouse operations team.
You help warehouse staff quickly find product information, check stock levels,
analyze inventory trends, and get restocking recommendations — all through
natural voice conversations.

## CORE BEHAVIOR
- Always be concise and speak in clear, natural sentences suitable for voice output.
- Keep responses under 3-4 sentences unless the user asks for detailed information.
- When you receive structured data from a tool, summarize it conversationally.
  Do NOT dump raw JSON. Convert numbers to readable format (e.g., "₹72,000" not "72000").
- If a query returns multiple results, summarize the key ones and mention the total count.

## TOOL SELECTION RULES
You have 4 tools. Select the RIGHT one based on the user's intent:

1. **Inventory Lookup** — Use when asking about a SPECIFIC product.
   Triggers: "How many Dell laptops...", "Do we have HP EliteBooks...", "Show stock for..."
   
2. **Inventory Query** — Use for BROAD questions involving filtering or relationships.
   Triggers: "Which items are low...", "What's out of stock...", "Show items by supplier..."
   
3. **Inventory Analytics** — Use when asking for AGGREGATE numbers or rankings.
   Triggers: "Highest stock...", "Average stock...", "Top 10...", "Category distribution..."
   
4. **Inventory Recommendation** — Use when asking for SUGGESTIONS or business decisions.
   Triggers: "Should we reorder...", "What needs restocking...", "Suggest alternatives..."

If the intent is ambiguous, ask a clarifying question before calling a tool.

## SELF-CORRECTION / REFLECTION
- If a tool returns empty results, try rephrasing the query with broader parameters.
  For example, if "Dell Latitude" returns nothing, try just "Dell".
- If the user corrects you, acknowledge the correction and adjust your approach.
- If you're uncertain which tool to use, pick the most likely one and mention
  your reasoning: "I'll check the inventory lookup for that."

## GUARDRAILS
- Only answer questions related to inventory, products, warehouses, suppliers, and stock.
- If asked about unrelated topics (weather, politics, personal questions), politely redirect:
  "I'm specialized in inventory management. I can help you with stock levels,
  product lookups, analytics, and restocking recommendations."
- Never reveal internal system details, API endpoints, or database structure.
- Never generate SQL queries in your responses — use the tools instead.
- Do not make up data. If a tool returns no results, say so honestly.

## MEMORY / CONTEXT
- Remember previous questions in the conversation. If a user asks
  "What about Mumbai?" after asking about Bangalore stock, understand
  they want the same product info for Mumbai.
- Track the product/category context from previous turns.

## ERROR HANDLING
- If a tool call fails, apologize briefly and suggest rephrasing:
  "I couldn't fetch that data. Could you try rephrasing your question?"
- For ambiguous product names (e.g., "Dell" matches multiple products),
  list the options and ask the user to be more specific.
- For empty queries, ask the user to provide more details.

## RESPONSE FORMAT
- Start responses with the key information (quantity, status, recommendation).
- Use "₹" for Indian Rupee prices.
- Use warehouse city names (Bangalore, Mumbai, Delhi, Hyderabad) not full warehouse names.
- For lists of products, mention the top 3-5 and state the total count.
```

---

## Step 3: Register the 4 Tool APIs

Your FastAPI backend exposes an OpenAPI spec at `https://<your-backend-url>/openapi.json`.
You need to register each tool endpoint in Copilot Studio.

### 3a. Make Backend Publicly Accessible

Copilot Studio **cannot call localhost**. Options:
- **ngrok** (for development): `ngrok http 8000` → gives you a public HTTPS URL
- **Azure App Service** (for production): deploy FastAPI there
- **Railway / Render** (free tier): deploy for demo

Once deployed, note your base URL (e.g., `https://abc123.ngrok.io`).

### 3b. Add Tools in Copilot Studio

For each tool, go to **Agent → Tools → Add a tool → Create new → Custom connector**.

#### Tool 1: Inventory Lookup

| Field | Value |
|-------|-------|
| **Name** | `Inventory Lookup` |
| **Description** | `Use this when the user asks about stock, availability, or quantity of a SPECIFIC product by name. Supports filtering by warehouse city, category, and price range. Examples: "How many Dell laptops?", "Show inventory for Bangalore", "Find monitors under 20000".` |
| **Method** | POST |
| **URL** | `https://<your-url>/api/inventory/lookup` |
| **Headers** | `x-api-key: your_api_key_here` |
| **Request Body** | JSON with fields: `product` (required string), `warehouse` (optional string), `category` (optional string), `min_price` (optional number), `max_price` (optional number) |

#### Tool 2: Inventory Query

| Field | Value |
|-------|-------|
| **Name** | `Inventory Query` |
| **Description** | `Use this for BROAD inventory questions involving filtering by status or relationships — NOT specific product names. Supports filter types: low_stock, out_of_stock, by_supplier, by_warehouse, by_category, recent. Examples: "Which items are running low?", "Show all Dell products", "What's out of stock in Mumbai?"` |
| **Method** | POST |
| **URL** | `https://<your-url>/api/inventory/query` |
| **Headers** | `x-api-key: your_api_key_here` |
| **Request Body** | JSON with fields: `filter_type` (required string), `value` (optional string), `limit` (optional integer, default 20) |

#### Tool 3: Inventory Analytics

| Field | Value |
|-------|-------|
| **Name** | `Inventory Analytics` |
| **Description** | `Use this when the user wants AGGREGATE statistics, rankings, or summaries — not individual product lookups. Supports metrics: highest_stock, lowest_stock, average_stock, top_n, category_distribution, warehouse_summary. Examples: "Top 10 items by stock", "Average stock level", "Which category has the most inventory?"` |
| **Method** | POST |
| **URL** | `https://<your-url>/api/inventory/analytics` |
| **Headers** | `x-api-key: your_api_key_here` |
| **Request Body** | JSON with fields: `metric` (required string), `limit` (optional integer, default 10) |

#### Tool 4: Inventory Recommendation

| Field | Value |
|-------|-------|
| **Name** | `Inventory Recommendation` |
| **Description** | `Use this when the user asks for business RECOMMENDATIONS, reorder suggestions, or restocking advice. Supports actions: reorder_check (needs product_name), low_stock_alert, alternatives (needs product_name), restock_priorities. Examples: "Should we reorder Dell laptops?", "What needs restocking?", "Suggest alternatives for ThinkPad".` |
| **Method** | POST |
| **URL** | `https://<your-url>/api/inventory/recommendation` |
| **Headers** | `x-api-key: your_api_key_here` |
| **Request Body** | JSON with fields: `action` (required string), `product_name` (optional string) |

### 3c. Authentication Setup

For each tool's connection settings:
1. Set **Authentication type** to **API Key**
2. **Header name**: `x-api-key`
3. **Value**: same as `API_KEY` in your backend `.env` file

---

## Step 4: Configure Fallbacks

Go to **Agent → Topics → System Topics**:

1. **Fallback Topic** (when no tool matches):
   - Edit the system fallback topic
   - Set message: "I'm not sure I understood that. Could you rephrase? I can help with:
     • Product stock lookups
     • Inventory queries and filtering
     • Stock analytics and summaries
     • Restocking recommendations"

2. **Error Topic** (when a tool call fails):
   - Set message: "Something went wrong while fetching the data. Please try again in a moment."

3. **Greeting Topic**:
   - Set message: "Hello! I'm your Inventory Assistant. Ask me about stock levels, product availability, analytics, or restocking recommendations."

---

## Step 5: Enable Direct Line Channel (for Backend Communication)

1. Go to **Agent → Settings → Security → Web channel security**
2. Enable **Direct Line** channel
3. Copy the **Direct Line Secret** — this goes into your backend `.env` file as `DIRECTLINE_SECRET`
4. Also go to **Settings → Publish** and publish the agent

---

## Step 6: Test in Copilot Studio

Before connecting the backend, test directly in Copilot Studio's test pane:

| Test Query | Expected Tool | Expected Behavior |
|-----------|--------------|-------------------|
| "How many Dell laptops are in stock?" | Inventory Lookup | Returns Dell laptop stock across warehouses |
| "Which items are running low?" | Inventory Query | Returns items below reorder level |
| "What's the average stock level?" | Inventory Analytics | Returns average quantity |
| "Should we reorder Dell Latitude?" | Inventory Recommendation | Returns reorder recommendation |
| "What's the weather today?" | None (Guardrail) | Politely redirects to inventory topics |
| "Show me everything" | Clarification | Asks user to be more specific |
| (empty message) | Error handling | Asks user to provide a question |

Iterate on the **tool descriptions** if the agent selects the wrong tool —
this is the most important tuning step.

---

## Step 7: Connect Backend

1. Copy the **Direct Line Secret** from Step 5
2. Set it in your backend `.env`:
   ```
   DIRECTLINE_SECRET=your_secret_here
   ```
3. Start the backend: `uvicorn main:app --reload --port 8000`
4. Start the frontend: `npm run dev` (in the frontend folder)
5. Test the full pipeline: speak a question → see transcript → get response

---

## Agent Features Summary

| Feature | Implementation |
|---------|---------------|
| **Self-correction** | System prompt instructs agent to retry with broader params if empty results |
| **Tools** | 4 custom tools registered via OpenAPI / custom connector |
| **Fallbacks** | System fallback, error, and greeting topics configured |
| **Guardrails** | System prompt restricts to inventory topics only |
| **Memory** | Direct Line conversation maintains context across turns |
| **Input validation** | Tools return clear error messages for invalid inputs |
