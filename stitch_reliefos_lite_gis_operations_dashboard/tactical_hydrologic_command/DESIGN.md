---
name: Tactical Hydrologic Command
colors:
  surface: '#051423'
  surface-dim: '#051423'
  surface-bright: '#2c3a4b'
  surface-container-lowest: '#010f1e'
  surface-container-low: '#0e1d2c'
  surface-container: '#122130'
  surface-container-high: '#1d2b3b'
  surface-container-highest: '#283646'
  on-surface: '#d5e4f9'
  on-surface-variant: '#bbcac4'
  inverse-surface: '#d5e4f9'
  inverse-on-surface: '#233241'
  outline: '#85948f'
  outline-variant: '#3c4a46'
  surface-tint: '#4ddcc1'
  primary: '#4ddcc1'
  on-primary: '#00382e'
  primary-container: '#20bfa5'
  on-primary-container: '#00483c'
  inverse-primary: '#006b5b'
  secondary: '#61d4ff'
  on-secondary: '#003545'
  secondary-container: '#01a0c9'
  on-secondary-container: '#00313f'
  tertiary: '#ffb3b1'
  on-tertiary: '#650713'
  tertiary-container: '#ff8786'
  on-tertiary-container: '#7a1920'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ff9dd'
  primary-fixed-dim: '#4ddcc1'
  on-primary-fixed: '#00201a'
  on-primary-fixed-variant: '#005144'
  secondary-fixed: '#bce9ff'
  secondary-fixed-dim: '#61d4ff'
  on-secondary-fixed: '#001f29'
  on-secondary-fixed-variant: '#004d63'
  tertiary-fixed: '#ffdad8'
  tertiary-fixed-dim: '#ffb3b1'
  on-tertiary-fixed: '#410007'
  on-tertiary-fixed-variant: '#852127'
  background: '#051423'
  on-background: '#d5e4f9'
  surface-variant: '#283646'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 1.75rem
    fontWeight: '600'
    lineHeight: 2.25rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '600'
    lineHeight: 1.5rem
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 0.9375rem
    fontWeight: '400'
    lineHeight: 1.375rem
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.25rem
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1rem
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: 0.03em
  label-sm:
    fontFamily: Inter
    fontSize: 0.6875rem
    fontWeight: '600'
    lineHeight: 0.875rem
    letterSpacing: 0.06em
  mono-data:
    fontFamily: Inter
    fontSize: 0.8125rem
    fontWeight: '500'
    lineHeight: 1.125rem
    letterSpacing: -0.01em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-lg: 1rem
  margin: 0.75rem
  margin-lg: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.375rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system establishes an operational, high-reliability command-and-control interface tailored for civic disaster response teams, GIS hydrographers, and field relief coordinators operating within the flood-prone Brahmaputra basin of Guwahati. 

The aesthetic adheres to **Tactical Data-Dense Minimalism**: deliberate, calm, and utilitarian. It dispenses with extraneous ornamentation, heavy gloss, or distracting neon glows, prioritizing information hierarchy, legibility under high-stress conditions, and uninterrupted real-time situational awareness. 

The UI evokes:
- **Authority and Rigor:** Crisp spatial grids, precision telemetry frames, and sharp visual anchors that mimic aerospace and tactical defense mapping consoles.
- **Cognitive Quietude:** Deep navy and slate tonal backdrops absorb eye strain over prolonged multi-screen operational shifts.
- **Decisive Urgency:** Chromatic saturation is rigorously quarantined to spatial vectors, stage-gauge indicators, and emergency status flags.

## Colors

The color system operates on an asymmetric dark-mode architecture engineered for multi-monitor command rooms. Background values layer depth through disciplined value stepping rather than heavy dropshadows:

- **Canvas & Structural Layers:**
  - Main Background (`#0B1220`): Deep subterranean base for active vector map canvasses and root viewports.
  - Sidebar Background (`#101A2A`): Anchored global navigation and mission control tool rails.
  - Panel Background (`#151F30`): Base surface for layer selectors, incident queues, and telemetry feeds.
  - Elevated Panel (`#192538`): Floating map HUDs, inspection drawers, and situational popovers.
  - Border/Stroke (`#263449`): Structural delineation separating high-density map quadrants and data tables.

- **Data Readouts & Typography:**
  - Primary (`#F4F7FB`): Uncompromising contrast for critical metrics, hydrologic station labels, and active telemetry.
  - Secondary (`#A9B8CC`): Operational metadata, column headers, and coordinates.
  - Muted (`#75869D`): Timestamp watermarks, grid axis markers, and inactive states.

- **Functional & River Severity States:**
  - Primary Accent (`#20BFA5`): System health, sensor ping confirmations, and safe operations.
  - Secondary Accent (`#45BFEA`): Water velocity vectors, Brahmaputra basin GIS overlays, and active hydrologic flow lines.
  - Low Risk (`#27AE80`): Normal river stage, safe shelter capacity, clear transport corridors.
  - Moderate Risk (`#F5B84B`): Waterlogging alert, tributary warning threshold, caution zones.
  - High Risk (`#F08A42`): Embankment seepage, localized inundation, immediate evacuation prep.
  - Critical Risk (`#F07171`): Flash flood surge, breached bunds, marooned sector distress signals.

## Typography

Typography prioritizes extreme scanability and tabular vertical alignment. **Inter** is deployed across all UI roles with mandatory OpenType features activated across the entire application interface:

- `font-feature-settings: "cv05" 1, "cv11" 1, "tnum" 1, "ss01" 1;`
  - **Tabular Numerals (`tnum`):** Critical for spatial coordinates (lat/long), water discharge rates (cumecs), and telemetry readouts to eliminate baseline jitter during rapid streaming updates.
  - **High-legibility Glyphs (`cv05`, `cv11`):** Distinctive shapes for lowercase 'l', digit '1', and capital 'I' prevent misinterpretations during rapid field dispatches.

Scale execution:
- Headings are kept compact (sub-32px) to maximize geospatial viewport estate.
- Section tags, spatial layer names, and status chips apply uppercase styling via `label-sm` with widened tracking (+0.06em).
- Data density is maintained by anchoring primary dashboard lists to `body-md` (13px) and metadata tags to `body-sm` (12px).

## Layout & Spacing

The layout is built upon a **Dense Operational Frame** utilizing an asymmetric 16-column fixed-dock fluid workspace:

- **Global Shell Hierarchy:**
  - Left Dock: 64px collapsed icon rail expanding to 280px operational layer panel (`Sidebar Background: #101A2A`).
  - Center Viewport: Fluid vector/satellite map canvas maintaining uninterrupted visual access.
  - Right Dock: 380px or 440px modular telemetry and incident response drawer (`Panel Background: #151F30`).
  - Bottom Bar: 40px fixed system health, coordinate scrubber, and data sync status strip.

- **Rhythm & Grid:**
  - Employs a strict 4px sub-grid with an 8px base rhythm.
  - Element paddings inside command cards and telemetry tiles rely on `space-sm` (6px) and `space-md` (12px) to maximize vertical information density.
  - Spatial gaps between modular dashboard widgets use `gutter` (12px).
  - Breakpoints:
    - **Desktop Large (Command Wall / Dual Monitor, >1800px):** 16-column grid with tri-pane multi-station view.
    - **Standard Desktop (Operations Station, 1280px - 1799px):** Persistent GIS center canvas with single collapsible incident panel.
    - **Field Dispatch (Tablet / Mobile, <1024px):** Single-column stack with bottom-sheet gesture controls, sliding map-over-table mode.

## Elevation & Depth

Visual depth is achieved through structural planar layering and tactical edge highlighting rather than diffuse ambient dropshadows:

- **Tonal Stepping:**
  - Base map: `#0B1220`
  - Fixed workbenches & sidebars: `#101A2A`
  - Content containers: `#151F30`
  - Floating map widgets & active inspection panels: `#192538`

- **Crisp Vector Framing:**
  - All panels, cards, and modal sheets are outlined by a single-pixel structural hairline: `1px solid #263449`.
  - Focused or active operational layers replace the hairline border with a high-visibility accent outline: `1px solid #20BFA5` or `1px solid #45BFEA`.

- **Tactical Elevation (Shadows):**
  - Ambient shadows are restricted to floating map controls, hover tooltips, and flyout alert panels.
  - Specification: `0 4px 16px -2px rgba(3, 7, 18, 0.65)`, maintaining dark, tightly bounded projection without ambient haze.

## Shapes

The design language mandates tightly controlled corner geometry (`roundedness: 1`), conveying technical engineering precision:

- Standard Cards, HUD widgets, and Side Panels: **6px** (`rounded-md`).
- Form inputs, segmented toggles, and buttons: **6px** (`rounded-md`).
- Micro status tags, counter chips, and badge pill flags: **4px** (`rounded-sm`).
- Global container frames (Main workspace layout): **0px** square-bound edges to maximize screen usage against screen borders.
- Floating overlay menus & inspection flyouts: **8px** (`rounded-lg`).

## Components

### Buttons & Action Triggers
- **Primary Operational Button:** Solid `#20BFA5` fill, `#0B1220` text, semi-bold 12px label, 6px radius, height 32px. Hover: Brightness 110%. Active: Inset hairline outline.
- **Secondary Dispatch Button:** `#192538` fill, `1px solid #263449`, `#F4F7FB` text. Hover: Border shifts to `#45BFEA`, text to `#45BFEA`.
- **Destructive/Emergency Button:** Solid `#F07171` fill, `#0B1220` text, reserved exclusively for irreversible actions (e.g., sound evacuation siren, lock sector).

### Status Indicators & Threat Badges
- Threat chips consist of a `1px solid` border, a tinted background at 12% opacity, and full-value foreground text:
  - Low: Border/Text `#27AE80`, BG `rgba(39, 174, 128, 0.12)`
  - Moderate: Border/Text `#F5B84B`, BG `rgba(245, 184, 75, 0.12)`
  - High: Border/Text `#F08A42`, BG `rgba(240, 138, 66, 0.12)`
  - Critical: Border/Text `#F07171`, BG `rgba(240, 113, 113, 0.12)` with active 1s rhythmic stroke blink.

### Data Inputs & Search
- Background `#101A2A`, `1px solid #263449`, text `#F4F7FB`, placeholder `#75869D`.
- Focus state: `1px solid #20BFA5`, no heavy outer glow ring, maintaining crisp 6px boundary. Height: 32px for filters, 28px for inline map query tools.

### Hydrologic & Telemetry Cards
- Surface `#151F30` with `1px solid #263449` perimeter.
- Top header: 8px padding, `#101A2A` inner tab strip, containing sensor ID in tabular mono font, location tag, and live ping pulse.
- Body content: Key data displayed in `display-lg` tabular numerals with water stage units (`m`, `cumecs`) styled in `label-sm` `#75869D`.

### Checkboxes & Segmented Map Layer Selectors
- Checkboxes: 14x14px square with 3px border-radius, background `#101A2A`, border `1.5px solid #263449`. Checked: `#20BFA5` fill with dark checkmark.
- Segmented layer switches: Enclosed container with `#101A2A` background, 4px internal padding; active segment elevated via `#192538` and `1px solid #263449`.

### Tactical Incident Lists
- Alternating row styling: Unread/Critical items highlighted with a 3px left vertical border accent corresponding to the incident risk tier.
- Row hover: `#192538` background shift with tabular timestamp right-aligned in `#75869D`.