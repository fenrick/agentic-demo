import React from "react";
import { LinkExternalIcon, BookIcon } from "@primer/octicons-react";

export interface SourceItem {
  url?: string;
  title?: string;
}

interface Props {
  sources: (SourceItem | string)[];
}

type Normalised = { url: string; title: string };

function normaliseSource(s: SourceItem | string): Normalised | null {
  const obj = typeof s === "string" ? { url: s, title: undefined } : s;
  if (!obj?.url) return null;
  try {
    const u = new URL(obj.url);
    const title =
      obj.title && obj.title.trim().length > 0
        ? obj.title
        : u.href.replace(/^https?:\/\//, "");
    return { url: u.toString(), title };
  } catch {
    return null; // ignore invalid URLs
  }
}

function hostOf(url: string): string {
  try {
    return new URL(url).host;
  } catch {
    return "";
  }
}

const listStyles: React.CSSProperties = {
  listStyle: "none",
  margin: 0,
  padding: 0,
  display: "grid",
  rowGap: "var(--base-size-8)", // 8px
};

const itemStyles: React.CSSProperties = {
  display: "flex",
  alignItems: "baseline",
  gap: "var(--base-size-8)",
  minWidth: 0,
};

const hostStyles: React.CSSProperties = {
  color: "var(--fgColor-muted)",
  fontSize: "12px",
  whiteSpace: "nowrap",
};

const emptyWrapStyles: React.CSSProperties = {
  border: "1px solid var(--borderColor-default)",
  borderRadius: "6px",
  padding: "var(--base-size-16)", // 16px
  textAlign: "center",
  background: "var(--color-canvas-subtle)",
};

const emptyIconStyles: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  width: 40,
  height: 40,
  borderRadius: "50%",
  border: "1px solid var(--borderColor-default)",
  marginBottom: "var(--base-size-8)",
};

const linkIconWrap: React.CSSProperties = {
  marginLeft: "4px",
  verticalAlign: "middle",
};

const linkStyles: React.CSSProperties = {
  wordBreak: "break-word",
};

const SourcesPanel: React.FC<Props> = ({ sources }) => {
  const items = React.useMemo(() => {
    const arr = sources
      .map(normaliseSource)
      .filter((x): x is Normalised => !!x);

    // Deduplicate by URL while preserving order
    const seen = new Set<string>();
    return arr.filter(({ url }) => (seen.has(url) ? false : (seen.add(url), true)));
  }, [sources]);

  if (!items.length) {
    return (
      <div role="status" aria-live="polite" style={emptyWrapStyles}>
        <div aria-hidden style={emptyIconStyles}>
          <BookIcon size={20} />
        </div>
        <div style={{ fontWeight: 600, marginBottom: "4px" }}>No sources yet</div>
        <div style={{ color: "var(--fgColor-muted)", fontSize: 14 }}>
          When the builder cites web pages, they’ll appear here.
        </div>
      </div>
    );
  }

  return (
    <ul style={listStyles} aria-label="Cited sources">
      {items.map(({ url, title }) => {
        const host = hostOf(url);
        return (
          <li key={url} style={itemStyles}>
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              style={linkStyles}
            >
              {title}
              <span aria-hidden style={linkIconWrap}>
                <LinkExternalIcon size={16} />
              </span>
            </a>
            {host && <span style={hostStyles}>— {host}</span>}
          </li>
        );
      })}
    </ul>
  );
};

export default SourcesPanel;
