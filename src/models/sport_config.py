from dataclasses import dataclass, field


@dataclass
class SportConfig:
    sport_id: str
    name_zh: str
    name_en: str
    periods_count: int = 2
    period_labels: list = field(default_factory=lambda: ["上半场", "下半场"])
    period_duration_seconds: int = 1200
    max_score: int | None = None
    win_by_two: bool = False
    has_overtime: bool = False
    overtime_label: str = "加时赛"
    overtime_duration_seconds: int = 300
    track_fouls: bool = False
    foul_limit: int | None = None
    timer_mode: str = "countdown"  # "countdown" or "countup"
    score_increment_buttons: list = field(default_factory=lambda: [1])
    preset_durations: list = field(default_factory=list)
