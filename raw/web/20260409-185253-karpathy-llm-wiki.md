# Web Search Capture

- query: karpathy llm wiki
- captured_at: 20260409-185253
- provider: tavily

## Tavily Answer
Karpathy's LLM Wiki is a personal knowledge management system using structured markdown files queried by an AI. It's designed for easy access by AI, not humans. It uses tools like Obsidian for visualization.

## Results
### 1. What Is Andrej Karpathy's LLM Wiki? How to Build a Personal ...
- url: https://www.mindstudio.ai/blog/andrej-karpathy-llm-wiki-knowledge-base-claude-code/
- score: 0.8976

### What exactly is Karpathy’s LLM wiki?

It’s a personal knowledge management system built on plain markdown files, designed to be queried by an LLM rather than browsed manually. Andrej Karpathy has advocated for storing notes in a structured, LLM-readable format so that coding agents like Claude Code can answer questions, synthesize information, and help manage the knowledge base directly. The core insight is that organizing information for a model to read is different — and in many ways simpler — than organizing it for human navigation.

### How is this different from just using Notion AI or ChatGPT? [...] ## Key Takeaways

 Karpathy’s LLM wiki is a simple pattern: structured markdown files, queried by Claude Code through natural language
 Plain markdown is the right format because it’s portable, future-proof, and something LLMs read natively
 Obsidian is the best front-end for managing the files — your data stays local and file-based
 Claude Code connects to your local filesystem directly, no copy-pasting required
 A summary line and consistent tags on each note dramatically improve query quality
 For team-facing or scaled knowledge bases, MindStudio can wrap the same concept in a shareable, no-code agent with a proper UI [...] He calls it an LLM wiki. The concept is straightforward. Instead of scattering knowledge across Notion, Google Docs, browser bookmarks, and sticky notes, you keep everything as structured markdown files. Then you point Claude Code (or any capable coding agent) at that folder and ask it questions. The LLM reads your files, finds what’s relevant, and gives you grounded answers drawn from your own knowledge — not the general internet.

This isn’t a product. It’s a workflow pattern. And it’s one of the most practical applications of Claude Code that most people haven’t tried yet.

This guide explains how Karpathy’s LLM wiki works, why markdown is the right format for it, and how to get a working version running with Obsidian in about five minutes.

### 2. Llm wiki by karpathy : r/LocalLLaMA - Reddit
- url: https://www.reddit.com/r/LocalLLaMA/comments/1sclfs6/llm_wiki_by_karpathy/
- score: 0.8495

`npx add-skill Astro-Han/karpathy-llm-wiki`

No embeddings, no vector DB. At the scale Karpathy described (~400K words), the LLM handles its own indexing fine through summary files. The bottleneck isn't retrieval, it's keeping the wiki consistent as new sources come in. The linting step helps with that.

Image 10: u/Fearless_Fennel3666 avatar

Fearless_Fennel3666

•2d ago

the core is how you parse your docuemts(pdf,doc,pptx,md,...) and feed to LLM,

More replies

Image 11: u/knlgeth avatar

knlgeth

•2d ago

Went back to see Karpathy's X post and found a recently launched product which is similar to his idea of LLM Knowledge Bases, what do you think of this?

Github repo: 

X comment reference: 

Image 12: u/Worried_Bench1554 avatar

Worried_Bench1554

•1d ago [...] # Llm wiki by karpathy : r/LocalLLaMA
Skip to main contentLlm wiki by karpathy : r/LocalLLaMA

Open menu Open navigation draw upon the primary RAG database to respond to the synthetic prompts. Those responses then go into the preferred database.

It doesn't take advantage of the responses inferred by the "fast" model interacting with the user, though. Karpathy might be on to something, there. I'm going to noodle on it.

Image 9: u/Astro-Han avatar

Astro-Han

•3d ago

I went the other direction from RAG. Just a skill file for Claude Code that does the compile/query/lint loop from the gist.

`npx add-skill Astro-Han/karpathy-llm-wiki`

### 3. Karpathy's LLM Wiki – How Teachers Can Use It - TrainingSites
- url: https://trainingsites.io/tutorial/karpathys-llm-wiki-how-teachers-can-use-it/
- score: 0.8406

## What Is Karpathy’s LLM Wiki?

The idea is simple: take all the “digital exhaust” sitting on your computer — videos, PDFs, Google Docs, transcripts, notes, images — and use an AI like Claude to convert it into a structured, visual knowledge base called a wiki.

The tool that makes it visual is Obsidian — free software that displays your notes and documents as an interconnected graph. Think of it like a map of everything you know, where related topics are connected by lines.

> “If we could have Obsidian running on our local computer, it would be a really good way for us to see it — but also to have a wiki created locally with large language models like Claude to create a personal wiki.” — James [...] ⚠️ Important: Don’t skip the customer-facing layer because the wiki feels easier to set up. A beautiful personal wiki that your students can’t access doesn’t improve their learning outcomes.

## Key Takeaways

 Karpathy’s LLM Wiki uses Obsidian + Claude to organize your digital exhaust into a visual, queryable local knowledge base — free to set up.
 The wiki is powerful for personal use (your Claude desktop app) but students can’t access it.
 The educator-ready solution is a two-layer model: personal wiki for you, published tutorials + RAG for your campus.
 The deciding question is simple: who’s consuming the content — you, or your students?

## Next Steps [...] Campus Builders Campus Builders

 Login / Signup

#### START HERE

#### STUDY HALLS

#### LIVE LABS & SPRINTS

#### RESOURCES & SUPPORT

#### COACHING & SERVICES

# Karpathy’s LLM Wiki – How Teachers Can Use It

# Karpathy's LLM Wiki - How Teachers Can Use It

Knowledge Systems 💡 Concept Tutorial ↺ 11 min Apr 7, 2026

## What You’ll Learn

Andrej Karpathy’s LLM Wiki idea went viral for a reason — it solves a real problem: years of digital files scattered across your hard drive with no easy way to search or reference them. In this tutorial, you’ll understand exactly what the LLM Wiki is, why it’s a powerful personal tool, and — critically — what it can and can’t do for your students. You’ll also see the two-layer model James uses at trainingsites.io that solves this for educators.

### 4. LLM Wiki Revolution: How Andrej Karpathy's Idea Is Changing AI
- url: https://www.analyticsvidhya.com/blog/2026/04/llm-wiki-by-andrej-karpathy/
- score: 0.8358

## Conclusion

The most important advice for building your first LLM wiki is the same advice Karpathy gives in his gist: don’t overthink the setup. The schema template from this guide can be easily copied after which you can create the directory structure by executing the bash commands.

The system achieves its magical effect through multiple architectural improvements which develop from the first day onwards. The wiki becomes more valuable with each new source material you include. The data belongs to you. The files exist in formats which can be used by any system. You can use any AI you want to query it. The LLM takes care of all maintenance tasks instead of you needing to handle them which creates a different experience from other productivity tools. [...] When you add a new document source to the LLM, the LLM does not merely create an index of that source for later retrieval. Instead, the LLM reads, understands, and integrates that source into the knowledge base, updating all relevant existing pages (where necessary). It notes down any contradictions between the new and existing claims or knowledge, creating any necessary new concept pages, and reinforcing the complex relationships across the entire wiki.

According to Karpathy, “With LLMs, knowledge is created and maintained continuously and consistently rather than being able to use individual queries to create knowledge.” Here is a simple comparison that illustrates this difference further. [...] 1.   Building an LLM-powered wiki is difficult:It involves multiple challenges across setup, structure, and long-term maintenance.
2.   Prompt engineering is the first challenge:You need clear instructions for structuring pages, deciding when to create vs update them, and resolving conflicting information, which requires iteration and refinement.
3.   Scalability is a hidden factor:Simple setups break down beyond a few hundred pages, so you need tagging, folders, and search systems planned in advance.
4.   Consistency over time matters:Without regular maintenance, your wiki will accumulate outdated information, contradictions, and orphaned pages.

### 5. We Took Karpathy's LLM Wiki and Wired It to the Live Web - Nimble
- url: https://www.nimbleway.com/blog/we-took-karpathys-llm-wiki-and-wired-it-to-the-live-web
- score: 0.8149

## Tech/AI: The Karpathy LLM Wiki Ecosystem

I wanted to understand the full picture: Obsidian, Karpathy, and what happened when the gist went viral.

What Nimble found:

 Obsidian: bootstrapped, $25M ARR, $350M valuation, 9 employees (3 engineers)
 Karpathy's path: OpenAI co-founder → Tesla AI director → Eureka Labs → LLM Wiki
 The viral moment: 5K stars in 48hrs, X trending, dozens of repos, Steph Ango responded
 Enterprise adoption: LinkedIn built a coding agent knowledge base (20% adoption lift), Shopify CEO ran the AutoResearch pattern overnight

Result: 101 cross-linked wiki pages: 35 companies, 16 people, 14 events, 13 concepts, 7 projects.

## Healthcare: The GLP-1 Drugs Market

Completely different domain. Same approach. It all starts with one prompt in Claude Code: [...] Before, LLMs had to start from scratch with every new query. Now, they get a head start.

# What we built

Karpathy designed the wiki layer. We built the data layer that feeds it. Our integration with Obsidian simplifies and accelerates the web search process needed to feed the wiki.

We just shipped this as the memory architecture for our open-source Nimble Web Search Skills. You run a skill (i.e. competitor intel, meeting prep, company research) and it doesn't just search the live web and generate reports, it digests and organizes the results straight into a structured, linked wiki

Importantly, these wikis aren't just lists of pages. The content is intelligently mapped and continuously updated to make it easy for LLMs to understand the relationship between the various information. [...] And each run makes the next one smarter. Yesterday's research enriches today's queries. Over time you end up with your own Private Web Index.

The stack is simple:

`Nimble (search + extract)    →  live web data`

`↓`

`LLM (compile + cross-link)   →  wiki pages`

`↓`

`Obsidian (navigate + graph)  → human layer`

 Nimble searches the live web, such as news, social, financial data, company pages, and forums, and extracts clean markdown.
 The LLM compiles it into cross-linked wiki pages with dates, sources, and entity relationships.
 Obsidian renders the whole thing with its graph view, you see every connection, every entity, every trail.

All local. All yours. Plain markdown files.

‍

# We built two indexes from scratch to prove it works

## Tech/AI: The Karpathy LLM Wiki Ecosystem
