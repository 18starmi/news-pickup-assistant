from html import escape


def render_page(*, title: str, eyebrow: str, heading: str, description: str, actions: str = "", content: str) -> str:
    escaped_title = escape(title)
    escaped_eyebrow = escape(eyebrow)
    escaped_heading = escape(heading)
    escaped_description = escape(description)
    return f"""
    <!doctype html>
    <html lang="ja">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{escaped_title}</title>
        <style>
          :root {{
            --bg: #f6f7f9;
            --surface: #ffffff;
            --surface-strong: #ffffff;
            --surface-muted: #f3f6fa;
            --surface-tint: #eef4ff;
            --border: #e5e7eb;
            --border-strong: #d1d5db;
            --text: #111827;
            --text-soft: #6b7280;
            --accent: #2563eb;
            --accent-strong: #1d4ed8;
            --accent-cool: #2563eb;
            --accent-green: #047857;
            --shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
            --radius-xl: 20px;
            --radius-lg: 18px;
            --radius-md: 14px;
            --radius-sm: 10px;
          }}

          * {{
            box-sizing: border-box;
          }}

          body {{
            margin: 0;
            min-height: 100vh;
            color: var(--text);
            font-family: Inter, "SF Pro Display", "SF Pro Text", "Segoe UI", "Hiragino Sans", "Yu Gothic UI", sans-serif;
            background:
              linear-gradient(180deg, #ffffff 0%, #f8fafc 180px, var(--bg) 100%);
          }}

          a {{
            color: var(--accent);
            text-decoration: none;
          }}

          a:hover {{
            text-decoration: underline;
          }}

          .button-link {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 14px;
            background: var(--surface);
            color: var(--text);
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: border-color 160ms ease, background 160ms ease;
          }}

          .button-link:hover {{
            background: #f9fafb;
            border-color: #cbd5e1;
            text-decoration: none;
          }}

          button {{
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 10px 14px;
            background: var(--accent);
            color: #ffffff;
            font: inherit;
            font-weight: 600;
            cursor: pointer;
            transition: background 160ms ease, border-color 160ms ease, color 160ms ease;
          }}

          button:hover {{
            background: var(--accent-strong);
          }}

          button.secondary {{
            background: var(--surface);
            border-color: var(--border);
            color: var(--text);
          }}

          button.secondary.is-selected {{
            background: #eff6ff;
            border-color: #93c5fd;
            color: #1d4ed8;
          }}

          main.shell {{
            width: min(1220px, calc(100% - 32px));
            margin: 0 auto;
            padding: 24px 0 56px;
          }}

          .topbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 18px;
            padding: 6px 2px;
          }}

          .brand {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            color: var(--text);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: -0.01em;
          }}

          .brand-mark {{
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%);
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.08);
          }}

          .topbar-nav {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
          }}

          .hero {{
            padding: 8px 0 0;
          }}

          .hero-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 20px;
            margin-bottom: 18px;
          }}

          .eyebrow {{
            margin: 0 0 10px;
            color: var(--text-soft);
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
          }}

          h1 {{
            margin: 0;
            font-family: inherit;
            font-size: clamp(1.75rem, 3vw, 2.4rem);
            line-height: 1.12;
            letter-spacing: -0.03em;
            font-weight: 700;
          }}

          .hero-description {{
            max-width: 620px;
            margin: 0;
            color: var(--text-soft);
            font-size: 14px;
            line-height: 1.65;
          }}

          .hero-actions {{
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 10px;
          }}

          .section {{
            margin-top: 10px;
          }}

          .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 14px;
            margin-top: 22px;
          }}

          .stat {{
            padding: 14px 16px;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            background: #fbfcfe;
          }}

          .stat-label {{
            margin: 0 0 6px;
            color: var(--text-soft);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
          }}

          .stat-value {{
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.02em;
          }}

          .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            align-items: stretch;
          }}

          .card {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 16px;
            background: var(--surface-strong);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
          }}

          .card-media {{
            position: relative;
            overflow: hidden;
            min-height: 148px;
            border-radius: 12px;
            background:
              linear-gradient(135deg, rgba(37, 99, 235, 0.92), rgba(59, 130, 246, 0.72)),
              linear-gradient(45deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0));
          }}

          .card-media::before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
              radial-gradient(circle at top right, rgba(255, 255, 255, 0.24), transparent 28%),
              linear-gradient(180deg, rgba(255, 255, 255, 0), rgba(15, 23, 42, 0.16));
          }}

          .card-media.has-image {{
            background: #dbe4f0;
          }}

          .card-image {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
          }}

          .media-labels {{
            position: absolute;
            top: 10px;
            left: 10px;
            right: 10px;
            display: flex;
            justify-content: space-between;
            gap: 8px;
            z-index: 1;
          }}

          .media-chip {{
            display: inline-flex;
            align-items: center;
            padding: 5px 8px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.92);
            color: #1f2937;
            font-size: 11px;
            font-weight: 700;
          }}

          .media-title {{
            position: absolute;
            left: 14px;
            right: 14px;
            bottom: 14px;
            z-index: 1;
            color: #eff6ff;
            font-size: 18px;
            font-weight: 700;
            line-height: 1.35;
            letter-spacing: -0.02em;
          }}

          .card-header {{
            display: flex;
            justify-content: space-between;
            gap: 14px;
            align-items: flex-start;
          }}

          .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }}

          .pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: 999px;
            background: var(--surface-muted);
            color: var(--text-soft);
            font-size: 12px;
            font-weight: 600;
          }}

          .pill.cool {{
            background: #eff6ff;
            color: var(--accent-cool);
          }}

          .pill.green {{
            background: #ecfdf5;
            color: var(--accent-green);
          }}

          .score {{
            min-width: 94px;
            padding: 8px 10px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
            background: #f8fafc;
            color: var(--text);
            text-align: right;
          }}

          .score-label {{
            display: block;
            margin-bottom: 4px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--text-soft);
          }}

          .score-value {{
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 0.03em;
          }}

          .card h2 {{
            margin: 0;
            font-family: inherit;
            font-size: 19px;
            line-height: 1.45;
            letter-spacing: -0.02em;
            font-weight: 700;
          }}

          .excerpt {{
            margin: 0;
            color: var(--text-soft);
            font-size: 13px;
            line-height: 1.7;
          }}

          .summary-stack {{
            display: grid;
            gap: 8px;
          }}

          .summary-block {{
            padding: 10px 12px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
          }}

          .summary-block strong {{
            display: block;
            margin-bottom: 6px;
            font-size: 12px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
          }}

          .summary-block.warm {{
            background: #fafafa;
          }}

          .summary-block.cool {{
            background: #f8fbff;
          }}

          .summary-block.green {{
            background: #f8fcfa;
          }}

          .summary-text {{
            margin: 0;
            font-size: 13px;
            line-height: 1.7;
          }}

          .supporting {{
            margin: 0;
            color: var(--text-soft);
            font-size: 14px;
            line-height: 1.75;
          }}

          details {{
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            background: #fafbfd;
          }}

          summary {{
            cursor: pointer;
            font-weight: 700;
            color: var(--text);
          }}

          .actions-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: auto;
          }}

          .actions-row button,
          .actions-row .button-link {{
            padding: 8px 10px;
            font-size: 12px;
            border-radius: 8px;
          }}

          .inline-form {{
            margin: 0;
          }}

          .table-shell {{
            margin-top: 22px;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            background: var(--surface);
            box-shadow: var(--shadow);
          }}

          table {{
            width: 100%;
            border-collapse: collapse;
          }}

          thead th {{
            padding: 18px 20px;
            border-bottom: 1px solid var(--border);
            color: var(--text-soft);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-align: left;
            text-transform: uppercase;
            background: #f8fafc;
          }}

          tbody td {{
            padding: 18px 20px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: top;
          }}

          tbody tr:last-child td {{
            border-bottom: 0;
          }}

          .empty-state {{
            padding: 42px 24px;
            border: 1px dashed var(--border-strong);
            border-radius: var(--radius-lg);
            background: #fbfdff;
            text-align: center;
            color: var(--text-soft);
            line-height: 1.8;
          }}

          @media (max-width: 860px) {{
            main.shell {{
              width: min(100% - 20px, 1220px);
              padding-top: 20px;
            }}

            .topbar {{
              flex-direction: column;
              align-items: flex-start;
            }}

            .hero-top {{
              flex-direction: column;
            }}

            .hero-actions {{
              justify-content: flex-start;
            }}

            .card {{
              padding: 12px;
            }}

            .card-header {{
              flex-direction: column;
            }}

            .score {{
              min-width: 0;
              text-align: left;
            }}

            .table-shell {{
              overflow-x: auto;
            }}

            table {{
              min-width: 760px;
            }}
          }}
        </style>
      </head>
      <body>
        <main class="shell">
          <header class="topbar">
            <div class="brand">
              <span class="brand-mark"></span>
              <span>{escaped_eyebrow}</span>
            </div>
            <nav class="topbar-nav">
              <a class="button-link" href="/items/view">ホーム</a>
              <a class="button-link" href="/trending/view">Trending</a>
              <a class="button-link" href="/items/archived/view">アーカイブ</a>
              <a class="button-link" href="/sources/view">ソース</a>
            </nav>
          </header>
          <section class="hero">
            <div class="hero-top">
              <div>
                <h1>{escaped_heading}</h1>
              </div>
              <div class="hero-actions">{actions}</div>
            </div>
            <p class="hero-description">{escaped_description}</p>
            <div class="section">
              {content}
            </div>
          </section>
        </main>
      </body>
    </html>
    """
