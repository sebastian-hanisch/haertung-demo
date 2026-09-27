"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Buttons (Standardmuster aus dem Demo-Portfolio, wie in `kas_presets.py`)."""

import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import haer_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


def _int_choice(options):
    def cast(value):
        value = int(value)
        if value not in options:
            raise ValueError(value)
        return value
    return cast


def _float_choice(options):
    def cast(value):
        value = float(value)
        if value not in options:
            raise ValueError(value)
        return value
    return cast


def _choice_from(options):
    def cast(value):
        value = str(value)
        if value not in options:
            raise ValueError(value)
        return value
    return cast


SETTING_SPECS = {
    "kind_select": SettingSpec("kind", _choice_from(C.KINDS), "city"),
    "side_slider": SettingSpec("side", int, C.DEFAULT_SIDE, C.SIDE_MIN, C.SIDE_MAX),
    "blocked_select": SettingSpec("blocked", _float_choice(C.BLOCKED_OPTIONS), C.DEFAULT_BLOCKED),
    "nettype_select": SettingSpec("nettype", _choice_from(C.NETTYPES), "grid"),
    "nba_slider": SettingSpec("nba", int, C.DEFAULT_N_BA, C.N_BA_MIN, C.N_BA_MAX),
    "m0ba_slider": SettingSpec("m0ba", int, C.DEFAULT_M0_BA, C.M0_BA_MIN, C.M0_BA_MAX),
    "mba_slider": SettingSpec("mba", int, C.DEFAULT_M_BA, C.M_BA_MIN, C.M0_BA_MAX),
    "kbarbell_slider": SettingSpec("kbarbell", int, C.DEFAULT_BARBELL_K, C.BARBELL_K_MIN, C.BARBELL_K_MAX),
    "strategy_select": SettingSpec("strategy", _choice_from(C.STRATEGIES), "random"),
    "budget_slider": SettingSpec("budget", int, C.DEFAULT_BUDGET, C.BUDGET_MIN, C.BUDGET_MAX),
    "ntrials_slider": SettingSpec("ntrials", int, C.DEFAULT_N_TRIALS, C.N_TRIALS_MIN, C.N_TRIALS_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "haer_step": SettingSpec("step", _int_choice(tuple(C.STEPS)), 1),
}
PRESET_KEYS = {"kind": "kind_select", "side": "side_slider", "blocked": "blocked_select", "nettype": "nettype_select", "nba": "nba_slider", "m0ba": "m0ba_slider", "mba": "mba_slider",
               "kbarbell": "kbarbell_slider", "strategy": "strategy_select", "budget": "budget_slider", "ntrials": "ntrials_slider", "seed": "seed_input", "step": "haer_step"}
WIDGET_KEYS = {"side_slider": "side_widget", "blocked_select": "blocked_widget", "nettype_select": "nettype_widget", "nba_slider": "nba_widget", "m0ba_slider": "m0ba_widget",
               "mba_slider": "mba_widget", "kbarbell_slider": "kbarbell_widget", "strategy_select": "strategy_widget", "budget_slider": "budget_widget", "ntrials_slider": "ntrials_widget",
               "seed_input": "seed_widget"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    # m <= m0: nach dem Laden erzwingen (die Permalink-Werte werden unabhängig voneinander geladen)
    if st.session_state.get("mba_slider", C.DEFAULT_M_BA) > st.session_state.get("m0ba_slider", C.DEFAULT_M0_BA):
        st.session_state["mba_slider"] = st.session_state.get("m0ba_slider", C.DEFAULT_M0_BA)
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def store_from_widget(state_key):
    """Callback: übernimmt den Wert eines nur zeitweise sichtbaren Reglers in den dauerhaft gespeicherten Wert."""
    st.session_state[state_key] = st.session_state[WIDGET_KEYS[state_key]]


def push_to_widget(state_key):
    """Ist der Regler gerade sichtbar, muss ein geänderter gespeicherter Wert (Preset, Würfel) auch ihn selbst ändern."""
    widget_key = WIDGET_KEYS[state_key]
    if widget_key in st.session_state:
        st.session_state[widget_key] = st.session_state[state_key]


def apply_preset(name):
    p = C.PRESETS[name]
    for key, state_key in PRESET_KEYS.items():
        if key in p:
            st.session_state[state_key] = p[key]
    for state_key in WIDGET_KEYS:
        push_to_widget(state_key)


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
    push_to_widget("seed_input")
