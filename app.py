import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

DATA_FILE = Path("scores.json")

if DATA_FILE.exists():
    scores = json.loads(DATA_FILE.read_text())
else:
    scores = {"matches": []}

players = ["Gregi", "Tomi", "Brina"]

st.title("🏓 Ping Pong Score Tracker")

# --- Match input form ---
with st.form("match_form"):
    p1 = st.selectbox("Player 1", players)
    p2 = st.selectbox("Player 2", [p for p in players if p != p1])
    score_input = st.text_input("Enter score (format: 11-9)")
    submitted = st.form_submit_button("Submit")

    # Score validation inside form submit:
    if submitted:
        try:
            s1, s2 = map(int, score_input.split('-'))
            diff = abs(s1 - s2)
            if (s1 < 11 and s2 < 11) or diff < 2:
                st.error("One player must have at least 11 points and win by 2.")
            elif s1 < 0 or s2 < 0:
                st.error("Scores must be positive.")
            else:
                scores["matches"].append({
                    "p1": p1, "p2": p2,
                    "score1": s1, "score2": s2,
                    "date": str(datetime.now())
                })
                DATA_FILE.write_text(json.dumps(scores, indent=2))
                st.success("Match saved!")
        except Exception:
            st.error("Invalid score format. Use e.g. 15-13, 11-7")

    wins = {p: 0 for p in players}
    losses = {p: 0 for p in players}
    points_won = {p: 0 for p in players}
    points_lost = {p: 0 for p in players}

    for m in scores["matches"]:
        if m["score1"] > m["score2"]:
            wins[m["p1"]] += 1
            losses[m["p2"]] += 1
        else:
            wins[m["p2"]] += 1
            losses[m["p1"]] += 1
        points_won[m["p1"]] += m["score1"]
        points_lost[m["p1"]] += m["score2"]
        points_won[m["p2"]] += m["score2"]
        points_lost[m["p2"]] += m["score1"]

# --- Build DataFrame and stats ---
df = pd.DataFrame(scores["matches"])

if not df.empty:
    df["point_diff"] = df["score1"] - df["score2"]
    df["result"] = df["point_diff"].apply(lambda x: "W" if x > 0 else "L")
    df = df[["p1", "score1", "p2", "score2", "date"]]
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # 1. Leaderboard
    data = []
    for p in players:
        total = wins[p] + losses[p]
        win_pct = (wins[p] / total * 100) if total > 0 else 0
        data.append({
            "Player": p,
            "Wins": wins[p],
            "Losses": losses[p],
            "Win %": f"{win_pct:.1f}%",
            "Points Won": points_won[p],
            "Points Lost": points_lost[p],
        })

    leaderboard_df = pd.DataFrame(data)
    leaderboard_df = leaderboard_df.sort_values(by="Wins", ascending=False)

    st.subheader("🏅 Player Leaderboard")
    st.dataframe(leaderboard_df, hide_index=True)
    # 2. Head-to-Head (H2H) matrix
    st.subheader("🤼 Head-to-Head Comparison")

    h2h = {p: {o: {"W": 0, "L": 0} for o in players if o != p} for p in players}

    for m in scores["matches"]:
        if m["score1"] > m["score2"]:
            h2h[m["p1"]][m["p2"]]["W"] += 1
            h2h[m["p2"]][m["p1"]]["L"] += 1
        else:
            h2h[m["p2"]][m["p1"]]["W"] += 1
            h2h[m["p1"]][m["p2"]]["L"] += 1

    h2h_data = []
    for p1 in players:
        row = []
        for p2 in players:
            if p1 == p2:
                row.append("-")
            else:
                rec = h2h[p1][p2]
                row.append(f"{rec['W']}-{rec['L']}")
        h2h_data.append(row)

    h2h_df = pd.DataFrame(h2h_data, columns=players, index=players)
    st.dataframe(h2h_df)
    

    # 3. Last 5 matches
    st.subheader("⏳ Last 5 Matches")
    st.dataframe(df.sort_values(by="date", ascending=False).head(5), hide_index=True)

    # 4. Monthly leaderboard
    df_dates = pd.to_datetime([m["date"] for m in scores["matches"]])
    months = df_dates.to_period("M").unique()

    st.subheader("📅 Monthly Leaderboard (Wins / Losses)")
    for month in months:
        month_str = month.strftime("%B %Y")
        st.markdown(f"**{month_str}**")
        wins_month = {p:0 for p in players}
        losses_month = {p:0 for p in players}
        for m in scores["matches"]:
            m_date = pd.to_datetime(m["date"]).to_period("M")
            if m_date == month:
                if m["score1"] > m["score2"]:
                    wins_month[m["p1"]] += 1
                    losses_month[m["p2"]] += 1
                else:
                    wins_month[m["p2"]] += 1
                    losses_month[m["p1"]] += 1
        data = []
        for p in players:
            data.append({"Player": p, "Wins": wins_month[p], "Losses": losses_month[p]})
        month_df = pd.DataFrame(data).sort_values(by="Wins", ascending=False)
        st.dataframe(month_df, use_container_width=True, hide_index=True)

    # 5. Match Table (all matches)
    st.subheader("📊 Match Table")
    st.dataframe(df.sort_values(by="date", ascending=False), height=300, hide_index=True)

