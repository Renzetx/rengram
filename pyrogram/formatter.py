
from typing import Optional
from pyrogram import enums

class MarkdownDelimiters:
    BOLD = "**"
    ITALIC = "__"
    UNDERLINE = "--"
    STRIKE = "~~"
    SPOILER = "||"
    CODE = "`"
    PRE = "```"
    BLOCKQUOTE = "> "
    BLOCKQUOTE_ESCAPE = "|> "
    BLOCKQUOTE_EXPANDABLE = "**>"
    BLOCKQUOTE_EXPANDABLE_END = "<**"


class TextFormatter(str):
    
    def __new__(cls, content="", mode="html"):
        instance = super().__new__(cls, content)
        instance.mode = mode
        return instance
    
    def __add__(self, other):
        return TextFormatter(str.__add__(self, other), mode=self.mode)


class Formatter:
    
    @staticmethod
    def bold(text_content: str, parse_mode: str = "markdown"):
        """Bold text"""
        if parse_mode == "html":
            return TextFormatter(f"<b>{text_content}</b>", mode=parse_mode)
        return TextFormatter(f"{MarkdownDelimiters.BOLD}{text_content}{MarkdownDelimiters.BOLD}", mode=parse_mode)

    @staticmethod
    def italic(text_content: str, parse_mode: str = "markdown"):
        """Italic text"""
        if parse_mode == "html":
            return TextFormatter(f"<i>{text_content}</i>", mode=parse_mode)
        return TextFormatter(f"{MarkdownDelimiters.ITALIC}{text_content}{MarkdownDelimiters.ITALIC}", mode=parse_mode)

    @staticmethod
    def underline(text_content: str, parse_mode: str = "markdown"):
        """Underlined text"""
        if parse_mode == "html":
            return TextFormatter(f"<u>{text_content}</u>", mode=parse_mode)
        return TextFormatter(f"{MarkdownDelimiters.UNDERLINE}{text_content}{MarkdownDelimiters.UNDERLINE}", mode=parse_mode)

    @staticmethod
    def strike(text_content: str, parse_mode: str = "markdown"):
        """Strikethrough text"""
        if parse_mode == "html":
            return TextFormatter(f"<s>{text_content}</s>", mode=parse_mode)
        return TextFormatter(f"{MarkdownDelimiters.STRIKE}{text_content}{MarkdownDelimiters.STRIKE}", mode=parse_mode)

    @staticmethod
    def spoiler(text_content: str, parse_mode: str = "markdown"):
        """Spoiler text"""
        if parse_mode == "html":
            return TextFormatter(f"<spoiler>{text_content}</spoiler>", mode=parse_mode)
        return TextFormatter(f"{MarkdownDelimiters.SPOILER}{text_content}{MarkdownDelimiters.SPOILER}", mode=parse_mode)

    @staticmethod
    def mono(text_content: str, parse_mode: str = "markdown"):
        """Monospace/code text"""
        if parse_mode == "html":
            return TextFormatter(f"<code>{text_content}</code>", mode=parse_mode)
        return TextFormatter(f"{MarkdownDelimiters.CODE}{text_content}{MarkdownDelimiters.CODE}", mode=parse_mode)

    @staticmethod
    def pre(text_content: str, language: str = "", parse_mode: str = "markdown"):
        """Preformatted code block"""
        if parse_mode == "html":
            return TextFormatter(
                f"<pre><code class='language-{language}'>{text_content}</code></pre>", 
                mode=parse_mode
            )
        return TextFormatter(
            f"{MarkdownDelimiters.PRE}{language}\n{text_content}\n{MarkdownDelimiters.PRE}", 
            mode=parse_mode
        )

    @staticmethod
    def blockquote(text_content: str, parse_mode: str = "markdown"):
        """Blockquote"""
        if parse_mode == "html":
            return TextFormatter(f"<blockquote>{text_content}</blockquote>", mode=parse_mode)

        lines = str(text_content).strip().split("\n")
        quoted_lines = "\n".join(f"{MarkdownDelimiters.BLOCKQUOTE}{line}" for line in lines)
        return TextFormatter(quoted_lines, mode=parse_mode)

    @staticmethod
    def escaped_blockquote(text_content: str, parse_mode: str = "markdown"):
        """Escaped blockquote"""
        if parse_mode == "html":
            return Formatter.blockquote(text_content, parse_mode)

        lines = str(text_content).strip().split("\n")
        quoted_lines = "\n".join(f"{MarkdownDelimiters.BLOCKQUOTE_ESCAPE}{line}" for line in lines)
        return TextFormatter(quoted_lines, mode=parse_mode)

    @staticmethod
    def expandable_blockquote(text_content: str, parse_mode: str = "markdown"):
        """Expandable blockquote"""
        if parse_mode == "html":
            return TextFormatter(f"<blockquote expandable>{text_content}</blockquote>", mode=parse_mode)
        return TextFormatter(
            f"{MarkdownDelimiters.BLOCKQUOTE_EXPANDABLE}{text_content}{MarkdownDelimiters.BLOCKQUOTE_EXPANDABLE_END}", 
            mode=parse_mode
        )

    @staticmethod
    def link(text_content: str, url: str, parse_mode: str = "markdown"):
        """Hyperlink"""
        if parse_mode == "html":
            return TextFormatter(f'<a href="{url}">{text_content}</a>', mode=parse_mode)
        return TextFormatter(f"[{text_content}]({url})", mode=parse_mode)

    @staticmethod
    def new_line(count: int = 1, parse_mode: str = "markdown"):
        """New line(s)"""
        return TextFormatter("\n" * count, mode=parse_mode)


# ============= WRAPPER METHODS UNTUK CLIENT CLASS =============
# Copy methods ini ke dalam Client class lu

class ClientFormatterMethods:
    """
    Copy semua method dibawah ini ke dalam Client class.
    Method ini akan otomatis pake self.parse_mode dari client instance.
    """
    
    def text(self, text_content: str):
        """Plain text without formatting"""
        return Formatter.text(text_content, self.parse_mode)

    def bold(self, text_content: str):
        """Bold text"""
        return Formatter.bold(text_content, self.parse_mode)

    def italic(self, text_content: str):
        """Italic text"""
        return Formatter.italic(text_content, self.parse_mode)

    def underline(self, text_content: str):
        """Underlined text"""
        return Formatter.underline(text_content, self.parse_mode)

    def strike(self, text_content: str):
        """Strikethrough text"""
        return Formatter.strike(text_content, self.parse_mode)

    def spoiler(self, text_content: str):
        """Spoiler text"""
        return Formatter.spoiler(text_content, self.parse_mode)

    def mono(self, text_content: str):
        """Monospace/code text"""
        return Formatter.mono(text_content, self.parse_mode)

    def pre(self, text_content: str, language: str = ""):
        """Preformatted code block"""
        return Formatter.pre(text_content, language, self.parse_mode)

    def blockquote(self, text_content: str):
        """Blockquote"""
        return Formatter.blockquote(text_content, self.parse_mode)

    def escaped_blockquote(self, text_content: str):
        """Escaped blockquote"""
        return Formatter.escaped_blockquote(text_content, self.parse_mode)

    def expandable_blockquote(self, text_content: str):
        """Expandable blockquote"""
        return Formatter.expandable_blockquote(text_content, self.parse_mode)

    def link(self, text_content: str, url: str):
        """Hyperlink"""
        return Formatter.link(text_content, url, self.parse_mode)

    def new_line(self, count: int = 1):
        """New line(s)"""
        return Formatter.new_line(count, self.parse_mode)