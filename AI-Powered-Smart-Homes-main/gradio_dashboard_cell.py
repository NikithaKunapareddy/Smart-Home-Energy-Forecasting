"""
SmartHome Energy Dashboard — India Edition  v4
=================================================
NEW IN v4:
  • Dynamic temperature slider — min / max / default / step auto-update on season change
  • Impossible combinations blocked (Summer 11°C, Winter 42°C, etc.)
  • Live helper-text label below slider: "Typical Summer India Range: 28–45°C"
  • If current temp is out of the new season's range, it is clamped to nearest valid value
  • All v3 features (Why This Prediction, 2 dynamic charts) preserved unchanged

Season → Temperature bounds (Indian conditions):
    Winter  : 5–28°C   default 18°C  (North India nights 5°C, South days 28°C)
    Spring  : 20–34°C  default 28°C  (March heat build-up)
    Summer  : 28–45°C  default 36°C  (Apr–Jun peak heat)
    Fall    : 22–34°C  default 29°C  (Jul–Nov: Monsoon + Post-Monsoon combined)
"""

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────
APPLIANCES = ['Air Conditioning','Heater','Fridge','Washing Machine',
              'Dishwasher','Oven','Microwave','TV','Computer','Lights']

SEASONS = ['Winter', 'Spring', 'Summer', 'Fall']

# Temperature bounds per season — the core of this update
SEASON_TEMP = {
    #           min   max  default   step  label
    'Winter': ( 5,   28,   18,      0.5, 'Winter India: 5–28°C  (North 5°C nights → South 28°C days)'),
    'Spring': (20,   34,   28,      0.5, 'Spring India: 20–34°C  (March warm build-up)'),
    'Summer': (28,   45,   36,      0.5, 'Summer India: 28–45°C  (Apr–Jun peak heat)'),
    'Fall':   (22,   34,   29,      0.5, 'Fall / Monsoon India: 22–34°C  (Jul–Nov humid)'),
}

SEASON_MONTH_CHOICES = {
    'Winter': ['Dec (12)', 'Jan (1)', 'Feb (2)'],
    'Spring': ['Mar (3)'],
    'Summer': ['Apr (4)', 'May (5)', 'Jun (6)'],
    'Fall':   ['Jul (7)', 'Aug (8)', 'Sep (9)', 'Oct (10)', 'Nov (11)'],
}
SEASON_MONTH_DEFAULT = {
    'Winter': 'Jan (1)',
    'Spring': 'Mar (3)',
    'Summer': 'May (5)',
    'Fall':   'Aug (8)',
}

DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

# (season, temp, hour, month, household_size, day_of_week)
# FIXES APPLIED:
#   Fridge  → season=True  (summer compressor load is higher than winter)
#   Lights  → day_of_week=True  (weekend = more people home = more rooms lit)
#   TV      → day_of_week already True — unchanged
#   Computer→ day_of_week already True — unchanged
RELEVANT = {
    'Air Conditioning': (True,  True,  True,  False, True,  False),
    'Heater':           (True,  True,  True,  False, True,  False),
    'Fridge':           (True,  True,  False, False, True,  False),
    'Washing Machine':  (False, False, True,  False, True,  True ),
    'Dishwasher':       (False, False, True,  False, True,  False),
    'Oven':             (False, False, True,  False, True,  False),
    'Microwave':        (False, False, True,  False, True,  False),
    'TV':               (False, False, True,  False, True,  True ),
    'Computer':         (False, False, True,  False, True,  True ),
    'Lights':           (True,  False, True,  False, True,  True ),
}

DEFAULTS = {'season':'Summer','temp':36,'hour':14,'month':5,'hs':3,'dow':2}


# ─────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────
def _tb(h):
    if 5 <= h < 12:  return 'Morning'
    if 12 <= h < 17: return 'Afternoon'
    if 17 <= h < 21: return 'Evening'
    return 'Night'

def _parse_month_label(label):
    """'May (5)' → 5"""
    return int(label.split('(')[1].rstrip(')'))

def _build_row(appliance, season, temperature, hour, month, household_size, day_of_week):
    """Build a single feature row for the model."""
    rel        = RELEVANT[appliance]
    eff_season = season                  if rel[0] else DEFAULTS['season']
    eff_temp   = float(temperature)      if rel[1] else DEFAULTS['temp']
    eff_hour   = int(hour)               if rel[2] else DEFAULTS['hour']
    eff_month  = int(month)              if rel[3] else DEFAULTS['month']
    eff_hs     = int(household_size)     if rel[4] else DEFAULTS['hs']
    eff_dow    = DAYS.index(day_of_week) if rel[5] else DEFAULTS['dow']

    # Hard-clamp temperature to the season's valid range (safety net)
    t_min, t_max = SEASON_TEMP[eff_season][0], SEASON_TEMP[eff_season][1]
    eff_temp = max(t_min, min(t_max, eff_temp))

    row = {
        'Outdoor Temperature (°C)': eff_temp,
        'Household Size':           eff_hs,
        'Hour':                     eff_hour,
        'Month':                    eff_month,
        'DayOfWeek':                eff_dow,
        'IsWeekend':                int(eff_dow >= 5),
        f'Appliance Type_{appliance}': 1,
        f'Season_{eff_season}':        1,
        f'TimeOfDay_{_tb(eff_hour)}':  1,
    }
    return row, eff_season, eff_temp, eff_hour, eff_month, eff_hs, eff_dow


# ─────────────────────────────────────────────────────────────────
# SEASON → TEMP SLIDER + HELPER TEXT UPDATE CALLBACK
# ─────────────────────────────────────────────────────────────────
def _temp_badge_html(season):
    """Render the live helper-text pill shown below the temperature slider."""
    t_min, t_max, t_def, _, label_text = SEASON_TEMP[season]
    icons = {'Winter':'❄️','Spring':'🌸','Summer':'🔥','Fall':'🌧️'}
    colors = {
        'Winter': ('#EFF6FF','#2563EB','#BFDBFE'),
        'Spring': ('#FFF7ED','#EA580C','#FED7AA'),
        'Summer': ('#FEF2F2','#DC2626','#FECACA'),
        'Fall':   ('#F0FDF4','#16A34A','#BBF7D0'),
    }
    bg, fg, border = colors[season]
    return (
        f'<div style="display:flex;align-items:center;gap:8px;'
        f'background:{bg};border:1px solid {border};border-radius:8px;'
        f'padding:7px 12px;margin-top:4px;font-family:\'Plus Jakarta Sans\',sans-serif;">'
        f'<span style="font-size:14px">{icons[season]}</span>'
        f'<span style="font-size:11.5px;font-weight:600;color:{fg}">'
        f'Typical {label_text}</span>'
        f'</div>'
    )

def update_season_controls(season):
    """
    Called when Season dropdown changes.
    Returns updates for: month_dd, temp slider, temp helper HTML.
    """
    t_min, t_max, t_def, t_step, _ = SEASON_TEMP[season]
    choices       = SEASON_MONTH_CHOICES[season]
    default_month = SEASON_MONTH_DEFAULT[season]
    helper_html   = _temp_badge_html(season)

    return (
        gr.update(choices=choices, value=default_month),
        gr.update(minimum=t_min, maximum=t_max,
                  value=t_def, step=t_step,
                  label=f'Outdoor Temperature (°C)  [{t_min}–{t_max}°C]'),
        helper_html,
    )

def update_controls(app):
    """Show/hide controls based on appliance relevance."""
    rel = RELEVANT[app]
    return (
        gr.update(visible=rel[0]),   # season
        gr.update(visible=rel[1]),   # temp
        gr.update(visible=rel[1]),   # temp_info (same visibility as temp)
        gr.update(visible=rel[2]),   # hour
        gr.update(visible=False),    # month_dd (hidden, controlled by season)
        gr.update(visible=True),     # hs always visible
        gr.update(visible=rel[5]),   # day_of_week
    )


# ─────────────────────────────────────────────────────────────────
# WHY THIS PREDICTION HTML BUILDER
# ─────────────────────────────────────────────────────────────────
def build_why_html(appliance, eff_season, eff_temp, eff_hour, eff_hs,
                   predicted, baseline, low_th, high_th, sev, diff_pct):
    def badge(icon, text, color):
        palettes = {
            'red':   ('FEF2F2','DC2626','FEE2E2'),
            'green': ('F0FDF4','16A34A','DCFCE7'),
            'blue':  ('EFF6FF','2563EB','DBEAFE'),
            'amber': ('FFFBEB','D97706','FEF3C7'),
        }
        bg, fg, border = palettes.get(color, palettes['blue'])
        return (f'<div style="display:flex;align-items:flex-start;gap:10px;'
                f'background:#{bg};border:1px solid #{border};border-radius:10px;'
                f'padding:10px 13px;margin-bottom:8px;">'
                f'<span style="font-size:16px;line-height:1.4">{icon}</span>'
                f'<span style="font-size:13px;color:#{fg};font-weight:500;line-height:1.5">{text}</span>'
                f'</div>')

    factors    = []
    time_block = _tb(eff_hour)

    if appliance == 'Air Conditioning':
        if eff_temp >= 38:
            factors.append(badge('🌡️', f'Extreme heat ({eff_temp}°C) — AC compressor runs at maximum load.', 'red'))
        elif eff_temp >= 32:
            factors.append(badge('☀️', f'High temperature ({eff_temp}°C) significantly increases cooling demand.', 'red'))
        elif eff_temp >= 26:
            factors.append(badge('🌤', f'Moderate temperature ({eff_temp}°C) — AC operates within normal range.', 'blue'))
        else:
            factors.append(badge('❄️', f'Cool conditions ({eff_temp}°C) reduce AC workload considerably.', 'green'))
        season_map = {
            'Summer': ('🔥','Summer season drives peak AC usage across all Indian regions.','red'),
            'Fall':   ('💧','Monsoon/post-monsoon humidity forces the AC to work harder (dehumidification load).','amber'),
            'Spring': ('🌸','Spring season — temperatures rising but not yet at summer peak.','blue'),
            'Winter': ('🧊','Winter season greatly reduces cooling requirement.','green'),
        }
        ico,txt,col = season_map.get(eff_season, ('🌡️','Seasonal effect on AC.','blue'))
        factors.append(badge(ico,txt,col))
        tb_map = {
            'Afternoon': ('⏰','Afternoon (12–5 PM) is peak solar heat gain — highest AC demand period.','red'),
            'Evening':   ('🌆','Evening (5–9 PM) — residual heat keeps AC demand elevated.','amber'),
            'Morning':   ('🌅','Morning hours — temperature still rising, AC demand moderate.','blue'),
            'Night':     ('🌙','Night hours — ambient temperature drops, reducing AC load.','green'),
        }
        ico,txt,col = tb_map.get(time_block, ('⏱','Time-of-day effect.','blue'))
        factors.append(badge(ico,txt,col))
        if eff_hs >= 4:
            factors.append(badge('👨‍👩‍👧‍👦', f'Large household ({eff_hs} people) adds indoor heat load.', 'amber'))
        elif eff_hs <= 2:
            factors.append(badge('🏠', f'Small household ({eff_hs} people) — lower occupancy.', 'green'))
        else:
            factors.append(badge('👥', f'Household of {eff_hs} — moderate occupancy, typical AC demand.', 'blue'))

    elif appliance == 'Heater':
        if eff_temp <= 8:
            factors.append(badge('🥶', f'Very cold outside ({eff_temp}°C) — heater runs at high intensity.', 'red'))
        elif eff_temp <= 15:
            factors.append(badge('🌨', f'Cold conditions ({eff_temp}°C) — heater usage is expected and elevated.', 'amber'))
        elif eff_temp <= 22:
            factors.append(badge('🌡️', f'Mild temperature ({eff_temp}°C) — heater usage is low to moderate.', 'blue'))
        else:
            factors.append(badge('☀️', f'Warm conditions ({eff_temp}°C) — heater demand is minimal in India.', 'green'))
        if eff_season == 'Winter':
            factors.append(badge('❄️', 'Winter season — primary heating season in North India (Dec–Feb).', 'red'))
        elif eff_season == 'Spring':
            factors.append(badge('🌱', 'Early spring — occasional chilly mornings may require short heating bursts.', 'blue'))
        else:
            factors.append(badge('🌞', 'Summer/Fall — heater demand is near-zero in Indian conditions.', 'green'))
        if time_block in ('Night','Morning') and eff_season == 'Winter':
            factors.append(badge('🌙', 'Night/early morning in winter — coldest part of the day, peak heater demand.', 'red'))
        elif time_block == 'Afternoon':
            factors.append(badge('🌤', 'Afternoon — sun warms the environment, reducing heater need.', 'green'))
        else:
            factors.append(badge('⏱', f'{time_block} hours — moderate heating requirement.', 'blue'))

    elif appliance == 'Fridge':
        factors.append(badge('🔄', 'Fridge runs continuously 24/7 — consumption varies mainly with ambient temperature and season.', 'blue'))
        if eff_season == 'Summer':
            factors.append(badge('🔥', 'Summer season — sustained high ambient temperatures force the compressor to run longer duty cycles.', 'red'))
        elif eff_season == 'Fall':
            factors.append(badge('💧', 'Fall/Monsoon — warm and humid conditions moderately increase compressor load.', 'amber'))
        elif eff_season == 'Spring':
            factors.append(badge('🌸', 'Spring — warming temperatures begin to increase compressor demand slightly.', 'blue'))
        else:
            factors.append(badge('❄️', 'Winter — cool ambient temperatures allow the compressor to run efficiently with lower energy draw.', 'green'))
        if eff_temp >= 35:
            factors.append(badge('🌡️', f'High ambient ({eff_temp}°C) forces the compressor to work harder.', 'red'))
        elif eff_temp >= 28:
            factors.append(badge('☀️', f'Warm ambient ({eff_temp}°C) — slightly elevated compressor duty cycle.', 'amber'))
        else:
            factors.append(badge('❄️', f'Cool ambient ({eff_temp}°C) — compressor runs efficiently.', 'green'))
        if eff_hs >= 4:
            factors.append(badge('👨‍👩‍👧‍👦', f'{eff_hs} people — more frequent door openings increase load.', 'amber'))
        else:
            factors.append(badge('🚪', f'Household of {eff_hs} — door opening frequency is typical.', 'blue'))

    elif appliance == 'Washing Machine':
        if eff_hs >= 4:
            factors.append(badge('👗', f'Large household ({eff_hs} people) — more loads per day.', 'red'))
        elif eff_hs == 3:
            factors.append(badge('👕', 'Household of 3 — average laundry frequency.', 'blue'))
        else:
            factors.append(badge('✅', f'Small household ({eff_hs} people) — fewer loads, efficient usage.', 'green'))
        if time_block in ('Morning','Afternoon'):
            factors.append(badge('⏰', f'{time_block} run — off-peak hours, good for cost savings.', 'green'))
        else:
            factors.append(badge('⚡', f'{time_block} run — higher grid load period.', 'amber'))

    elif appliance == 'Dishwasher':
        if eff_hs >= 4:
            factors.append(badge('🍽️', f'Large household ({eff_hs} people) — more dishes, likely multiple cycles.', 'red'))
        else:
            factors.append(badge('🍽️', f'Household of {eff_hs} — standard dishwasher usage.', 'blue'))
        if eff_hour in range(8,10) or eff_hour in range(13,15) or eff_hour in range(20,22):
            factors.append(badge('🍛', 'Post-meal hours — dishwasher usage aligns with typical cleanup times.', 'amber'))
        else:
            factors.append(badge('⏳', 'Off-meal hours — lower-than-typical dishwasher activity expected.', 'green'))

    elif appliance == 'Oven':
        if eff_hour in range(7,10):
            factors.append(badge('🌅', 'Breakfast window (7–10 AM) — oven demand elevated.', 'amber'))
        elif eff_hour in range(12,15):
            factors.append(badge('🍱', 'Lunch window (12–3 PM) — cooking activity at peak.', 'red'))
        elif eff_hour in range(19,22):
            factors.append(badge('🌆', 'Dinner window (7–10 PM) — highest oven usage period.', 'red'))
        else:
            factors.append(badge('💤', 'Off-meal hours — oven is typically idle.', 'green'))
        if eff_hs >= 4:
            factors.append(badge('👨‍👩‍👧‍👦', f'Large household ({eff_hs} people) — longer cooking durations.', 'amber'))
        elif eff_hs <= 2:
            factors.append(badge('🍳', f'Small household ({eff_hs} people) — shorter cooking cycles.', 'green'))
        else:
            factors.append(badge('🍽️', f'Household of {eff_hs} — typical cooking load.', 'blue'))

    elif appliance == 'Microwave':
        if eff_hour in range(7,10) or eff_hour in range(12,15) or eff_hour in range(19,22):
            factors.append(badge('⚡', 'Meal window — microwave sees its highest usage during meal times.', 'amber'))
        else:
            factors.append(badge('💤', 'Off-meal hours — microwave is typically idle.', 'green'))
        factors.append(badge('✅', 'Microwave is inherently energy-efficient — low consumption regardless of timing.', 'blue'))

    elif appliance == 'TV':
        if time_block == 'Evening':
            factors.append(badge('📺', 'Prime time (5–9 PM) — highest TV viewership period, elevated consumption.', 'red'))
        elif time_block == 'Night':
            factors.append(badge('🌙', 'Night viewing — moderate TV usage, some households still active.', 'amber'))
        elif time_block == 'Morning':
            factors.append(badge('☀️', 'Morning — TV usage is low (news/breakfast viewing only).', 'green'))
        else:
            factors.append(badge('⏱', 'Daytime — occasional background TV use.', 'blue'))
        if eff_hs >= 4:
            factors.append(badge('👨‍👩‍👧‍👦', f'{eff_hs} people — multiple screens may run simultaneously.', 'amber'))
        else:
            factors.append(badge('📺', f'Household of {eff_hs} — single-screen usage most likely.', 'blue'))

    elif appliance == 'Computer':
        if 9 <= eff_hour <= 18:
            factors.append(badge('💻', 'Core work/study hours (9 AM–6 PM) — highest computer utilisation.', 'red'))
        elif time_block == 'Evening':
            factors.append(badge('🖥', 'Evening hours — personal computing and entertainment use.', 'amber'))
        elif time_block == 'Night':
            factors.append(badge('🌙', 'Late night — most systems idle or in sleep mode.', 'green'))
        else:
            factors.append(badge('🌅', 'Early morning — low computer activity expected.', 'green'))
        if eff_hs >= 4:
            factors.append(badge('👨‍👩‍👧‍👦', f'{eff_hs} people — multiple devices likely running simultaneously.', 'amber'))

    elif appliance == 'Lights':
        if time_block == 'Night' or eff_hour <= 5:
            factors.append(badge('💡', 'Night hours — all indoor lighting required, peak consumption.', 'red'))
        elif time_block == 'Evening':
            factors.append(badge('🌆', 'Evening (5–9 PM) — lights switched on across all rooms.', 'red'))
        elif time_block == 'Morning':
            factors.append(badge('🌅', 'Morning — partial lighting alongside natural daylight.', 'amber'))
        else:
            factors.append(badge('☀️', 'Daytime — natural sunlight available; artificial lighting minimal.', 'green'))
        if eff_season == 'Winter':
            factors.append(badge('❄️', 'Winter — shorter days mean lights are needed earlier and longer.', 'amber'))
        elif eff_season == 'Summer':
            factors.append(badge('☀️', 'Summer — longest daylight hours reduce total daily lighting demand.', 'green'))
        if eff_hs >= 4:
            factors.append(badge('💡', f'{eff_hs} people — more rooms actively used, more lights on simultaneously.', 'amber'))

    # Conclusion badge
    if sev == 'high':
        c_col='#DC2626'; c_bg='#FEF2F2'; c_brd='#FECACA'; c_ico='⚠️'
        c_txt = (f'<strong>Result: HIGH consumption</strong> — '
                 f'Predicted {predicted:.3f} kWh is {diff_pct:+.1f}% above the {appliance} median. '
                 f'The factors above are pushing usage beyond the normal range ({round(low_th,2)}–{round(high_th,2)} kWh).')
    elif sev == 'low':
        c_col='#16A34A'; c_bg='#F0FDF4'; c_brd='#BBF7D0'; c_ico='✅'
        c_txt = (f'<strong>Result: EFFICIENT usage</strong> — '
                 f'Predicted {predicted:.3f} kWh is {abs(diff_pct):.1f}% below the {appliance} median. '
                 f'Current conditions favour low energy demand for this appliance.')
    else:
        c_col='#2563EB'; c_bg='#EFF6FF'; c_brd='#BFDBFE'; c_ico='🟢'
        c_txt = (f'<strong>Result: NORMAL range</strong> — '
                 f'Predicted {predicted:.3f} kWh sits within the typical range '
                 f'({round(low_th,2)}–{round(high_th,2)} kWh) for {appliance}. '
                 f'No dominant factor is pushing consumption unusually high or low.')

    factors_html = "\n".join(factors)
    return f"""
<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;
            padding:18px 20px;margin-top:4px;
            box-shadow:0 1px 4px rgba(0,0,0,0.04),0 4px 12px rgba(0,0,0,0.03);">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;
              padding-bottom:12px;border-bottom:1px solid #F1F5F9;">
    <div style="width:32px;height:32px;background:linear-gradient(135deg,#1D4ED8,#4F46E5);
                border-radius:8px;display:grid;place-items:center;font-size:15px;flex-shrink:0;">🔍</div>
    <div>
      <div style="font-size:13px;font-weight:700;color:#0F172A;letter-spacing:-.01em;">Why This Prediction?</div>
      <div style="font-size:11px;color:#94A3B8;margin-top:1px;">
        Factor-by-factor analysis for <strong style="color:#1D4ED8">{appliance}</strong>
      </div>
    </div>
  </div>
  {factors_html}
  <div style="display:flex;align-items:flex-start;gap:10px;
              background:{c_bg};border:1.5px solid {c_brd};border-radius:10px;
              padding:12px 14px;margin-top:10px;">
    <span style="font-size:18px;line-height:1.3">{c_ico}</span>
    <span style="font-size:13px;color:{c_col};line-height:1.6">{c_txt}</span>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────
# DYNAMIC CHART BUILDERS
# ─────────────────────────────────────────────────────────────────
def build_bar_chart(appliance, predicted, baseline, low_th, high_th):
    import plotly.graph_objects as go
    categories = ['Predicted', 'Appliance Median', 'Normal Range Max']
    values     = [predicted, baseline, round(high_th, 3)]
    colors     = []
    for cat in categories:
        if cat == 'Predicted':
            colors.append('#DC2626' if predicted >= high_th else ('#16A34A' if predicted <= low_th else '#2563EB'))
        elif cat == 'Appliance Median':
            colors.append('#94A3B8')
        else:
            colors.append('#F59E0B')
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories, y=values, marker_color=colors, marker_line_width=0,
        text=[f'{v:.3f} kWh' for v in values], textposition='outside',
        textfont=dict(size=12, family='Plus Jakarta Sans, sans-serif', color='#1E293B'),
        hovertemplate='<b>%{x}</b><br>%{y:.3f} kWh<extra></extra>', width=0.45,
    ))
    fig.add_hrect(y0=low_th, y1=high_th, fillcolor='rgba(34,197,94,0.08)', line_width=0,
                  annotation_text=f"Normal range: {round(low_th,2)}–{round(high_th,2)} kWh",
                  annotation_position="top right",
                  annotation_font_size=10, annotation_font_color='#16A34A')
    status_label = 'HIGH ⚠️' if predicted >= high_th else ('EFFICIENT ✅' if predicted <= low_th else 'NORMAL 🟢')
    status_color = '#DC2626' if predicted >= high_th else ('#16A34A' if predicted <= low_th else '#2563EB')
    fig.update_layout(
        title=dict(
            text=f'<b>Consumption Analysis — {appliance}</b>   <span style="color:{status_color};font-size:13px">{status_label}</span>',
            font=dict(size=14, family='Plus Jakarta Sans, sans-serif', color='#0F172A'), x=0, xanchor='left'),
        yaxis=dict(title='Energy (kWh)', title_font=dict(size=11, color='#64748B'),
                   tickfont=dict(size=10, color='#64748B'), gridcolor='#F1F5F9',
                   zeroline=False, range=[0, max(values) * 1.3]),
        xaxis=dict(tickfont=dict(size=12, family='Plus Jakarta Sans, sans-serif', color='#1E293B'), tickangle=0),
        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
        margin=dict(l=40, r=20, t=55, b=30), height=320, showlegend=False,
        font=dict(family='Plus Jakarta Sans, sans-serif'),
    )
    return fig


def build_hourly_chart(appliance, season, temperature, month_label, household_size, day_of_week, selected_hour):
    import plotly.graph_objects as go
    month = _parse_month_label(month_label)
    hours = list(range(24))
    preds = []
    for h in hours:
        row, *_ = _build_row(appliance, season, temperature, h, month, household_size, day_of_week)
        inp = pd.DataFrame([row]).reindex(columns=FEATURE_COLS, fill_value=0)
        preds.append(round(max(0.0, float(prod_model.predict(inp)[0])), 3))
    sel_hour     = int(selected_hour)
    point_colors = ['#DC2626' if h == sel_hour else '#2563EB' for h in hours]
    point_sizes  = [12 if h == sel_hour else 5 for h in hours]
    fig = go.Figure()
    block_colors = {
        'Night':     'rgba(30,41,59,0.04)',
        'Morning':   'rgba(251,191,36,0.06)',
        'Afternoon': 'rgba(239,68,68,0.05)',
        'Evening':   'rgba(99,102,241,0.06)',
    }
    for name, x0, x1 in [('Night',0,5),('Morning',5,12),('Afternoon',12,17),('Evening',17,21),('Night2',21,23)]:
        fig.add_vrect(x0=x0, x1=x1,
                      fillcolor=block_colors['Night' if 'Night' in name else name],
                      line_width=0)
    fig.add_trace(go.Scatter(
        x=hours, y=preds, mode='lines+markers',
        line=dict(color='#2563EB', width=2.5, shape='spline'),
        marker=dict(color=point_colors, size=point_sizes, line=dict(color='#FFFFFF', width=1.5)),
        hovertemplate='<b>%{x:02d}:00</b>  →  %{y:.3f} kWh<extra></extra>', name='Predicted kWh',
    ))
    fig.add_vline(x=sel_hour, line=dict(color='#DC2626', width=1.5, dash='dot'),
                  annotation_text=f'  Selected: {sel_hour:02d}:00',
                  annotation_font_size=10, annotation_font_color='#DC2626',
                  annotation_position='top right')
    peak_h = preds.index(max(preds))
    fig.add_annotation(x=peak_h, y=max(preds), text=f'Peak {max(preds):.3f}',
                       showarrow=True, arrowhead=2, arrowsize=1, arrowcolor='#DC2626',
                       font=dict(size=10, color='#DC2626'), ax=20, ay=-30,
                       bgcolor='#FEF2F2', bordercolor='#FECACA', borderwidth=1, borderpad=4)
    fig.update_layout(
        title=dict(
            text=f'<b>Hourly Prediction Trend — {appliance}</b>   <span style="font-size:11px;color:#64748B">{season} · {temperature}°C · {household_size} people</span>',
            font=dict(size=14, family='Plus Jakarta Sans, sans-serif', color='#0F172A'), x=0, xanchor='left'),
        xaxis=dict(title='Hour of Day', title_font=dict(size=11, color='#64748B'),
                   tickmode='array', tickvals=list(range(0,24,3)),
                   ticktext=[f'{h:02d}:00' for h in range(0,24,3)],
                   tickfont=dict(size=10, color='#64748B'), gridcolor='#F8FAFC', zeroline=False),
        yaxis=dict(title='Predicted kWh', title_font=dict(size=11, color='#64748B'),
                   tickfont=dict(size=10, color='#64748B'), gridcolor='#F1F5F9', zeroline=False),
        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
        margin=dict(l=45, r=20, t=55, b=40), height=330, showlegend=False,
        font=dict(family='Plus Jakarta Sans, sans-serif'), hovermode='x unified',
    )
    return fig


# ─────────────────────────────────────────────────────────────────
# MAIN PREDICT FUNCTION
# ─────────────────────────────────────────────────────────────────
def predict_and_recommend(appliance, season, temperature, hour, month_label,
                           household_size, day_of_week):
    month = _parse_month_label(month_label) if isinstance(month_label, str) else int(month_label)
    row, eff_season, eff_temp, eff_hour, eff_month, eff_hs, eff_dow = _build_row(
        appliance, season, temperature, hour, month, household_size, day_of_week
    )
    inp       = pd.DataFrame([row]).reindex(columns=FEATURE_COLS, fill_value=0)
    predicted = round(float(prod_model.predict(inp)[0]), 3)

    low_th   = float(app_thresholds.loc[appliance,'low'])  if appliance in app_thresholds.index else 0.3
    high_th  = float(app_thresholds.loc[appliance,'high']) if appliance in app_thresholds.index else 1.5
    baseline = round(float(app_median.get(appliance, 1.0)), 3)
    diff_pct = round(((predicted - baseline) / baseline) * 100, 1)

    if predicted >= high_th:
        status = f"⚠️  HIGH  ·  {diff_pct:+.1f}% above median  (>{round(high_th,2)} kWh)"
        sev    = "high"
    elif predicted <= low_th:
        status = f"✅  EFFICIENT  ·  {abs(diff_pct):.1f}% below median  (<{round(low_th,2)} kWh)"
        sev    = "low"
    else:
        status = f"🟢  NORMAL  ·  within typical range  ({round(low_th,2)}–{round(high_th,2)} kWh)"
        sev    = "normal"

    # Recommendations
    recs = []
    rel  = RELEVANT[appliance]
    h    = eff_hour
    if sev == "high":
        recs.append(f"⚠️  {appliance} is consuming {diff_pct:.1f}% more than its typical median.")
    elif sev == "low":
        recs.append(f"✅  {appliance} is running efficiently — {abs(diff_pct):.1f}% below typical median.")
    else:
        recs.append(f"🟢  {appliance} consumption is within the normal range.")

    if rel[2] and 18 <= h <= 22:
        recs.append("⏰  Evening peak (6–10 PM). Shift usage to off-peak (11 PM–5 AM) for lower electricity bills.")
    if appliance == 'Air Conditioning' and eff_temp > 35:
        recs.append("❄️  Extreme heat! Set AC to 24–26°C instead of max — saves up to 20% energy.")
    if appliance == 'Air Conditioning' and eff_season == 'Summer':
        recs.append("🌀  Use ceiling fans with AC — can raise thermostat by 2°C comfortably.")
    if appliance == 'Air Conditioning' and eff_season == 'Fall':
        recs.append("💧  Monsoon humidity makes AC work harder. Use 'dry mode' to dehumidify efficiently.")
    if appliance == 'Heater' and eff_temp < 10:
        recs.append("🔥  Very cold outside! Use a timer and seal windows to reduce heat loss significantly.")
    if appliance == 'Heater' and eff_season == 'Winter':
        recs.append("🧥  Set Heater to 18–20°C. Layer clothing rather than running it higher.")
    if appliance == 'Fridge':
        recs.append("🌡️  Keep Fridge at 3–5°C. Minimise door openings and check door seals monthly.")
    if appliance == 'Fridge' and eff_temp > 35:
        recs.append("☀️  High summer temperatures increase Fridge load — ensure 5 cm clearance around it.")
    if appliance == 'Fridge' and eff_season == 'Summer':
        recs.append("🌀  Summer season raises compressor duty — avoid placing hot food directly into the fridge.")
    if appliance in ['Washing Machine','Dishwasher'] and eff_hs >= 4:
        recs.append(f"🏠  Large household: Run {appliance} with full loads only and use eco mode (saves ~30%).")
    if appliance == 'Washing Machine':
        recs.append("🌊  Use cold water wash (20–30°C) — saves ~90% of the energy used for heating water.")
    if appliance == 'Oven' and eff_hs <= 2:
        recs.append("🍳  Small household: A microwave or air fryer uses 70% less energy than a full oven.")
    if appliance in ['TV','Computer'] and h >= 22:
        recs.append(f"🔌  Power OFF {appliance} completely at night — standby mode draws phantom load.")
    if appliance == 'Computer' and rel[5] and eff_dow < 5:
        recs.append("💻  Weekday usage: Enable power-saving/sleep mode during idle periods.")
    if appliance == 'Lights' and (h >= 18 or h <= 6):
        recs.append("💡  Night usage: Switch to LED bulbs — 75% less energy than incandescent bulbs.")
    if appliance == 'Lights' and eff_season == 'Summer' and 8 <= h <= 18:
        recs.append("☀️  Long summer days: Use natural daylight and keep lights off during daytime.")
    if appliance == 'Lights' and rel[5] and eff_dow >= 5:
        recs.append("🏠  Weekend — more people home. Switch off lights in unoccupied rooms.")
    if appliance == 'Microwave':
        recs.append("⚡  Microwave is already energy-efficient. Prefer it over the Oven for reheating leftovers.")

    recs_text = "\n\n".join(recs)

    used = []
    if rel[0]: used.append(f"Season: {eff_season}")
    if rel[1]: used.append(f"Temp: {eff_temp}°C")
    if rel[2]: used.append(f"Time: {eff_hour}:00 ({_tb(eff_hour)})")
    if rel[3]: used.append(f"Month: {eff_month}")
    if rel[4]: used.append(f"Household: {eff_hs}")
    if rel[5]: used.append(f"Day: {day_of_week}")
    used_str     = "  ·  ".join(used)
    baseline_str = f"Median: {baseline} kWh  ·  Normal: {round(low_th,2)} – {round(high_th,2)} kWh"

    hour_avg = (df.groupby('Hour')['Energy Consumption (kWh)'].mean().round(3)
                  .reset_index().rename(columns={'Energy Consumption (kWh)':'Avg kWh'}))
    app_avg  = (df.groupby('Appliance Type')['Energy Consumption (kWh)'].mean().round(3)
                  .sort_values(ascending=False).reset_index()
                  .rename(columns={'Appliance Type':'Appliance','Energy Consumption (kWh)':'Avg kWh'}))
    sea_avg  = (df.groupby('Season')['Energy Consumption (kWh)'].mean().round(3)
                  .reset_index().rename(columns={'Energy Consumption (kWh)':'Avg kWh'}))

    why_html   = build_why_html(appliance, eff_season, eff_temp, eff_hour, eff_hs,
                                predicted, baseline, low_th, high_th, sev, diff_pct)
    bar_fig    = build_bar_chart(appliance, predicted, baseline, low_th, high_th)
    hourly_fig = build_hourly_chart(appliance, eff_season, eff_temp,
                                     month_label, eff_hs, day_of_week, eff_hour)

    return (predicted, baseline_str, status, why_html, recs_text, used_str,
            hour_avg, app_avg, sea_avg, bar_fig, hourly_fig)


# ─────────────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────────────
total    = f"{len(df):,}"
avg_kwh  = f"{df['Energy Consumption (kWh)'].mean():.3f} kWh"
peak_kwh = f"{df['Energy Consumption (kWh)'].max():.1f} kWh"
n_homes  = str(df['Home ID'].nunique())
n_apps   = str(df['Appliance Type'].nunique())


# ─────────────────────────────────────────────────────────────────
# THEME & CSS
# ─────────────────────────────────────────────────────────────────
theme = gr.themes.Default(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Plus Jakarta Sans"), "ui-sans-serif", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
).set(
    body_background_fill="#EEF2F7",
    background_fill_primary="#FFFFFF",
    background_fill_secondary="#F8FAFC",
    border_color_primary="#E2E8F0",
    block_border_width="1px",
    block_border_color="#E2E8F0",
    block_radius="14px",
    block_shadow="0 1px 4px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.04)",
    input_background_fill="#F8FAFC",
    input_border_color="#E2E8F0",
    input_border_width="1.5px",
    input_radius="10px",
    input_shadow="none",
    input_shadow_focus="0 0 0 3px rgba(29,78,216,0.1)",
    input_border_color_focus="#1D4ED8",
    body_text_color="#1E293B",
    body_text_size="14px",
    block_label_text_color="#64748B",
    block_label_text_size="11px",
    block_label_text_weight="600",
    button_primary_background_fill="linear-gradient(135deg,#1D4ED8,#4F46E5)",
    button_primary_background_fill_hover="linear-gradient(135deg,#1E40AF,#4338CA)",
    button_primary_text_color="#FFFFFF",
    button_primary_border_color="transparent",
    button_primary_shadow="0 4px 14px rgba(29,78,216,0.3)",
    button_large_radius="12px",
    button_large_text_size="15px",
    button_large_text_weight="700",
    button_large_padding="14px 28px",
    slider_color="#1D4ED8",
)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');
footer { display: none !important; }
body, .gradio-container { background: #EEF2F7 !important; }
.dash-header {
    background:#fff; border:1px solid #E2E8F0; border-radius:18px;
    padding:26px 30px 22px; margin-bottom:18px;
    box-shadow:0 1px 4px rgba(0,0,0,0.04),0 8px 24px rgba(0,0,0,0.05);
    position:relative; overflow:hidden;
}
.dash-header::before {
    content:''; position:absolute; top:0; left:0; right:0; height:4px;
    background:linear-gradient(90deg,#1D4ED8 0%,#4F46E5 50%,#7C3AED 100%);
}
.stat-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; }
.stat-card {
    background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px;
    padding:14px 16px; transition:border-color .2s,box-shadow .2s,transform .15s;
}
.stat-card:hover { border-color:#BFDBFE; box-shadow:0 4px 14px rgba(29,78,216,0.08); transform:translateY(-1px); }
.stat-label { font-size:9.5px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:.12em; margin-bottom:6px; }
.stat-value { font-size:21px; font-weight:800; color:#1D4ED8; line-height:1; font-family:'Plus Jakarta Sans',sans-serif; }
.stat-sub   { font-size:10px; color:#94A3B8; margin-top:4px; }
.sec-div { display:flex; align-items:center; gap:10px; margin:20px 0 14px; }
.sec-dot  { width:7px; height:7px; border-radius:50%; background:#1D4ED8; flex-shrink:0; }
.sec-text { font-size:10px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:.12em; white-space:nowrap; }
.sec-line { flex:1; height:1px; background:#E2E8F0; }
#predict-btn > div > button {
    background:linear-gradient(135deg,#1D4ED8,#4F46E5) !important;
    color:#fff !important; font-weight:700 !important; font-size:15px !important;
    letter-spacing:.025em !important; border-radius:12px !important; border:none !important;
    padding:15px !important; width:100% !important;
    box-shadow:0 4px 16px rgba(29,78,216,0.32) !important;
    transition:transform .15s,box-shadow .15s !important; cursor:pointer !important;
}
#predict-btn > div > button:hover { transform:translateY(-2px) !important; box-shadow:0 8px 24px rgba(29,78,216,0.42) !important; }
.panel-title {
    font-size:10.5px; font-weight:700; color:#94A3B8;
    text-transform:uppercase; letter-spacing:.1em;
    padding-bottom:12px; border-bottom:1px solid #F1F5F9; margin-bottom:6px;
}
.result-num input {
    font-family:'JetBrains Mono',monospace !important;
    font-size:20px !important; font-weight:700 !important;
    color:#1D4ED8 !important; text-align:center !important;
    background:#EFF6FF !important; border-color:#BFDBFE !important;
}
.tabs > div > button {
    font-size:11px !important; font-weight:700 !important;
    text-transform:uppercase !important; letter-spacing:.08em !important;
}
"""

def sc(label, value, sub):
    return (f'<div class="stat-card"><div class="stat-label">{label}</div>'
            f'<div class="stat-value">{value}</div><div class="stat-sub">{sub}</div></div>')

def sec(icon, text):
    return (f'<div class="sec-div"><div class="sec-dot"></div>'
            f'<span class="sec-text">{icon}&nbsp; {text}</span>'
            f'<div class="sec-line"></div></div>')

HEADER = f"""
<div class="dash-header">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:22px">
    <div style="width:50px;height:50px;flex-shrink:0;background:linear-gradient(135deg,#1D4ED8,#4F46E5);
                border-radius:14px;display:grid;place-items:center;font-size:22px;
                box-shadow:0 6px 18px rgba(29,78,216,0.28)">⚡</div>
    <div style="flex:1">
      <div style="font-size:22px;font-weight:800;color:#0F172A;letter-spacing:-.025em;line-height:1.2;
                  font-family:'Plus Jakarta Sans',sans-serif">
        SmartHome <span style="color:#1D4ED8">Energy</span> Dashboard
        <span style="font-size:13px;color:#059669;font-weight:600;margin-left:8px">🇮🇳 India Edition</span>
      </div>
      <div style="font-size:12px;color:#94A3B8;margin-top:4px">
        AI-Powered Prediction &nbsp;·&nbsp; LightGBM Model &nbsp;·&nbsp;
        <span style="color:#059669;font-weight:600">Indian Household Conditions</span>
        &nbsp;·&nbsp; Appliance-Aware Intelligence
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:7px;background:#F0FDF4;border:1.5px solid #BBF7D0;
                border-radius:999px;padding:6px 14px;font-size:11px;font-weight:700;color:#059669;
                letter-spacing:.05em;white-space:nowrap">
      <span style="width:7px;height:7px;border-radius:50%;background:#10B981;display:inline-block;
                   box-shadow:0 0 6px rgba(16,185,129,.5)"></span>
      MODEL ONLINE
    </div>
  </div>
  <div class="stat-grid">
    {sc("Total Records",   total,    "data points")}
    {sc("Avg Consumption", avg_kwh,  "per reading")}
    {sc("Peak Recorded",   peak_kwh, "max value")}
    {sc("Homes Tracked",   n_homes,  "unique homes")}
    {sc("Appliance Types", n_apps,   "categories")}
  </div>
</div>
"""

WHY_PLACEHOLDER = """
<div style="background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:14px;
            padding:28px 20px;text-align:center;color:#94A3B8;">
  <div style="font-size:28px;margin-bottom:8px">🔍</div>
  <div style="font-size:13px;font-weight:600">Run a prediction to see the explanation</div>
  <div style="font-size:11px;margin-top:4px">Factor-by-factor analysis will appear here</div>
</div>
"""


# ─────────────────────────────────────────────────────────────────
# BUILD GRADIO UI
# ─────────────────────────────────────────────────────────────────
_init_season = 'Summer'
_it          = SEASON_TEMP[_init_season]   # (min, max, default, step, label)

with gr.Blocks(theme=theme, css=CSS, title="SmartHome Energy Dashboard — India v4") as demo:

    gr.HTML(HEADER)
    gr.HTML(sec("⚡", "Prediction Engine"))

    with gr.Row(equal_height=False):

        # ── LEFT: Inputs ──────────────────────────────────────────
        with gr.Column(scale=1, min_width=340):
            with gr.Group():
                gr.HTML('<div class="panel-title">🎛️&nbsp; Configure Parameters</div>')

                appliance = gr.Dropdown(APPLIANCES, value='Air Conditioning', label="Appliance Type")

                season = gr.Dropdown(
                    SEASONS, value=_init_season,
                    label="Season (India)",
                    visible=True, interactive=True
                )
                month_dd = gr.Dropdown(
                    choices=SEASON_MONTH_CHOICES[_init_season],
                    value=SEASON_MONTH_DEFAULT[_init_season],
                    label="Month  (auto-filtered by Season)",
                    visible=True, interactive=True
                )

                temp = gr.Slider(
                    minimum=_it[0], maximum=_it[1],
                    value=_it[2], step=_it[3],
                    label=f"Outdoor Temperature (°C)  [{_it[0]}–{_it[1]}°C]",
                    visible=True, interactive=True
                )
                temp_info = gr.HTML(
                    value=_temp_badge_html(_init_season),
                    visible=True
                )

                hour = gr.Slider(
                    0, 23, value=14, step=1,
                    label="Time of Day  (0 = midnight · 12 = noon)",
                    visible=True, interactive=True
                )
                hs = gr.Slider(
                    1, 5, value=3, step=1,
                    label="Household Size  (number of people)",
                    visible=True, interactive=True
                )
                day = gr.Dropdown(
                    DAYS, value='Wed',
                    label="Day of Week",
                    visible=False, interactive=True
                )

            with gr.Row(elem_id="predict-btn"):
                btn = gr.Button("⚡  Predict Energy Consumption", variant="primary", size="lg")

        # ── RIGHT: Results ────────────────────────────────────────
        with gr.Column(scale=1, min_width=340):
            with gr.Group():
                gr.HTML('<div class="panel-title">📊&nbsp; Prediction Results</div>')
                with gr.Row():
                    out_pred = gr.Number(label="🔮  Predicted (kWh)", precision=3,
                                         elem_classes=["result-num"])
                    out_base = gr.Textbox(label="📐  Baseline & Normal Range", interactive=False)
                out_status = gr.Textbox(label="📌  Efficiency Status", interactive=False)

                gr.HTML(sec("🔍", "Why This Prediction?"))
                out_why = gr.HTML(value=WHY_PLACEHOLDER)

                out_recs = gr.Textbox(label="💡  Personalised Recommendations",
                                       lines=6, interactive=False)
                out_used = gr.Textbox(label="🔧  Active Parameters", interactive=False)

    # ── Static Analytics ──────────────────────────────────────────
    gr.HTML(sec("📊", "Energy Analytics"))
    with gr.Tabs():
        with gr.Tab("⏰  Hourly Pattern"):
            out_hourly = gr.DataFrame(label="", wrap=True, headers=["Hour","Avg kWh"])
        with gr.Tab("🔌  By Appliance"):
            out_app    = gr.DataFrame(label="", wrap=True, headers=["Appliance","Avg kWh"])
        with gr.Tab("🌤  By Season"):
            out_season = gr.DataFrame(label="", wrap=True, headers=["Season","Avg kWh"])

    # ── Dynamic Charts ────────────────────────────────────────────
    gr.HTML(sec("📈", "Dynamic Charts  —  refresh on every prediction"))
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML('<div style="font-size:10.5px;font-weight:700;color:#94A3B8;'
                    'text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;">'
                    '📊&nbsp; Predicted vs Average Consumption</div>')
            out_bar_chart = gr.Plot(label="", show_label=False)
        with gr.Column(scale=1):
            gr.HTML('<div style="font-size:10.5px;font-weight:700;color:#94A3B8;'
                    'text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;">'
                    '⏰&nbsp; Hourly Prediction Trend</div>')
            out_hourly_chart = gr.Plot(label="", show_label=False)

    # ── Wire events ───────────────────────────────────────────────
    appliance.change(
        fn=update_controls,
        inputs=appliance,
        outputs=[season, temp, temp_info, hour, month_dd, hs, day]
    )

    season.change(
        fn=update_season_controls,
        inputs=season,
        outputs=[month_dd, temp, temp_info]
    )

    btn.click(
        fn=predict_and_recommend,
        inputs=[appliance, season, temp, hour, month_dd, hs, day],
        outputs=[
            out_pred, out_base, out_status,
            out_why,
            out_recs, out_used,
            out_hourly, out_app, out_season,
            out_bar_chart, out_hourly_chart,
        ]
    )

demo.launch(share=True)
