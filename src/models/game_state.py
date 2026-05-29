from PySide6.QtCore import QObject, Signal
from src.models.sport_config import SportConfig
from src.config.sports import SPORTS, DEFAULT_SPORT_ID


class GameState(QObject):
    team_a_name_changed = Signal(str)
    team_b_name_changed = Signal(str)
    team_a_score_changed = Signal(int)
    team_b_score_changed = Signal(int)
    period_changed = Signal(int, int)
    timer_seconds_changed = Signal(int)
    timer_running_changed = Signal(bool)
    timer_expired = Signal()
    sport_changed = Signal(str)
    overtime_changed = Signal(bool)
    scores_reset = Signal()
    sides_swapped = Signal()
    template_changed = Signal(str)
    timer_mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sport_config = SPORTS[DEFAULT_SPORT_ID]
        self._team_a_name = "队伍 A"
        self._team_b_name = "队伍 B"
        self._team_a_score = 0
        self._team_b_score = 0
        self._period = 1
        self._timer_seconds = self._sport_config.period_duration_seconds
        self._is_running = False
        self._is_overtime = False
        self._template_id = "default"
        self._timer_mode = self._sport_config.timer_mode

    # ---- sport ----
    @property
    def sport_config(self) -> SportConfig:
        return self._sport_config

    def set_sport(self, sport_id: str):
        if sport_id not in SPORTS:
            return
        self._sport_config = SPORTS[sport_id]
        self._period = 1
        self._team_a_score = 0
        self._team_b_score = 0
        self._is_overtime = False
        self._is_running = False
        self._timer_mode = self._sport_config.timer_mode
        self._timer_seconds = self._sport_config.period_duration_seconds
        self.sport_changed.emit(sport_id)
        self.scores_reset.emit()
        self.timer_seconds_changed.emit(self._timer_seconds)
        self.timer_running_changed.emit(False)
        self.period_changed.emit(self._period, self._sport_config.periods_count)
        self.overtime_changed.emit(False)
        self.timer_mode_changed.emit(self._timer_mode)

    # ---- team names ----
    @property
    def team_a_name(self) -> str:
        return self._team_a_name

    def set_team_a_name(self, name: str):
        if name != self._team_a_name:
            self._team_a_name = name
            self.team_a_name_changed.emit(name)

    @property
    def team_b_name(self) -> str:
        return self._team_b_name

    def set_team_b_name(self, name: str):
        if name != self._team_b_name:
            self._team_b_name = name
            self.team_b_name_changed.emit(name)

    # ---- scores ----
    @property
    def team_a_score(self) -> int:
        return self._team_a_score

    @property
    def team_b_score(self) -> int:
        return self._team_b_score

    def increment_score(self, team: str, amount: int = 1):
        if team == "A":
            self._team_a_score = max(0, self._team_a_score + amount)
            self.team_a_score_changed.emit(self._team_a_score)
        elif team == "B":
            self._team_b_score = max(0, self._team_b_score + amount)
            self.team_b_score_changed.emit(self._team_b_score)

    # ---- period ----
    @property
    def period(self) -> int:
        return self._period

    @property
    def periods_count(self) -> int:
        return self._sport_config.periods_count

    def set_period(self, period: int):
        if 1 <= period <= self._sport_config.periods_count:
            self._period = period
            self._is_running = False
            self._timer_seconds = self._sport_config.period_duration_seconds
            self.period_changed.emit(self._period, self._sport_config.periods_count)
            self.timer_seconds_changed.emit(self._timer_seconds)
            self.timer_running_changed.emit(False)

    # ---- timer mode ----
    @property
    def timer_mode(self) -> str:
        return self._timer_mode

    def set_timer_mode(self, mode: str):
        if mode in ("countdown", "countup") and mode != self._timer_mode:
            self._timer_mode = mode
            self._is_running = False
            if mode == "countup":
                self._timer_seconds = 0
            else:
                self._timer_seconds = self._sport_config.period_duration_seconds
            self.timer_mode_changed.emit(mode)
            self.timer_seconds_changed.emit(self._timer_seconds)
            self.timer_running_changed.emit(False)

    # ---- timer ----
    @property
    def timer_seconds(self) -> int:
        return self._timer_seconds

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_timer_seconds(self, seconds: int):
        self._timer_seconds = max(0, seconds)
        self._is_running = False
        self.timer_seconds_changed.emit(self._timer_seconds)
        self.timer_running_changed.emit(False)

    def start_timer(self):
        self._is_running = True
        self.timer_running_changed.emit(True)

    def pause_timer(self):
        self._is_running = False
        self.timer_running_changed.emit(False)

    def reset_timer(self):
        self._is_running = False
        if self._timer_mode == "countup":
            self._timer_seconds = 0
        else:
            self._timer_seconds = self._sport_config.period_duration_seconds
        self.timer_seconds_changed.emit(self._timer_seconds)
        self.timer_running_changed.emit(False)

    def tick(self):
        if not self._is_running:
            return
        if self._timer_mode == "countdown":
            if self._timer_seconds > 0:
                self._timer_seconds -= 1
                self.timer_seconds_changed.emit(self._timer_seconds)
            if self._timer_seconds == 0:
                self._is_running = False
                self.timer_running_changed.emit(False)
                self.timer_expired.emit()
        else:
            self._timer_seconds += 1
            self.timer_seconds_changed.emit(self._timer_seconds)

    # ---- overtime ----
    @property
    def is_overtime(self) -> bool:
        return self._is_overtime

    def toggle_overtime(self):
        self._is_overtime = not self._is_overtime
        if self._is_overtime:
            self._timer_seconds = self._sport_config.overtime_duration_seconds
            self._is_running = False
            self.timer_seconds_changed.emit(self._timer_seconds)
            self.timer_running_changed.emit(False)
        else:
            self._timer_seconds = self._sport_config.period_duration_seconds
            self._is_running = False
            self.timer_seconds_changed.emit(self._timer_seconds)
            self.timer_running_changed.emit(False)
        self.overtime_changed.emit(self._is_overtime)

    # ---- reset all ----
    def reset_all(self):
        self._team_a_score = 0
        self._team_b_score = 0
        self._period = 1
        self._is_overtime = False
        self._is_running = False
        if self._timer_mode == "countup":
            self._timer_seconds = 0
        else:
            self._timer_seconds = self._sport_config.period_duration_seconds
        self.scores_reset.emit()
        self.team_a_score_changed.emit(0)
        self.team_b_score_changed.emit(0)
        self.period_changed.emit(1, self._sport_config.periods_count)
        self.timer_seconds_changed.emit(self._timer_seconds)
        self.timer_running_changed.emit(False)
        self.overtime_changed.emit(False)

    # ---- swap sides (scores only, layout unchanged) ----
    def swap_sides(self):
        self._team_a_score, self._team_b_score = self._team_b_score, self._team_a_score
        self._team_a_name, self._team_b_name = self._team_b_name, self._team_a_name
        self.sides_swapped.emit()
        self.team_a_score_changed.emit(self._team_a_score)
        self.team_b_score_changed.emit(self._team_b_score)
        self.team_a_name_changed.emit(self._team_a_name)
        self.team_b_name_changed.emit(self._team_b_name)

    # ---- template ----
    @property
    def template_id(self) -> str:
        return self._template_id

    def set_template(self, template_id: str):
        if template_id != self._template_id:
            self._template_id = template_id
            self.template_changed.emit(template_id)
