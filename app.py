import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import uuid

DATA_FILE = Path("scores.json")

if DATA_FILE.exists():
    scores = json.loads(DATA_FILE.read_text())
else:
    scores = {"matches": []}

# Add this 👇
for match in scores["matches"]:
    if "id" not in match:
        match["id"] = str(uuid.uuid4())
DATA_FILE.write_text(json.dumps(scores, indent=2))

players = ["Gregi", "Tomi", "Brina", "Nejc"]

st.title("🏓 Ping Pong Score Tracker")

# Password input
password = st.text_input("Enter password to add match", type="password")

if password == "olly":
    with st.form("match_form"):
        p1 = st.selectbox("Player 1", players)
        p2 = st.selectbox("Player 2", [p for p in players if p != p1])
        s1 = st.number_input("Player 1 Score", min_value=0, step=1)
        s2 = st.number_input("Player 2 Score", min_value=0, step=1)
        submitted = st.form_submit_button("Submit")

        if submitted:
            diff = abs(s1 - s2)
            if (s1 < 11 and s2 < 11) or diff < 2:
                st.error("One player must have at least 11 points and win by 2.")
            else:
                scores["matches"].append({
                    "id": str(uuid.uuid4()),
                    "p1": p1, "p2": p2,
                    "score1": int(s1), "score2": int(s2),
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                DATA_FILE.write_text(json.dumps(scores, indent=2))
                st.success("Match saved!")
else:
    st.info("Enter password to add matches")

# Stats calculation
wins = {p: 0 for p in players}
losses = {p: 0 for p in players}
points_won = {p: 0 for p in players}
points_lost = {p: 0 for p in players}
overtime_wins = {p: 0 for p in players}
overtime_losses = {p: 0 for p in players}
biggest_wins = {p: {"diff": 0, "vs": None} for p in players}

for m in scores["matches"]:
    s1, s2 = m["score1"], m["score2"]
    p1, p2 = m["p1"], m["p2"]
    ot = s1 > 11 or s2 > 11
    if s1 > s2:
        wins[p1] += 1
        losses[p2] += 1
        if ot:
            overtime_wins[p1] += 1
            overtime_losses[p2] += 1
        diff = s1 - s2
        if diff > biggest_wins[p1]["diff"]:
            biggest_wins[p1] = {"diff": diff, "vs": p2}
    else:
        wins[p2] += 1
        losses[p1] += 1
        if ot:
            overtime_wins[p2] += 1
            overtime_losses[p1] += 1
        diff = s2 - s1
        if diff > biggest_wins[p2]["diff"]:
            biggest_wins[p2] = {"diff": diff, "vs": p1}

    points_won[p1] += s1
    points_lost[p1] += s2
    points_won[p2] += s2
    points_lost[p2] += s1

# Longest Winning Streak Calculation
streaks = {p: 0 for p in players}
longest_streaks = {p: 0 for p in players}
current_streaks = {p: 0 for p in players}

matches_sorted = sorted(scores["matches"], key=lambda m: m["date"])

for m in matches_sorted:
    winner = m["p1"] if m["score1"] > m["score2"] else m["p2"]
    for p in players:
        if p == winner:
            current_streaks[p] += 1
            if current_streaks[p] > longest_streaks[p]:
                longest_streaks[p] = current_streaks[p]
        else:
            current_streaks[p] = 0

# Build DataFrame
df = pd.DataFrame(scores["matches"])

if not df.empty:
    df["point_diff"] = df["score1"] - df["score2"]
    df = df[["p1", "score1", "p2", "score2", "date"]]
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Leaderboard data
    data = []
    for p in players:
        total = wins[p] + losses[p]
        win_pct = (wins[p] / total * 100) if total > 0 else 0
        ot_total = overtime_wins[p] + overtime_losses[p]
        ot_win_pct = (overtime_wins[p] / ot_total * 100) if ot_total > 0 else 0

        biggest_score = "-"
        max_diff = 0
        for m in scores["matches"]:
            if m["p1"] == p or m["p2"] == p:
                diff = abs(m["score1"] - m["score2"])
                winner = m["p1"] if m["score1"] > m["score2"] else m["p2"]
                if winner == p and diff > max_diff:
                    max_diff = diff
                    loser = m["p2"] if winner == m["p1"] else m["p1"]
                    score_str = f"{m['score1']}-{m['score2']}"
                    biggest_score = f"{score_str} vs {loser}"

        data.append({
            "Player": p,
            "Wins": wins[p],
            "Losses": losses[p],
            "Win %": f"{win_pct:.1f}%",
            "Points Won": points_won[p],
            "Points Lost": points_lost[p],
            "OT Ws": overtime_wins[p],
            "OT Ls": overtime_losses[p],
            "OT W %": f"{ot_win_pct:.1f}%",
            "Biggest Win": biggest_score,
        })

    leaderboard_df = pd.DataFrame(data).sort_values(by="Wins", ascending=False)

    st.subheader("🏅 Player Leaderboard")
    st.dataframe(leaderboard_df, hide_index=True)

    # Head-to-Head (H2H) matrix
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

    # Last 5 matches
    st.subheader("⏳ Last 5 Matches")
    st.dataframe(df.sort_values(by="date", ascending=False).head(5), hide_index=True)

    # Monthly leaderboard
    df_dates = pd.to_datetime([m["date"] for m in scores["matches"]])
    months = df_dates.to_period("M").unique()

    st.subheader("📅 Monthly Leaderboard (Wins / Losses)")
    for month in months:
        month_str = month.strftime("%B %Y")
        st.markdown(f"**{month_str}**")
        wins_month = {p: 0 for p in players}
        losses_month = {p: 0 for p in players}
        for m in scores["matches"]:
            m_date = pd.to_datetime(m["date"], format="%Y-%m-%d").to_period("M")
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

    # Match Table (all matches)
    st.subheader("📊 Match Table")
    st.dataframe(df.sort_values(by="date", ascending=False), height=300, hide_index=True)

    # Longest match
    if scores["matches"]:
        longest_match = max(scores["matches"], key=lambda m: m["score1"] + m["score2"])
        longest_points = longest_match["score1"] + longest_match["score2"]
        p1 = longest_match["p1"]
        p2 = longest_match["p2"]
        score_str = f"{longest_match['score1']}-{longest_match['score2']}"
        date_str = pd.to_datetime(longest_match["date"], format="%Y-%m-%d").strftime("%d-%m-%Y")

        st.subheader("⏱️ Longest Match (Most Points Played)")
        st.write(f"{p1} vs {p2} — {score_str} ({longest_points} points) on {date_str}")

    # Longest Winning Streak (Whole Section)
    st.subheader("🔥 Longest Winning Streaks")
    st.write(
        "Longest winning streak per player based on consecutive match wins:"
    )
    st.dataframe(pd.DataFrame({
        "Player": players,
        "Longest Win Streak": [longest_streaks[p] for p in players]
    }), hide_index=True)

# 💀 Loser of the Month (most losses in current month)
current_month = pd.Timestamp.now().to_period("M")
losses_this_month = {p: 0 for p in players}

for m in scores["matches"]:
    match_month = pd.to_datetime(m["date"]).to_period("M")
    if match_month == current_month:
        if m["score1"] > m["score2"]:
            losses_this_month[m["p2"]] += 1
        else:
            losses_this_month[m["p1"]] += 1

loser_of_month = max(losses_this_month, key=losses_this_month.get)
st.markdown(f"💀 **Loser of the Month:** {loser_of_month}")

st.markdown(f"💀 **Actual Loser:** nibber")

total_matches = len(scores["matches"])
st.write(f"**Total matches played:** {total_matches}")

# 🔒 Delete Match Section (Admin Only)
st.subheader("🗑️ Delete a Match")

delete_password = st.text_input("Enter admin password to delete", type="password")
if delete_password == "johnny":
    match_options = [
        f"{m['p1']} {m['score1']}-{m['score2']} {m['p2']} on {pd.to_datetime(m['date'], format='%Y-%m-%d').strftime('%d-%m-%Y')
} (ID: {m['id']})"
        for m in scores["matches"]
    ]
    selected = st.selectbox("Select a match to delete", match_options)
    if st.button("Delete Selected Match"):
        match_id = selected.split("ID: ")[-1].replace(")", "")
        scores["matches"] = [m for m in scores["matches"] if m["id"] != match_id]
        DATA_FILE.write_text(json.dumps(scores, indent=2))
        st.success("Match deleted!")
        st.rerun()
else:
    st.info("Enter password to unlock delete feature")