---
version: alpha
name: ChatGPT Minimal
description: A restrained, high-clarity conversational interface with soft surfaces, dark text, and subtle borders.
colors:
  primary: "#0D0D0D"
  secondary: "#6B7280"
  tertiary: "#E5E7EB"
  neutral: "#FFFFFF"
  surface: "#FFFFFF"
  on-surface: "#0D0D0D"
  error: "#D92D20"
  border: "#E5E7EB"
  muted: "#F3F4F6"
typography:
  headline-display:
    fontFamily: "-apple-system-body"
    fontSize: "40px"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "0px"
  headline-lg:
    fontFamily: "-apple-system-body"
    fontSize: "24px"
    fontWeight: 400
    lineHeight: "28px"
    letterSpacing: "0.07px"
  headline-md:
    fontFamily: "-apple-system-body"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: "26px"
    letterSpacing: "0px"
  headline-sm:
    fontFamily: "-apple-system-body"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: "24px"
    letterSpacing: "0px"
  body-lg:
    fontFamily: "-apple-system-body"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: "28px"
    letterSpacing: "0px"
  body-md:
    fontFamily: "-apple-system-body"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "24px"
    letterSpacing: "0px"
  body-sm:
    fontFamily: "-apple-system-body"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "20px"
    letterSpacing: "0px"
  label-lg:
    fontFamily: "-apple-system-body"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "20px"
    letterSpacing: "0px"
  label-md:
    fontFamily: "-apple-system-body"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "18px"
    letterSpacing: "0px"
  label-sm:
    fontFamily: "-apple-system-body"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: "16px"
    letterSpacing: "0px"
  caption:
    fontFamily: "-apple-system-body"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: "16px"
    letterSpacing: "0px"
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 16px
  xl: 24px
  full: 9999px
spacing:
  xs: 2px
  sm: 10px
  md: 16px
  lg: 20px
  xl: 24px
  2xl: 60px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
    typography: "{typography.label-md}"
    rounded: "{rounded.full}"
    padding: "11px 12px"
    height: "36px"
  button-secondary:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-md}"
    rounded: "{rounded.full}"
    padding: "11px 12px"
    height: "36px"
  button-tertiary:
    backgroundColor: "transparent"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.none}"
    padding: "0px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "16px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.full}"
    padding: "12px 16px"
    height: "52px"
  chip:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.full}"
    padding: "8px 12px"
---

# ChatGPT Minimal

## Overview
This interface feels calm, utilitarian, and highly polished, with a strong emphasis on speed and clarity over decoration. It is designed for a broad audience: casual users entering a prompt, plus returning users navigating chat history and account actions. The tone is professional but approachable, with spacious white areas and very light visual weight so the content stays dominant.

## Colors
- **Primary (#0D0D0D):** A near-black ink used for the main brand mark, primary buttons, headings, and essential text. It gives the interface crisp contrast without feeling harsh.
- **Secondary (#6B7280):** A soft gray for de-emphasized navigation and supporting copy when needed. It should remain clearly readable but never compete with the main prompt area.
- **Tertiary (#E5E7EB):** A delicate border gray used for outlines, dividers, and subtle button edging. This keeps surfaces distinct while preserving the minimal look.
- **Neutral / Surface (#FFFFFF):** The dominant canvas color across the app, including the main workspace, side rail, cards, and buttons. The system relies on white space rather than colored panels to create separation.
- **Muted (#F3F4F6):** A gentle neutral fill for hover states, chips, and low-emphasis backgrounds. It adds affordance without introducing visual noise.
- **Error (#D92D20):** A reserved alert color for destructive actions and validation feedback. It should be used sparingly so the rest of the interface stays serene.
- **Border (#E5E7EB):** The primary structural line color for cards, inputs, and button outlines. Borders are thin and understated, supporting the flat aesthetic.

## Typography
The system uses the platform-native `-apple-system-body` stack, which keeps the interface familiar, highly legible, and fast-loading. Headings are lightweight rather than bold; even large titles remain regular-weight, which reinforces the quiet, editorial feel.

`headline-display`, `headline-lg`, `headline-md`, and `headline-sm` are used for page-level messaging and state text such as “Ready when you are.” They stay compact and restrained, with modest line heights and almost no letter spacing.

`body-md` and `body-lg` are the main reading sizes for descriptive content, sidebar copy, and legal text. `body-sm` and `caption` support utility text, while `label-md` and `label-sm` are used for controls like buttons, nav items, and compact input affordances.

Uppercase styling is not a visible pattern here. Letter spacing is minimal and generally neutral, which keeps the tone direct and conversational.

## Layout & Spacing
The layout is a fixed-sidebar plus expansive main canvas structure. The sidebar is narrow and vertically stacked, while the main area uses large open space to center the primary interaction around the prompt composer.

Spacing follows a sparse, breathable rhythm rather than a dense grid. The most visible increments cluster around 10px, 16px, 20px, 24px, and 60px, which creates clear hierarchy between navigation items, the hero message, the input bar, and footer/legal content.

Cards and controls rely on modest internal padding, typically 12px to 16px, with broader spacing reserved for whole-section separation. This system should prefer generous outer whitespace and compact control padding to keep the experience feeling efficient.

## Elevation & Depth
Depth is intentionally flat. There are no noticeable shadows, and hierarchy comes from contrast, borders, and placement rather than stacked layers.

Inputs and cards use thin borders and subtle tonal shifts instead of raised surfaces. This keeps the interface clean and reduces visual friction, which suits a utility-first conversational product.

## Shapes
The shape language is soft and highly rounded. Primary actions, inputs, and pill-like controls use `rounded.full`, while cards use modest `rounded.md` corners.

This creates a gentle, approachable feel without becoming playful. Straight edges are reserved for links and some text-based affordances, which helps keep the interface crisp.

## Components
**Buttons**
- Use `button-primary` for the strongest action. It is a black pill with white text, compact height, and no shadow.
- Use `button-secondary` for secondary account or utility actions. It mirrors the primary button’s pill shape but uses a white fill with a light border.
- Use `button-tertiary` for text-like actions where a button frame would feel too heavy.
- Button sizing is compact: roughly 36px tall with tight horizontal padding. This keeps the header and sidebar actions unobtrusive.
- Hover and focus states should remain subtle: prefer border or fill shifts over motion-heavy effects.

**Inputs**
- Use `input` for the main prompt composer and other text entry fields. It should be wide, pill-shaped, white, and lightly bordered.
- Placeholder text should be medium gray and concise.
- The input should feel integrated into the page rather than floating above it.

**Cards**
- Use `card` for panels, prompts, and content containers that need separation from the white background.
- Cards should remain flat with a thin border and 8px radius.
- Internal padding should stay around 16px, with generous gaps around the card rather than within it.

**Chips**
- Use `chip` for compact toggles, contextual labels, and secondary actions.
- Chips should be soft, muted, and pill-shaped to match the broader rounded language.

**Navigation items**
- Sidebar items should be low-contrast, icon-led rows with clear hover affordance.
- Active or primary navigation can be indicated with a muted background rather than a strong accent block.

**Links and legal text**
- Links should stay underlined and text-forward.
- Footer/legal copy should be small, quiet, and centered or minimally offset, never competing with the main prompt area.

## Do's and Don'ts
- Do keep the UI mostly white with black text and very light gray structural borders.
- Do use rounded pills for high-frequency actions like login, signup, and the composer.
- Do rely on spacing and placement for hierarchy instead of shadows or colorful panels.
- Do keep typography regular-weight and highly legible, with minimal stylistic flourish.
- Don't introduce heavy gradients, rich textures, or pronounced elevation.
- Don't make primary controls tall, square, or visually loud.
- Don't overload the sidebar with dense information or nested chrome.
- Don't use saturated accent colors unless they are reserved for errors or critical alerts.