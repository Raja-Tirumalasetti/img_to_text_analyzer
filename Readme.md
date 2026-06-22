# AI-Powered Context-Aware Content Moderation System

A premium, highly responsive, and context-aware content moderation web application styled with a modern Facebook-inspired theme. This system evaluates the semantics and intent of statements instead of relying solely on crude keyword blacklists.

## New Facebook‑Styled Moderation UI

The project now includes a lightweight, Facebook‑inspired moderation interface that:
- Lets you type a single sentence (or multiple lines) and click **Check**.
- Shows an immediate ✅ (approved) or ❌ (flagged) badge with a short reason.
- Processes requests asynchronously, so you can continue typing while previous checks are running.
- Uses the Gemini model with a custom system prompt that only flags profanity when it targets a person or group.

### How to run locally
1. Open `index.html` in a browser (no build step required).
2. Enter your text in the composer box and press **Enter** or click the **Check** button.
3. Watch the feed update with a card showing the result and the decision reasoning.

Feel free to customize the theme colors in `styles.css` or adjust the system prompt in `app.js` under the `DEFAULT_SYSTEM_INSTRUCTION` constant.

## Features

1. **Context-Aware Decisions**: Evaluates intent, target, and severity. Differentiates between casual profanity (approved) and targeted abuse (flagged).
2. **Facebook Inspired UI/UX**: Clean layout containing a top header bar, left navigation controls, middle composer and live feed, and right statistics dashboard.
3. **Asynchronous Non-Blocking Processing**: Queue-based request execution allowing developers/moderators to submit multiple prompts simultaneously.
4. **Theme Customization**: Toggle seamlessly between Light Mode and Dark Mode.
5. **Prompt Injection Resistance**: Neutralizes adversarial attempts to override safety filters.
6. **Detailed Audit logs**: Full-featured logs dashboard to search, sort, filter, and drill down into evaluation parameters (IDs, reasoning, execution times).

## Project Structure

- `index.html`: The structural foundation of the Facebook-inspired application.
- `styles.css`: Premium styling with CSS variable themes (Light/Dark), responsive layout, and transitions.
- `app.js`: Moderation queue system, Gemini API integration (with structured JSON schemas), event handlers, and LocalStorage caches.
- `instructions.md`: Rules and categories of evaluation.
- `isto.md` (DOS_AND_DONTS.md): Development best practices and testing guidelines.
- `crediental.md`: The Google Gemini API key used by the application.

## Getting Started

### Local Setup
Since the application is built entirely as a static web application using standard vanilla HTML, CSS, and modern JavaScript, there are no complex installation dependencies. You can run it directly:

1. Open `index.html` in any modern web browser (Double-click or drag-and-drop the file).
2. Alternatively, run a lightweight local dev server if you prefer (e.g. `npx live-server` or VS Code Live Server extension).

### API Configuration
- The system includes a default Gemini API key retrieved from `crediental.md`.
- You can change or view the key, model selector (`gemini-2.5-flash` or `gemini-3.5-flash`), and customize system rules in the **System Settings** tab inside the web app.
