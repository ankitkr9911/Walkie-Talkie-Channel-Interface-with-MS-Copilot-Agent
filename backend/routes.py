"""
routes.py — API Endpoints
===========================
Two categories of endpoints:

1. PIPELINE ENDPOINTS (called by frontend):
   - POST /api/voice  → audio in, text + audio out
   - POST /api/chat   → text in, text + audio out

2. TOOL ENDPOINTS (called by Copilot Studio):
   - POST /api/inventory/lookup         → specific product lookups
   - POST /api/inventory/query          → flexible inventory queries
   - POST /api/inventory/analytics      → aggregation & analytics
   - POST /api/inventory/recommendation → reorder & restock suggestions

IMPORTANT: Tool endpoint descriptions are used by Copilot Studio's LLM
to decide which tool to call. Treat them as prompt engineering.
"""

import os
import base64
import tempfile
from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from database import execute_query, execute_scalar
from copilot_client import copilot
from speech import transcribe_audio, synthesize_speech

router = APIRouter()

# ---------- API Key Authentication (for tool endpoints) ----------
API_KEY = os.getenv("API_KEY", "dev-key-123")


def _verify_api_key(x_api_key: str = Header(default=None)):
    """Validate API key from Copilot Studio tool calls."""
    if API_KEY and x_api_key != API_KEY:
        # Skip validation in dev mode (API_KEY == "dev-key-123")
        if API_KEY != "dev-key-123":
            raise HTTPException(status_code=401, detail="Invalid API key")


# ====================================================================
# SECTION 1: PIPELINE ENDPOINTS (Frontend → Backend → Copilot → Backend → Frontend)
# ====================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's text message")
    session_id: str = Field(default="default", description="Session ID for conversation memory")


@router.post("/api/voice", summary="Voice pipeline — audio in, text + audio out")
async def voice_pipeline(audio: UploadFile = File(...), session_id: str = "default"):
    """
    Full voice pipeline:
    1. Receive audio from frontend (webm/wav)
    2. Transcribe with Faster-Whisper → text
    3. Send transcript to Copilot Studio → get response
    4. Convert response to speech with edge-tts → audio
    5. Return transcript + response text + response audio (base64)
    """
    # Save uploaded audio to temp file for Whisper
    suffix = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Step 1: Speech-to-Text
        transcript = transcribe_audio(tmp_path)
        if not transcript.strip():
            return {"transcript": "", "response": "I didn't catch that. Could you please try again?", "audio": None}

        # Step 2: Send to Copilot Studio
        response_text = await copilot.send_message(transcript, session_id)

        # Step 3: Text-to-Speech
        audio_bytes = await synthesize_speech(response_text)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        return {"transcript": transcript, "response": response_text, "audio": audio_b64}

    finally:
        os.unlink(tmp_path)  # Cleanup temp file


@router.post("/api/chat", summary="Text chat pipeline — text in, text + audio out")
async def chat_pipeline(req: ChatRequest):
    """
    Text-only pipeline (skips STT):
    1. Send user text to Copilot Studio
    2. Convert response to speech
    3. Return response text + audio
    """
    if not req.message.strip():
        return {"response": "Please provide a message.", "audio": None}

    response_text = await copilot.send_message(req.message, req.session_id)

    # Generate speech for the response
    audio_bytes = await synthesize_speech(response_text)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return {"response": response_text, "audio": audio_b64}


# ====================================================================
# SECTION 2: TOOL ENDPOINTS (Called by Copilot Studio agent)
# ====================================================================

# ---------- Tool 1: Inventory Lookup ----------

class LookupRequest(BaseModel):
    product: str = Field(..., description="Product name to search for (e.g. 'Dell Laptop', 'HP EliteBook'). Supports partial matching.")
    warehouse: Optional[str] = Field(None, description="Filter by warehouse city name (e.g. 'Bangalore', 'Mumbai')")
    category: Optional[str] = Field(None, description="Filter by category (e.g. 'Laptops', 'Monitors', 'Accessories')")
    min_price: Optional[float] = Field(None, description="Minimum unit price in INR")
    max_price: Optional[float] = Field(None, description="Maximum unit price in INR")


@router.post(
    "/api/inventory/lookup",
    summary="Look up inventory for a specific product",
    description=(
        "Use this tool when the user asks about stock, availability, or quantity of a SPECIFIC product. "
        "Supports filtering by warehouse, category, and price range. "
        "Examples: 'How many Dell laptops are in stock?', 'Show inventory for Bangalore warehouse', "
        "'Do we have HP EliteBooks available?', 'Find all monitors under ₹20,000'."
    ),
)
async def inventory_lookup(req: LookupRequest, x_api_key: str = Header(default=None)):
    """Look up specific products by name, optionally filtered by warehouse/category/price."""
    _verify_api_key(x_api_key)

    # Build dynamic SQL query with parameterized filters
    query = """
        SELECT p.name AS product_name, p.sku, p.unit_price, p.description,
               c.name AS category, s.name AS supplier,
               w.name AS warehouse, w.city,
               i.quantity, i.reorder_level, i.last_restocked,
               CASE WHEN i.quantity = 0 THEN 'Out of Stock'
                    WHEN i.quantity <= i.reorder_level THEN 'Low Stock'
                    ELSE 'In Stock' END AS status
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN suppliers s ON p.supplier_id = s.id
        JOIN warehouses w ON i.warehouse_id = w.id
        WHERE LOWER(p.name) LIKE LOWER(?)
    """
    params = [f"%{req.product}%"]

    if req.warehouse:
        query += " AND LOWER(w.city) LIKE LOWER(?)"
        params.append(f"%{req.warehouse}%")
    if req.category:
        query += " AND LOWER(c.name) LIKE LOWER(?)"
        params.append(f"%{req.category}%")
    if req.min_price is not None:
        query += " AND p.unit_price >= ?"
        params.append(req.min_price)
    if req.max_price is not None:
        query += " AND p.unit_price <= ?"
        params.append(req.max_price)

    query += " ORDER BY p.name, w.city"
    results = await execute_query(query, tuple(params))

    return {
        "results": results,
        "count": len(results),
        "message": f"Found {len(results)} matching inventory records" if results else "No matching products found",
    }


# ---------- Tool 2: Inventory Query ----------

class QueryRequest(BaseModel):
    filter_type: str = Field(
        ...,
        description=(
            "Type of query to execute. Must be one of: "
            "'low_stock' (items below reorder level), "
            "'out_of_stock' (items with zero quantity), "
            "'by_supplier' (items from a specific supplier), "
            "'by_warehouse' (all items in a specific warehouse), "
            "'by_category' (all items in a category), "
            "'recent' (recently restocked items)"
        ),
    )
    value: Optional[str] = Field(None, description="Filter value — supplier name, warehouse city, or category name depending on filter_type")
    limit: int = Field(default=20, description="Maximum number of results to return")


@router.post(
    "/api/inventory/query",
    summary="Run flexible inventory queries with filters",
    description=(
        "Use this tool when the user asks broad inventory questions that involve filtering, "
        "grouping, or relationships — NOT about a specific product name. "
        "Examples: 'Which items are running low?', 'Which products are out of stock?', "
        "'Show inventory added this month', 'Which supplier provided this item?', "
        "'Show all accessories related to Dell'."
    ),
)
async def inventory_query(req: QueryRequest, x_api_key: str = Header(default=None)):
    """Execute flexible inventory queries based on filter type."""
    _verify_api_key(x_api_key)

    base = """
        SELECT p.name AS product_name, p.sku, p.unit_price,
               c.name AS category, s.name AS supplier,
               w.name AS warehouse, w.city,
               i.quantity, i.reorder_level, i.last_restocked,
               CASE WHEN i.quantity = 0 THEN 'Out of Stock'
                    WHEN i.quantity <= i.reorder_level THEN 'Low Stock'
                    ELSE 'In Stock' END AS status
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        JOIN suppliers s ON p.supplier_id = s.id
        JOIN warehouses w ON i.warehouse_id = w.id
    """

    # Map filter_type to WHERE clause
    filter_map = {
        "low_stock":    ("WHERE i.quantity > 0 AND i.quantity <= i.reorder_level", []),
        "out_of_stock": ("WHERE i.quantity = 0", []),
        "by_supplier":  ("WHERE LOWER(s.name) LIKE LOWER(?)", [f"%{req.value or ''}%"]),
        "by_warehouse": ("WHERE LOWER(w.city) LIKE LOWER(?)", [f"%{req.value or ''}%"]),
        "by_category":  ("WHERE LOWER(c.name) LIKE LOWER(?)", [f"%{req.value or ''}%"]),
        "recent":       ("WHERE i.last_restocked >= date('now', '-30 days')", []),
    }

    if req.filter_type not in filter_map:
        return {"error": f"Invalid filter_type. Must be one of: {list(filter_map.keys())}", "results": [], "count": 0}

    where, params = filter_map[req.filter_type]
    query = f"{base} {where} ORDER BY p.name LIMIT ?"
    params.append(req.limit)

    results = await execute_query(query, tuple(params))
    return {
        "results": results,
        "count": len(results),
        "filter_applied": req.filter_type,
        "message": f"Found {len(results)} records matching '{req.filter_type}'" if results else f"No results for '{req.filter_type}' filter",
    }


# ---------- Tool 3: Inventory Analytics ----------

class AnalyticsRequest(BaseModel):
    metric: str = Field(
        ...,
        description=(
            "Analytics metric to compute. Must be one of: "
            "'highest_stock' (products with most stock), "
            "'lowest_stock' (products with least stock, excluding zero), "
            "'average_stock' (average quantity across all inventory), "
            "'top_n' (top N products by total stock), "
            "'category_distribution' (total stock per category), "
            "'warehouse_summary' (total stock per warehouse)"
        ),
    )
    limit: int = Field(default=10, description="Number of results for top_n and ranked queries")


@router.post(
    "/api/inventory/analytics",
    summary="Generate analytical insights from inventory data",
    description=(
        "Use this tool when the user wants AGGREGATE insights, statistics, or summaries — "
        "not individual product lookups. "
        "Examples: 'Which product has the highest stock?', 'What is the average stock level?', "
        "'Top 10 most available items', 'Which category occupies the most inventory?', "
        "'Give me a warehouse summary'."
    ),
)
async def inventory_analytics(req: AnalyticsRequest, x_api_key: str = Header(default=None)):
    """Compute inventory analytics and aggregations."""
    _verify_api_key(x_api_key)

    queries = {
        "highest_stock": (
            """SELECT p.name AS product_name, c.name AS category, SUM(i.quantity) AS total_stock
               FROM inventory i JOIN products p ON i.product_id = p.id JOIN categories c ON p.category_id = c.id
               GROUP BY p.id ORDER BY total_stock DESC LIMIT ?""",
            [req.limit],
        ),
        "lowest_stock": (
            """SELECT p.name AS product_name, c.name AS category, w.city AS warehouse, i.quantity
               FROM inventory i JOIN products p ON i.product_id = p.id JOIN categories c ON p.category_id = c.id
               JOIN warehouses w ON i.warehouse_id = w.id
               WHERE i.quantity > 0 ORDER BY i.quantity ASC LIMIT ?""",
            [req.limit],
        ),
        "average_stock": (
            "SELECT ROUND(AVG(quantity), 1) AS average_stock, COUNT(*) AS total_records FROM inventory",
            [],
        ),
        "top_n": (
            """SELECT p.name AS product_name, c.name AS category, s.name AS supplier,
                      SUM(i.quantity) AS total_stock
               FROM inventory i JOIN products p ON i.product_id = p.id
               JOIN categories c ON p.category_id = c.id JOIN suppliers s ON p.supplier_id = s.id
               GROUP BY p.id ORDER BY total_stock DESC LIMIT ?""",
            [req.limit],
        ),
        "category_distribution": (
            """SELECT c.name AS category, SUM(i.quantity) AS total_stock,
                      COUNT(DISTINCT p.id) AS product_count
               FROM inventory i JOIN products p ON i.product_id = p.id
               JOIN categories c ON p.category_id = c.id
               GROUP BY c.id ORDER BY total_stock DESC""",
            [],
        ),
        "warehouse_summary": (
            """SELECT w.name AS warehouse, w.city, SUM(i.quantity) AS total_stock,
                      COUNT(DISTINCT i.product_id) AS unique_products
               FROM inventory i JOIN warehouses w ON i.warehouse_id = w.id
               GROUP BY w.id ORDER BY total_stock DESC""",
            [],
        ),
    }

    if req.metric not in queries:
        return {"error": f"Invalid metric. Must be one of: {list(queries.keys())}", "results": []}

    query, params = queries[req.metric]
    results = await execute_query(query, tuple(params))

    return {"metric": req.metric, "results": results, "count": len(results)}


# ---------- Tool 4: Inventory Recommendation ----------

class RecommendationRequest(BaseModel):
    action: str = Field(
        ...,
        description=(
            "Recommendation action to perform. Must be one of: "
            "'reorder_check' (check if a specific product needs reordering), "
            "'low_stock_alert' (list all items that need restocking soon), "
            "'alternatives' (suggest alternative products in same category), "
            "'restock_priorities' (rank items by urgency of restocking)"
        ),
    )
    product_name: Optional[str] = Field(None, description="Product name (required for 'reorder_check' and 'alternatives')")


@router.post(
    "/api/inventory/recommendation",
    summary="Get intelligent inventory recommendations",
    description=(
        "Use this tool when the user asks for business RECOMMENDATIONS or SUGGESTIONS about inventory. "
        "Examples: 'Should we reorder Dell laptops?', 'Which products are likely to run out soon?', "
        "'Suggest items that need restocking', 'Recommend alternative products if this one is unavailable'."
    ),
)
async def inventory_recommendation(req: RecommendationRequest, x_api_key: str = Header(default=None)):
    """Generate inventory recommendations and business suggestions."""
    _verify_api_key(x_api_key)

    if req.action == "reorder_check":
        if not req.product_name:
            return {"error": "product_name is required for reorder_check", "recommendations": []}

        results = await execute_query(
            """SELECT p.name AS product_name, w.city AS warehouse, i.quantity, i.reorder_level,
                      i.last_restocked, s.name AS supplier, s.contact_email,
                      CASE WHEN i.quantity = 0 THEN 'URGENT — Out of stock, reorder immediately'
                           WHEN i.quantity <= i.reorder_level THEN 'RECOMMENDED — Stock below reorder level'
                           ELSE 'NOT NEEDED — Stock is sufficient' END AS recommendation
               FROM inventory i JOIN products p ON i.product_id = p.id
               JOIN warehouses w ON i.warehouse_id = w.id JOIN suppliers s ON p.supplier_id = s.id
               WHERE LOWER(p.name) LIKE LOWER(?)
               ORDER BY i.quantity ASC""",
            (f"%{req.product_name}%",),
        )
        return {"action": "reorder_check", "recommendations": results, "count": len(results)}

    elif req.action == "low_stock_alert":
        results = await execute_query(
            """SELECT p.name AS product_name, w.city AS warehouse, i.quantity, i.reorder_level,
                      s.name AS supplier, s.contact_email, i.last_restocked,
                      CASE WHEN i.quantity = 0 THEN 'CRITICAL' ELSE 'WARNING' END AS severity
               FROM inventory i JOIN products p ON i.product_id = p.id
               JOIN warehouses w ON i.warehouse_id = w.id JOIN suppliers s ON p.supplier_id = s.id
               WHERE i.quantity <= i.reorder_level
               ORDER BY i.quantity ASC, p.name"""
        )
        return {"action": "low_stock_alert", "recommendations": results, "count": len(results)}

    elif req.action == "alternatives":
        if not req.product_name:
            return {"error": "product_name is required for alternatives", "recommendations": []}

        results = await execute_query(
            """SELECT p2.name AS alternative_product, p2.unit_price, s.name AS supplier,
                      SUM(i.quantity) AS total_stock, c.name AS category
               FROM products p1
               JOIN products p2 ON p1.category_id = p2.category_id AND p1.id != p2.id
               JOIN categories c ON p2.category_id = c.id
               JOIN suppliers s ON p2.supplier_id = s.id
               LEFT JOIN inventory i ON p2.id = i.product_id
               WHERE LOWER(p1.name) LIKE LOWER(?)
               GROUP BY p2.id
               HAVING total_stock > 0
               ORDER BY total_stock DESC""",
            (f"%{req.product_name}%",),
        )
        return {"action": "alternatives", "product_searched": req.product_name, "recommendations": results, "count": len(results)}

    elif req.action == "restock_priorities":
        results = await execute_query(
            """SELECT p.name AS product_name, w.city AS warehouse,
                      i.quantity, i.reorder_level,
                      (i.reorder_level - i.quantity) AS deficit,
                      p.unit_price, s.name AS supplier,
                      CASE WHEN i.quantity = 0 THEN 1
                           WHEN i.quantity <= i.reorder_level * 0.5 THEN 2
                           ELSE 3 END AS priority_rank
               FROM inventory i JOIN products p ON i.product_id = p.id
               JOIN warehouses w ON i.warehouse_id = w.id JOIN suppliers s ON p.supplier_id = s.id
               WHERE i.quantity <= i.reorder_level
               ORDER BY priority_rank ASC, deficit DESC"""
        )
        return {"action": "restock_priorities", "recommendations": results, "count": len(results)}

    else:
        return {"error": f"Invalid action. Must be one of: reorder_check, low_stock_alert, alternatives, restock_priorities"}
