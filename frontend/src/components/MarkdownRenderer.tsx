import React, { useEffect, useRef } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

// Lazy imports for syntax highlighting, math, and diagrams
// Install: npm install prismjs katex mermaid @types/prismjs
let Prism: any = null;
let katex: any = null;
let mermaid: any = null;

// Dynamically import libraries on client-side
if (typeof window !== 'undefined') {
  import('prismjs').then((module) => {
    Prism = module.default;
    // Import common language syntaxes
    import('prismjs/components/prism-python');
    import('prismjs/components/prism-javascript');
    import('prismjs/components/prism-typescript');
    import('prismjs/components/prism-jsx');
    import('prismjs/components/prism-tsx');
    import('prismjs/components/prism-bash');
    import('prismjs/components/prism-json');
    import('prismjs/components/prism-markdown');
    import('prismjs/components/prism-sql');
    import('prismjs/components/prism-yaml');
    import('prismjs/components/prism-docker');
    import('prismjs/components/prism-rust');
    import('prismjs/components/prism-go');
    import('prismjs/components/prism-java');
    import('prismjs/components/prism-c');
    import('prismjs/components/prism-cpp');
    // Import dark theme
    import('prismjs/themes/prism-tomorrow.css');
  }).catch(err => console.warn('Prism.js not loaded:', err));

  import('katex').then((module) => {
    katex = module.default;
    import('katex/dist/katex.min.css');
  }).catch(err => console.warn('KaTeX not loaded:', err));

  import('mermaid').then((module) => {
    mermaid = module.default;
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      fontFamily: 'ui-monospace, monospace'
    });
  }).catch(err => console.warn('Mermaid not loaded:', err));
}

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Configure marked with custom renderer
    const renderer = new marked.Renderer();

    // Custom code block rendering
    const originalCodeRenderer = renderer.code.bind(renderer);
    renderer.code = (code: string, language: string | undefined, isEscaped: boolean) => {
      // Check if mermaid diagram
      if (language === 'mermaid') {
        const id = `mermaid-${Math.random().toString(36).substring(7)}`;
        setTimeout(() => {
          if (mermaid && containerRef.current) {
            const element = containerRef.current.querySelector(`#${id}`);
            if (element) {
              mermaid.render(id, code).then((result: any) => {
                if (element) {
                  element.innerHTML = result.svg;
                }
              }).catch((err: Error) => {
                console.error('Mermaid render error:', err);
                if (element) {
                  element.textContent = `Mermaid error: ${err.message}`;
                }
              });
            }
          }
        }, 100);
        return `<div id="${id}" class="mermaid-diagram my-4 p-4 bg-gray-900 rounded-lg overflow-auto">${code}</div>`;
      }

      // Syntax highlighting with Prism.js
      if (language && Prism && Prism.languages[language]) {
        try {
          const highlighted = Prism.highlight(code, Prism.languages[language], language);
          return `<pre class="language-${language} rounded-lg my-4 overflow-x-auto"><code class="language-${language}">${highlighted}</code></pre>`;
        } catch (err) {
          console.warn(`Prism highlighting failed for ${language}:`, err);
        }
      }

      // Fallback to default rendering
      return originalCodeRenderer(code, language, isEscaped);
    };

    // Custom inline code rendering
    const originalCodespanRenderer = renderer.codespan.bind(renderer);
    renderer.codespan = (code: string) => {
      // Check if LaTeX inline math: $...$
      if (code.startsWith('$') && code.endsWith('$') && code.length > 2) {
        const latex = code.slice(1, -1);
        if (katex) {
          try {
            const html = katex.renderToString(latex, {
              throwOnError: false,
              displayMode: false
            });
            return `<span class="katex-inline">${html}</span>`;
          } catch (err) {
            console.warn('KaTeX inline render error:', err);
          }
        }
      }
      return originalCodespanRenderer(code);
    };

    // Custom paragraph rendering for block LaTeX: $$...$$
    const originalParagraphRenderer = renderer.paragraph.bind(renderer);
    renderer.paragraph = (text: string) => {
      // Check if LaTeX block math: $$...$$
      if (text.startsWith('$$') && text.endsWith('$$') && text.length > 4) {
        const latex = text.slice(2, -2).trim();
        if (katex) {
          try {
            const html = katex.renderToString(latex, {
              throwOnError: false,
              displayMode: true
            });
            return `<div class="katex-block my-4 text-center">${html}</div>`;
          } catch (err) {
            console.warn('KaTeX block render error:', err);
          }
        }
      }
      return originalParagraphRenderer(text);
    };

    // Set marked options
    marked.setOptions({
      renderer,
      gfm: true,
      breaks: true,
      pedantic: false,
      sanitize: false, // We use DOMPurify instead
      smartLists: true,
      smartypants: true,
      xhtml: false
    });

    // Parse markdown
    const rawHtml = marked.parse(content) as string;

    // Sanitize HTML
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
      ADD_TAGS: ['iframe'],
      ADD_ATTR: ['allow', 'allowfullscreen', 'frameborder', 'scrolling'],
      FORBID_TAGS: ['style'],
      FORBID_ATTR: ['onerror', 'onload']
    });

    // Render
    containerRef.current.innerHTML = cleanHtml;

    // Apply Prism highlighting to any code blocks that weren't processed
    if (Prism && containerRef.current) {
      containerRef.current.querySelectorAll('pre code').forEach((block) => {
        if (!block.classList.contains('language-mermaid')) {
          Prism.highlightElement(block);
        }
      });
    }

    // Render mermaid diagrams
    if (mermaid && containerRef.current) {
      const mermaidBlocks = containerRef.current.querySelectorAll('.mermaid-diagram');
      mermaidBlocks.forEach((block, index) => {
        const code = block.textContent || '';
        const id = `mermaid-runtime-${index}`;
        mermaid.render(id, code).then((result: any) => {
          block.innerHTML = result.svg;
        }).catch((err: Error) => {
          console.error('Mermaid runtime render error:', err);
          block.textContent = `Mermaid error: ${err.message}`;
        });
      });
    }
  }, [content]);

  return (
    <div
      ref={containerRef}
      className={`markdown-content prose prose-invert max-w-none ${className}`}
      style={{
        fontSize: '15px',
        lineHeight: '1.7'
      }}
    />
  );
};

export default MarkdownRenderer;
