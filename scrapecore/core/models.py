"""
Domain entities and data structures for AOV ScrapeCore.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Skill:
    """Represents a champion skill or passive ability."""
    id: str
    type: str
    name: str
    icon_url: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "icon_url": self.icon_url,
            "description": self.description
        }


@dataclass
class Skin:
    """Represents a champion skin / splash art."""
    id: str
    name: str
    image_url: str
    thumb_url: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "image_url": self.image_url,
            "thumb_url": self.thumb_url
        }


@dataclass
class Champion:
    """Represents a champion entity."""
    id: str
    name: str
    url: str
    avatar_url: str
    roles: List[str] = field(default_factory=list)
    skins: List[Skin] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "avatar_url": self.avatar_url,
            "roles": self.roles,
            "skins": [s.to_dict() if isinstance(s, Skin) else s for s in self.skins],
            "skills": [sk.to_dict() if isinstance(sk, Skill) else sk for sk in self.skills]
        }


@dataclass
class DownloadResult:
    """Represents the results of an asset download session."""
    hero: str
    avatar: int = 0
    skins: int = 0
    skills: int = 0
    failed: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "hero": self.hero,
            "avatar": self.avatar,
            "skins": self.skins,
            "skills": self.skills,
            "failed": self.failed
        }
        if self.error:
            d["error"] = self.error
        return d
