import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

// react-markdown ham HTML'i render etmez (XSS güvenli). Kod blokları highlight.js ile renklendirilir.
export function MarkdownView({ source }: { source: string }) {
  return (
    <div className="prose">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[[rehypeHighlight, { detect: true }]]}>
        {source}
      </ReactMarkdown>
    </div>
  );
}
