declare module "react-syntax-highlighter/dist/esm/languages/prism/*" {
  import { Language } from "react-syntax-highlighter";
  const value: Language;
  export default value;
}

declare module "react-syntax-highlighter/dist/esm/styles/prism/*" {
  import { SyntaxHighlighterStyle } from "react-syntax-highlighter";
  const value: SyntaxHighlighterStyle;
  export default value;
}

declare module "react-syntax-highlighter" {
  import { ComponentType, SVGProps } from "react";

  export interface SyntaxHighlighterProps {
    language?: string;
    style: Record<string, unknown>;
    customStyle?: Record<string, unknown>;
    showLineNumbers?: boolean;
    children?: React.ReactNode;
    className?: string;
  }

  export default function SyntaxHighlighter(props: SyntaxHighlighterProps): JSX.Element;

  export function registerLanguage(language: string, languageDefinition: unknown): void;
}