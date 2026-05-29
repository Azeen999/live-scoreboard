import json
from dataclasses import dataclass, field


@dataclass
class ElementConfig:
    type: str  # "label", "digits", "timer", "foul_dots"
    geometry: dict  # {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0}
    font_size: int = 24
    color: str = "#ffffff"
    alignment: str = "center"
    font_family: str = ""
    format: str = ""  # timer format
    min_digits: int = 2  # for digits
    max_visible: int = 6  # for foul_dots
    dot_color: str = "#ffab00"
    dot_radius: int = 8
    spacing: int = 25


@dataclass
class BackgroundConfig:
    color: str = "#0a0a1a"
    gradient: bool = False
    gradient_from: str = "#0a0a1a"
    gradient_to: str = "#1a1a3a"
    opacity: float = 1.0  # 0.0=fully transparent, 1.0=fully opaque
    image: str = ""  # filename relative to template dir, e.g. "bg.png"


@dataclass
class TemplateConfig:
    template_id: str = ""
    name: str = ""
    template_dir: str = ""
    resolution_width: int = 1920
    resolution_height: int = 1080
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    elements: dict[str, ElementConfig] = field(default_factory=dict)
    font_family: str = "Microsoft YaHei"

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateConfig":
        bg_data = data.get("background", {})
        bg = BackgroundConfig(
            color=bg_data.get("color", "#0a0a1a"),
            gradient=bg_data.get("gradient", False),
            gradient_from=bg_data.get("gradient_from", "#0a0a1a"),
            gradient_to=bg_data.get("gradient_to", "#1a1a3a"),
            opacity=bg_data.get("opacity", 1.0),
            image=bg_data.get("image", ""),
        )
        res = data.get("resolution", {})
        elements = {}
        for elem_id, elem_data in data.get("elements", {}).items():
            elements[elem_id] = ElementConfig(
                type=elem_data.get("type", "label"),
                geometry=elem_data.get("geometry", {}),
                font_size=elem_data.get("font_size", 24),
                color=elem_data.get("color", "#ffffff"),
                alignment=elem_data.get("alignment", "center"),
                font_family=elem_data.get("font_family", ""),
                format=elem_data.get("format", ""),
                min_digits=elem_data.get("min_digits", 2),
                max_visible=elem_data.get("max_visible", 6),
                dot_color=elem_data.get("dot_color", "#ffab00"),
                dot_radius=elem_data.get("dot_radius", 8),
                spacing=elem_data.get("spacing", 25),
            )
        return cls(
            template_id=data.get("template_id", ""),
            name=data.get("name", ""),
            resolution_width=res.get("width", 1920),
            resolution_height=res.get("height", 1080),
            background=bg,
            elements=elements,
            font_family=data.get("global_style", {}).get("font_family", "Microsoft YaHei"),
        )


def load_template(template_dir: str) -> TemplateConfig:
    json_path = f"{template_dir}/template.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    config = TemplateConfig.from_dict(data)
    config.template_dir = template_dir
    return config
