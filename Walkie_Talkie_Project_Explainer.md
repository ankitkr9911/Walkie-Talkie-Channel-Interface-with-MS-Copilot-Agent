# Walkie Talkie — Inventory Assistant
### A Plain-English Guide to What It Is, How It Works, and Why We Built It

---

## 1. The Problem We Were Trying to Solve

Imagine you are a warehouse manager at an Accenture client's facility. You are standing in the middle of a busy warehouse floor, hands full, and you need to quickly find out — *how many Dell laptops do we have left in the Hyderabad warehouse?* Or — *which items are about to run out of stock?*

The traditional way to get this answer involves logging into a desktop system, navigating menus, typing in filters, and reading through rows of data on a screen. That takes time. If you are on the move, it is even harder.

What if you could just *talk* to the inventory system, like you are talking to a colleague? Just say the question out loud, and get a clear, spoken answer back — instantly?

That is exactly what this project does.

**Walkie Talkie — Inventory Assistant** is a voice-first, AI-powered tool that lets anyone — technical or not — ask inventory questions by speaking or typing, and get smart, formatted answers both in text and as a spoken voice response. No menus, no filters, no training needed. You just ask, and it answers.

---

## 2. What Did We Actually Build?

We built a system with three main parts that work together like a well-coordinated team.

**Part 1 — The Screen (What You See)**

This is the webpage the user opens in a browser. It has a dark sidebar on the left with three options — Voice, Chat, and Audio Player. You click Voice and speak your question. You click Chat and type it. After the AI answers, you can go to the Audio Player section and replay the voice response as many times as you want, just like replaying a voice note.

**Part 2 — The Engine Behind the Scenes (The Server)**

This is the invisible part running on a server in the cloud. When you speak, it listens and converts your voice into text. It then passes that text question to the AI agent. When the AI agent responds, this engine converts the text response back into a spoken voice and sends both the text and the voice audio back to your screen. All of this happens in a matter of seconds.

**Part 3 — The AI Agent (Microsoft Copilot Studio)**

This is the actual "thinking" part of the system. It is a smart AI agent built on Microsoft's Copilot Studio platform. It receives the question in text form, understands what is being asked, reaches into the inventory database to fetch the right data, and crafts a clear, well-formatted answer — complete with tables, bullet points, and even restocking recommendations when needed.

---

## 3. The Big Picture — How Everything Connects

Think of it like placing an order at a restaurant.

You are the customer — you speak or type your question. The waiter is the backend server — it takes your order, relays it, and brings back what you asked for. The kitchen is the Microsoft Copilot Studio AI Agent — it does the actual thinking, understands the question, fetches data, and prepares the answer. And the pantry is the inventory database — the source of all the raw data the kitchen uses. You never talk to the kitchen directly. The waiter handles everything in between.

```
You speak or type a question
           ↓
      Your Screen (browser)
           ↓
    Backend Server (the engine)  ←─────────────────────────────┐
           ↓                                                    │
  MS Copilot Studio AI Agent                                    │
           ↓                                                    │
  Picks the right inventory tool ──→ Backend Server ──→ Database
           ↓
  AI writes a clear, formatted response
           ↓
  Backend converts it to voice audio
           ↓
  Your screen shows the text + plays the audio
```

---

## 4. The Journey of Your Voice — Step by Step

Let us walk through exactly what happens from the moment you speak to the moment you hear the answer.

---

### When You Use Voice (Tap to Talk)

**Step 1 — You Click the Voice Button and Speak**

You open the web app and click the microphone icon in the left sidebar. The button turns red with a pulsing glow — your microphone is now on and recording. You speak your question: *"How many Dell laptops are available?"* Then you click the button again to stop. The label changes to "Release to Send" when recording, so you always know the system is listening.

**Step 2 — Your Voice Is Sent to the Server**

The moment you click to stop, your audio recording is packaged up and sent over the internet to the backend server. The server is hosted on a cloud platform, so it is always running even when your laptop is off.

**Step 3 — Your Voice Is Converted to Text**

The server takes your audio and runs it through a speech-to-text conversion engine. This engine listens carefully and produces a written transcript. So your spoken *"How many Dell laptops are available?"* becomes the written sentence: `How many Dell laptops are available?`

This happens entirely on the server — no internet call is made, no outside service is contacted. It all runs locally on the server itself, so it works even in environments with strict network restrictions.

**Step 4 — The Text Question Is Sent to the AI Agent**

The written transcript is now sent over a secure private channel to the Microsoft Copilot Studio AI Agent. This private channel is always open between our server and the AI agent, so the message arrives instantly.

**Step 5 — The AI Agent Reads the Question and Decides What to Do**

The AI agent receives the question and understands it. It figures out the intent — what kind of information is being requested. In this case, it recognises that the user is asking about how many units of a specific product (Dell laptops) are in stock. It decides to use its product lookup capability.

**Step 6 — The AI Agent Contacts the Inventory Database**

The AI agent sends a request back to our backend server, asking it to search the inventory database for all records matching "Dell laptops." The backend opens the database, searches through all products whose name contains "Dell," and pulls back every matching record — including which warehouse it is in, how many units are available, and whether any are running low.

**Step 7 — The Raw Data Goes Back to the AI Agent**

All those raw records — numbers, warehouse names, stock levels, reorder thresholds — get returned to the AI agent. The AI now has everything it needs. It reads through all the records and writes a clear, human-friendly, nicely formatted response, for example:

> *"Here's a summary of Dell laptops currently available across all warehouses:*
>
> | Model | Total Stock | Status |
> |-------|-------------|--------|
> | Dell Inspiron 15 | 100 units | ✅ In Stock |
> | Dell Latitude 5440 | 135 units | ✅ In Stock |
> | Dell Latitude 7440 | 25 units | ⚠️ Low Stock |
>
> *Overall, there are 260 Dell laptops in stock. The Dell Latitude 7440 is running low in Mumbai (5 units) and Hyderabad (8 units) — you may want to consider restocking those."*

**Step 8 — The Response Travels Back to Our Server**

That formatted text response travels back from the AI agent through the private channel to our backend server.

**Step 9 — The Text Is Converted to a Spoken Voice**

The backend server takes the full text response and converts it into audio — a spoken voice. This also happens entirely on the server, using a voice engine that runs offline with no internet connection needed. The voice sounds natural and clear.

**Step 10 — Everything Is Sent Back to Your Screen**

The backend bundles up three things and sends them back to your browser in one go:
- The **transcript** of what you said, so you can confirm the system heard you correctly
- The **text response** from the AI, with full formatting — tables, bold text, bullet points, emojis
- The **voice audio** of the response, ready to play

**Step 11 — You See It and Hear It**

Your screen updates. The chat window shows the bot's response with rich formatting. At the same time, the voice response plays automatically through your speakers. If you missed any of it, you can click the Audio Player tab in the sidebar and replay it as many times as you like — just like a song.

---

### When You Use Chat (Type a Question)

This works exactly the same way, except the first three steps are skipped entirely. You type your question, and it goes straight to the AI agent. The AI answers, the answer is converted to voice, and you see the text and hear the audio — same as before.

---

## 5. What Can the AI Agent Answer?

The AI agent is specifically built to handle inventory-related questions. It has four capabilities — think of them as four different departments it can reach into.

---

### Capability 1 — Specific Product Lookup

**Use this when you want to know about a particular product.**

- *"How many Dell laptops are in stock?"*
- *"Do we have HP EliteBooks available in Bangalore?"*
- *"Show me all monitors under ₹20,000."*

The AI searches the database for that exact product, applies any filters you mentioned (warehouse, price range, category), and returns every matching record.

---

### Capability 2 — Broad Inventory Queries

**Use this when you want to browse by a condition rather than a product name.**

- *"Which items are running low?"*
- *"What is out of stock in Mumbai?"*
- *"Show me everything from the Dell supplier."*
- *"What was restocked in the last 30 days?"*

The AI applies the right filter to the entire database and returns the matching results.

---

### Capability 3 — Analytics and Statistics

**Use this when you want a summary or ranking rather than a list.**

- *"Which category has the most inventory?"*
- *"What is the average stock level across all products?"*
- *"Give me a warehouse summary."*
- *"Top 10 most stocked items."*

The AI runs a calculation across the full database and returns aggregated numbers rather than individual product records.

---

### Capability 4 — Recommendations

**Use this when you want advice or suggestions, not just data.**

- *"Should we reorder Dell laptops?"*
- *"Which products are most urgently in need of restocking?"*
- *"Suggest alternatives if ThinkPad X1 Carbon is unavailable."*

The AI compares current stock against reorder thresholds, figures out which items are most critical, and returns a prioritised list. Priority 1 means order immediately (out of stock). Priority 2 means critically low. Priority 3 means approaching the reorder level.

---

### What the AI Will Not Answer

The AI agent has guardrails built in. If you ask anything outside inventory — like *"What's the weather today?"* or *"Write me an email"* — it politely declines and tells you what it can help with instead. It never goes off-topic. And if your question is too vague — like *"Show me everything"* — it asks a follow-up question to narrow things down rather than guessing.

---

## 6. The Challenges We Hit and How We Fixed Them

Building this system was not straightforward. Here are the real problems we ran into, explained in plain terms, and exactly how we solved each one.

---

### Challenge 1 — The AI Agent Kept Saying "Authentication Not Configured"

**What happened:** Every time our server sent a question to the AI agent, instead of getting an answer back, we got an error message saying *"Authentication Not Configured."* The AI agent was refusing to talk to us.

**Why it happened:** Inside Microsoft Copilot Studio, there is a setting that controls how the agent handles user logins. Our organisation's IT policy had locked down the simplest option — the one that allows the agent to accept questions from anyone without requiring a login. So the agent was stuck in a half-configured state where it was trying to enforce a login system that had not been set up. Every question got rejected.

On top of this, the tools the AI agent uses to query our inventory database were set to "End User Credentials" — meaning the agent expected each individual user to have their own personal login for the database. Since our database uses a single shared access key (not per-user logins), this was completely wrong.

**How we fixed it:** We made two changes in Copilot Studio. First, we changed the authentication setting to "Authenticate manually" with the "Require users to sign in" toggle turned OFF. This keeps the IT policy satisfied while allowing the agent to accept questions without demanding individual logins. Second, we changed all four inventory tools from "End User Credentials" to "Maker-provided credentials" — meaning the agent uses our single shared access key automatically, without expecting anything from the user. Once both changes were made and the agent was republished, it started responding perfectly.

---

### Challenge 2 — The Spoken Voice Output Was Completely Silent (Network Block)

**What happened:** After the AI gave a text response, our server was supposed to convert it to a spoken voice and send it to the user. But the voice conversion was failing every single time. Users would see the text but hear nothing.

**Why it happened:** Our original voice engine worked by connecting to a Microsoft cloud service over the internet. Accenture's corporate network has a security system (called Forcepoint) that blocks certain types of internet connections. The connection type used by Microsoft's cloud speech service was among those being blocked. Every attempt to convert text to voice got stopped by the network firewall.

**How we fixed it:** We switched to a completely different voice engine — one that runs entirely on the server itself, with no internet connection needed. It uses a pre-downloaded voice model file (about 63 megabytes) that lives on the server. When text needs to be converted to speech, it reads the text and generates the audio using that local file — no network calls, nothing for the firewall to block. For the cloud server where this file does not exist by default, we added a step that automatically downloads it the first time the server starts up.

---

### Challenge 3 — The Voice Recording Button Did Nothing

**What happened:** Users would click the microphone button to start recording, and nothing happened. No recording, no response.

**Why it happened:** The original design required users to press and hold the button while speaking — like a walkie-talkie. But people naturally just clicked it once and let go. A single click triggers the start and stop of recording almost at the same time, producing an audio clip so short that the system treated it as an accidental click and threw it away. From the user's perspective, nothing happened at all.

**How we fixed it:** We changed it to a toggle. One click starts recording — the button turns red and the label changes to "Release to Send." The user speaks at their own pace. Another click stops the recording and sends it. This is far more natural and matches how voice interfaces work on smartphones.

---

### Challenge 4 — The AI Agent Was Confused About the Access Key

**What happened:** Our inventory tools were not being called correctly — the AI was confused about how to authenticate the requests it was sending to our database.

**Why it happened:** The blueprint document we gave the AI agent (which tells it how to use the inventory tools) had a mistake. The access key that protects our database was defined in two places — once correctly as an automatic security setting, and once incorrectly as a regular input field that the AI was expected to fill in. The AI could not decide which one to use, causing the tool calls to fail.

**How we fixed it:** We cleaned up the blueprint to remove the duplicate. The access key now only appears in the correct place — as a background setting that gets applied automatically every time the AI calls an inventory tool. The AI itself never has to think about it.

---

### Challenge 5 — Audio Files Would Not Process on Some Windows Machines

**What happened:** Voice recordings made in the browser would sometimes fail to process on Windows machines, with a confusing error about file paths.

**Why it happened:** Windows has an old quirk where folder names with certain characters can get automatically shortened into an older format (e.g., a folder named `a.aq.kumar` might silently become `AAQ~1.KUM`). Our audio processing library would try to open the recording file using this shortened path and fail.

**How we fixed it:** Instead of telling the audio processing library to open a file by its path, we first read the entire file into the server's memory and then passed the in-memory data directly to the library. No file path is involved, so the Windows shortening quirk has nothing to interfere with. The audio processes correctly every time.

---

## 7. The Complete Data Flow in One View

Here is the full journey of a question from the moment you open your mouth to the moment you hear the answer.

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR SCREEN                              │
│  Voice mode: Click mic → speak → click again to send           │
│  Chat mode:  Type question → press Enter                        │
└────────────────────┬────────────────────────────────────────────┘
                     │  Audio file (Voice) OR Text (Chat)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND SERVER                             │
│                                                                 │
│  [Voice path only]                                              │
│  → Converts audio to text  (offline, no internet needed)        │
│                                                                 │
│  → Sends text question to MS Copilot Studio AI Agent            │
└────────────────────┬────────────────────────────────────────────┘
                     │  Text question
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              MS COPILOT STUDIO AI AGENT                         │
│                                                                 │
│  Reads the question, understands intent, picks the right tool:  │
│                                                                 │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────┐  ┌───────┐  │
│  │Product Lookup│  │Broad Queries│  │ Analytics  │  │Recomm.│  │
│  └──────────────┘  └─────────────┘  └────────────┘  └───────┘  │
│                                                                 │
│  → Sends request to Backend to query the database               │
└────────────────────┬────────────────────────────────────────────┘
                     │  Tool request (e.g., "look up Dell laptops")
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND SERVER                             │
│                                                                 │
│  → Opens the inventory database                                 │
│  → Runs the search or calculation                               │
│  → Returns raw records back to the AI Agent                     │
└────────────────────┬────────────────────────────────────────────┘
                     │  Raw database records (numbers, names, etc.)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              MS COPILOT STUDIO AI AGENT                         │
│                                                                 │
│  Reads the raw data, writes a clear, formatted response         │
│  (with tables, bold text, emojis, recommendations as needed)    │
│  → Sends formatted response back to Backend                     │
└────────────────────┬────────────────────────────────────────────┘
                     │  Formatted text response
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND SERVER                             │
│                                                                 │
│  → Converts text response to spoken audio (offline)             │
│  → Sends back to your screen:                                   │
│      • What you said (transcript)                               │
│      • The AI's text response (with full formatting)            │
│      • The AI's voice response (audio file)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │  Text + Audio
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR SCREEN                              │
│                                                                 │
│  Chat window shows the formatted response (tables, lists, etc.) │
│  Speaker plays the voice response automatically                  │
│  Audio Player tab lets you replay it anytime                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. What Goes In and What Comes Out

| Stage | What Goes In | What Comes Out |
|-------|-------------|----------------|
| You speak | A few seconds of voice audio | — (sent to server) |
| Voice → Text | Audio file (webm format) | Your question as written text |
| Text → AI Agent | Your question as a string of words | A request to query the database |
| Database Search | A search (e.g., "Dell laptops") | A list of raw inventory records |
| AI Formats Answer | Raw numbers, names, warehouse data | A nicely written response with tables |
| Text → Voice | The AI's written response | An audio file (WAV format) |
| Final delivery | Text + Audio | What appears on screen + what you hear |

---

## 9. The Inventory Database

The database holds all the information the AI draws from when it answers your questions.

- **Products** — 20 products with names, descriptions, prices, and which category and supplier they belong to
- **Warehouses** — four locations: Bangalore, Mumbai, Delhi, and Hyderabad
- **Inventory records** — 48 records tracking how many units of each product are in each warehouse, when it was last restocked, and the minimum level before restocking should happen
- **Suppliers** — names and contact details for each product's supplier
- **Categories** — Laptops, Monitors, Accessories, Desktops, Networking

All of this data comes pre-loaded when the system starts up, so the AI is immediately ready to answer questions without any manual data entry.

---

## 10. Technology Used

This is the only technical section of this document — a quick summary of the tools and technologies that make this system run.

| Component | Technology | What It Does |
|-----------|-----------|--------------|
| Web interface | React + Vite | The website the user interacts with in a browser |
| Styling | Vanilla CSS | Makes the website look premium and polished |
| Backend server | FastAPI (Python) | The engine that handles all behind-the-scenes logic |
| Database | SQLite | Stores all inventory data |
| Speech-to-Text | Faster-Whisper | Converts voice recordings to text (runs offline) |
| Text-to-Speech | Piper TTS | Converts text responses to spoken audio (runs offline) |
| AI Agent | Microsoft Copilot Studio | The AI brain that understands questions and fetches data |
| AI Communication | Direct Line (Microsoft Bot Framework) | Private channel between our server and the AI agent |
| Cloud Hosting | Render | Keeps the backend server always running online |
| Markdown Rendering | React Markdown + remark-gfm | Displays AI responses with proper tables and formatting |

---

## 11. The API Connections — Briefly

There are two sets of "doors" (called API endpoints) that the system uses to move information around.

**Doors that the user's browser talks to:**

- `/api/voice` — Send in a voice recording → get back the transcript, the AI's text response, and the AI's spoken response
- `/api/chat` — Send in a typed question → get back the AI's text response and spoken response

**Doors that the AI Agent talks to (to query the database):**

- `/api/inventory/lookup` — Look up stock for a specific named product
- `/api/inventory/query` — Run a filter (low stock, out of stock, by warehouse, by supplier, etc.)
- `/api/inventory/analytics` — Get statistics and summaries (highest stock, warehouse totals, category breakdowns)
- `/api/inventory/recommendation` — Get restocking advice and reorder priorities

The AI agent knows which door to use for which question because we gave it a blueprint document that describes exactly what each door does. The AI reads this blueprint and makes the right choice automatically based on what you asked.

---

## 12. Wrapping Up

What we have built is a voice-first AI assistant for inventory management — the kind of capability you would normally expect only in large, expensive enterprise software, now working through a simple webpage that anyone can open in a browser on any device.

The user does not need to know how any of this works. They just talk. Or they type. The system figures out the rest — converting their words, routing the question to the right capability, fetching the exact data needed, and delivering a clear, spoken, and well-formatted answer.

No training. No menus. No filters. Just questions and answers.

The system is fully working in its current form — covering all four inventory capabilities across four warehouses, with full voice input and output, markdown-formatted chat responses, and a replayable audio player for every response.

---

*Walkie Talkie — Inventory Assistant*
*Built using Microsoft Copilot Studio, FastAPI, Piper TTS, and Faster-Whisper*
