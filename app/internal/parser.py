import re
from typing import List, Dict, Optional, NamedTuple
from urllib.parse import urlparse


class ParsedProject(NamedTuple):
    """Structured representation of a parsed project"""

    name: str
    description: Optional[str]
    url: Optional[str]
    category: Optional[str]
    raw_markdown: str


class MarkdownParser:
    """Parser for extracting projects from awesome repository markdown"""

    # Common patterns for project entries
    PROJECT_PATTERNS = [
        # [Name](url) - Description
        re.compile(r"^\s*[-*]\s*\[([^\]]+)\]\(([^)]+)\)\s*[-–—]\s*(.+)$", re.MULTILINE),
        # [Name](url): Description
        re.compile(r"^\s*[-*]\s*\[([^\]]+)\]\(([^)]+)\):\s*(.+)$", re.MULTILINE),
        # [Name](url) Description (no separator)
        re.compile(r"^\s*[-*]\s*\[([^\]]+)\]\(([^)]+)\)\s+([^-–—:].+)$", re.MULTILINE),
        # Simple link without description
        re.compile(r"^\s*[-*]\s*\[([^\]]+)\]\(([^)]+)\)\s*$", re.MULTILINE),
    ]

    # Pattern to identify section headers
    SECTION_PATTERN = re.compile(r"^#+\s*(.+)$", re.MULTILINE)

    def __init__(self):
        self.current_category = None

    def parse_awesome_readme(self, content: str) -> List[ParsedProject]:
        """Parse an awesome repository README and extract projects"""
        projects = []
        lines = content.split("\n")
        current_category = None

        for line in lines:
            # Check for section headers
            section_match = self.SECTION_PATTERN.match(line)
            if section_match:
                current_category = self._clean_category_name(section_match.group(1))
                continue

            # Try to match project patterns
            project = self._parse_project_line(line, current_category)
            if project:
                projects.append(project)

        return projects

    def _parse_project_line(
        self, line: str, category: Optional[str]
    ) -> Optional[ParsedProject]:
        """Parse a single line to extract project information"""
        for pattern in self.PROJECT_PATTERNS:
            match = pattern.match(line)
            if match:
                groups = match.groups()
                name = groups[0].strip()
                url = groups[1].strip()
                description = groups[2].strip() if len(groups) > 2 else None

                # Skip invalid URLs (anchors, empty, etc.)
                if not self._is_valid_url(url):
                    continue

                return ParsedProject(
                    name=name,
                    description=description,
                    url=url,
                    category=category,
                    raw_markdown=line.strip(),
                )

        return None

    def _clean_category_name(self, category: str) -> str:
        """Clean up category name by removing special characters"""
        # Remove markdown formatting, emojis, and extra whitespace
        cleaned = re.sub(r"[#*_`~]", "", category)
        cleaned = re.sub(r":\w+:", "", cleaned)  # Remove emoji codes
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _is_github_url(self, url: str) -> bool:
        """Check if URL is a GitHub repository URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() in ["github.com", "www.github.com"]
        except Exception:
            return False

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid (not an anchor link)"""
        if not url or url.strip() == "":
            return False
        
        # Filter out anchor-only URLs
        if url.startswith('#'):
            return False
            
        # Filter out relative anchor URLs
        if '#' in url and not url.startswith('http'):
            return False
            
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc)  # Must have a domain
        except Exception:
            return False

    def extract_github_repo_name(self, github_url: str) -> Optional[str]:
        """Extract owner/repo from GitHub URL"""
        try:
            parsed = urlparse(github_url)
            if parsed.netloc.lower() in ["github.com", "www.github.com"]:
                path_parts = parsed.path.strip("/").split("/")
                if len(path_parts) >= 2:
                    return f"{path_parts[0]}/{path_parts[1]}"
        except Exception:
            pass
        return None


# Global parser instance
markdown_parser = MarkdownParser()
