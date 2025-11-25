import streamlit as st
import pandas as pd
from espn_api.football import League

st.set_page_config(page_title="Fantasy Football Standings", layout="wide")

st.title('🏈 Fantasy Football Dashboard')

year = st.number_input('Select Year:', min_value=2015, max_value=2025, value=2025, step=1)
# Create tabs
tab1, tab2, tab3 = st.tabs(["Power Rankings", "Team Stats", "Matchups"])
league = League(league_id=753911, year=year, espn_s2='AECSbKZxmko3IVdPdkTGtFd9GbPnjt8tsnNWCdt1F4%2FcDNjVw%2FBUlq25YTgworHWi2fdQvfN2VjYhHd%2FuUxab2%2BUwHM0FUh2mxUm74VT3FEJgDWGpQb8hnL4FA8AXuaTKCs%2B3RheFyHPHB8rq0%2B%2FTQzTQ7856nW3zesI%2BVrjVCY3m%2B6BaOafaytHn8eCv0FVNsOkuqvtnRyuxkWHMKDON53MvvDWpsHu3BNNTNFSwuVDq7YhogahNeHlP%2F5QOi7mRv%2BX4fnvlgigZHzvW%2BS1hsRyAjYYbiu07tk37%2BF3rjPgZw%3D%3D', swid='{D29A0BC7-76B3-4AF2-A91D-7F2ADC252CE4}')

with tab1:
    st.header('Power Rankings')

    # Week selector
    week = st.number_input('Select Week:', min_value=1, max_value=18, value=13, step=1)

    # Button to fetch rankings
    if st.button('Get Rankings') or 'rankings_data' not in st.session_state:
        with st.spinner('Fetching rankings...'):
            # Your function call here
            result = league.power_rankings(week)
            st.session_state.rankings_data = result

    # Display rankings if available
    if 'rankings_data' in st.session_state:
        data = st.session_state.rankings_data

        # Extract data properly - it's tuples of (score, Team object)
        df = pd.DataFrame([
            {
                'Points': float(score),
                'Team Name': str(team)  # Convert Team object to string
            }
            for score, team in data
        ])

        df['Rank'] = range(1, len(df) + 1)

        # Clean up the team name if it has "Team(" prefix
        df['Team Name'] = df['Team Name'].str.replace('Team(', '', regex=False).str.replace(')', '', regex=False)

        st.subheader(f'Week {week} Rankings')

        # Display as a nice table
        st.dataframe(
            df[['Rank', 'Team Name', 'Points']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn(
                    "Rank",
                    help="Team ranking",
                    format="%d 🏆"
                ),
                "Points": st.column_config.NumberColumn(
                    "Points",
                    help="Power ranking score",
                    format="%.2f"
                )
            }
        )

        # Add a bar chart
        st.bar_chart(df.set_index('Team Name')['Points'])

        # Show stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Top Team", df.iloc[0]['Team Name'])
        col2.metric("High Score", f"{df.iloc[0]['Points']:.2f}")
        col3.metric("Total Teams", len(df))

with tab2:
    st.header('Player Performance')

    # Week range selector
    col1, col2 = st.columns(2)
    with col1:
        start_week = st.number_input('Start Week:', min_value=1, max_value=18, value=1, step=1)
    with col2:
        end_week = st.number_input('End Week:', min_value=1, max_value=18, value=18, step=1)

    # Team selector (optional - to filter by team)
    teams = [str(team) for team in league.teams]
    selected_team = st.selectbox('Filter by Team (optional):', ['All Teams'] + teams)

    if st.button('Load Player Data'):
        with st.spinner('Loading player data...'):
            player_data = []

            # Loop through weeks
            for week in range(start_week, end_week + 1):
                box_scores = league.box_scores(week)

                for box in box_scores:
                    # Process home team
                    for player in box.home_lineup:
                        if selected_team == 'All Teams' or str(box.home_team) == selected_team:
                            player_data.append({
                                'Week': week,
                                'Team': str(box.home_team).replace('Team(', '').replace(')', ''),
                                'Player': player.name,
                                'Position': player.position,
                                'Slot': player.slot_position,
                                'Points': player.points,
                                'Projected': player.projected_points,
                                'Diff': player.points - player.projected_points,
                                'Opponent': player.pro_opponent,
                                'Pos Rank': player.pro_pos_rank
                            })

                    # Process away team
                    for player in box.away_lineup:
                        if selected_team == 'All Teams' or str(box.away_team) == selected_team:
                            player_data.append({
                                'Week': week,
                                'Team': str(box.away_team).replace('Team(', '').replace(')', ''),
                                'Player': player.name,
                                'Position': player.position,
                                'Slot': player.slot_position,
                                'Points': player.points,
                                'Projected': player.projected_points,
                                'Diff': player.points - player.projected_points,
                                'Opponent': player.pro_opponent,
                                'Pos Rank': player.pro_pos_rank
                            })

            df_players = pd.DataFrame(player_data)
            st.session_state.player_df = df_players

    # Display the data if available
    if 'player_df' in st.session_state:
        df = st.session_state.player_df

        st.subheader(f'Player Stats (Weeks {start_week}-{end_week})')

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Players", len(df['Player'].unique()))
        col2.metric("Avg Points/Week", f"{df['Points'].mean():.2f}")
        col3.metric("Top Scorer", df.loc[df['Points'].idxmax(), 'Player'])
        col4.metric("Top Score", f"{df['Points'].max():.2f}")

        # Filter options
        st.subheader('Filters')
        col1, col2 = st.columns(2)
        with col1:
            position_filter = st.multiselect('Filter by Position:',
                                             options=sorted(df['Position'].unique()),
                                             default=None)
        with col2:
            min_points = st.slider('Minimum Points:',
                                   min_value=0.0,
                                   max_value=float(df['Points'].max()),
                                   value=0.0)

        # Apply filters
        filtered_df = df.copy()
        if position_filter:
            filtered_df = filtered_df[filtered_df['Position'].isin(position_filter)]
        filtered_df = filtered_df[filtered_df['Points'] >= min_points]

        # Display table
        st.dataframe(
            filtered_df.sort_values('Points', ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Points": st.column_config.NumberColumn(format="%.2f"),
                "Projected": st.column_config.NumberColumn(format="%.2f"),
                "Diff": st.column_config.NumberColumn(
                    format="%.2f",
                    help="Points - Projected"
                )
            }
        )

        # Aggregate by player across all weeks
        st.subheader('Season Totals by Player')
        player_totals = df.groupby('Player').agg({
            'Points': 'sum',
            'Projected': 'sum',
            'Week': 'count'
        }).reset_index()
        player_totals.columns = ['Player', 'Total Points', 'Total Projected', 'Weeks Played']
        player_totals = player_totals.sort_values('Total Points', ascending=False)

        st.dataframe(
            player_totals,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total Points": st.column_config.NumberColumn(format="%.2f"),
                "Total Projected": st.column_config.NumberColumn(format="%.2f")
            }
        )

        # Top performers chart
        st.subheader('Top 20 Scorers')
        top_20 = player_totals.head(20)
        st.bar_chart(top_20.set_index('Player')['Total Points'])

with tab3:
    st.header('Head to Head')

    # Week selector for matchups
    matchup_week = st.number_input('Select Week for Matchups:', min_value=1, max_value=18, value=12, step=1,
                                   key='matchup_week')

    if st.button('Load Matchups', key='load_matchups'):
        with st.spinner('Loading matchups...'):
            box_scores = league.box_scores(matchup_week)
            st.session_state.box_scores = box_scores
            st.session_state.matchup_week_loaded = matchup_week

    # Display matchups if available
    if 'box_scores' in st.session_state:
        box_scores = st.session_state.box_scores
        week_loaded = st.session_state.get('matchup_week_loaded', matchup_week)

        st.subheader(f'Week {week_loaded} Matchups')

        # Calculate some stats
        total_points_home = sum(box.home_score for box in box_scores)
        total_points_away = sum(box.away_score for box in box_scores)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Matchups", len(box_scores))
        col2.metric("Avg Home Score", f"{total_points_home / len(box_scores):.2f}")
        col3.metric("Avg Away Score", f"{total_points_away / len(box_scores):.2f}")

        st.write("---")

        # Display each matchup
        for idx, box in enumerate(box_scores):
            home_team = str(box.home_team).replace('Team(', '').replace(')', '')
            away_team = str(box.away_team).replace('Team(', '').replace(')', '')
            home_score = box.home_score
            away_score = box.away_score

            # Determine winner
            if home_score > away_score:
                winner = "home"
                margin = home_score - away_score
            else:
                winner = "away"
                margin = away_score - home_score

            # Create a nice matchup card
            with st.container():
                st.markdown(f"### Matchup {idx + 1}")

                col1, col2, col3 = st.columns([2, 1, 2])

                with col1:
                    if winner == "home":
                        st.markdown(f"**🏆 {home_team}**")
                    else:
                        st.markdown(f"{home_team}")
                    st.markdown(f"<h2 style='color: {'green' if winner == 'home' else 'gray'};'>{home_score:.2f}</h2>",
                                unsafe_allow_html=True)

                with col2:
                    st.markdown("<div style='text-align: center; padding-top: 20px;'>", unsafe_allow_html=True)
                    st.markdown("**VS**")
                    st.markdown(f"*Margin: {margin:.2f}*")
                    st.markdown("</div>", unsafe_allow_html=True)

                with col3:
                    if winner == "away":
                        st.markdown(f"**🏆 {away_team}**")
                    else:
                        st.markdown(f"{away_team}")
                    st.markdown(f"<h2 style='color: {'green' if winner == 'away' else 'gray'};'>{away_score:.2f}</h2>",
                                unsafe_allow_html=True)

                # Expandable section for lineup details
                with st.expander(f"View Lineups for {home_team} vs {away_team}"):
                    col_home, col_away = st.columns(2)

                    with col_home:
                        st.markdown(f"**{home_team} Lineup**")
                        home_players = []
                        for player in box.home_lineup:
                            home_players.append({
                                'Player': player.name,
                                'Pos': player.slot_position,
                                'Points': player.points,
                                'Proj': player.projected_points
                            })
                        df_home = pd.DataFrame(home_players)
                        st.dataframe(df_home, use_container_width=True, hide_index=True)

                    with col_away:
                        st.markdown(f"**{away_team} Lineup**")
                        away_players = []
                        for player in box.away_lineup:
                            away_players.append({
                                'Player': player.name,
                                'Pos': player.slot_position,
                                'Points': player.points,
                                'Proj': player.projected_points
                            })
                        df_away = pd.DataFrame(away_players)
                        st.dataframe(df_away, use_container_width=True, hide_index=True)

                st.write("---")

        # Summary table of all matchups
        st.subheader('Matchup Summary')
        matchup_summary = []
        for box in box_scores:
            home_team = str(box.home_team).replace('Team(', '').replace(')', '')
            away_team = str(box.away_team).replace('Team(', '').replace(')', '')

            if box.home_score > box.away_score:
                winner = home_team
                loser = away_team
                win_score = box.home_score
                lose_score = box.away_score
            else:
                winner = away_team
                loser = home_team
                win_score = box.away_score
                lose_score = box.home_score

            matchup_summary.append({
                'Winner': winner,
                'Winner Score': win_score,
                'Loser': loser,
                'Loser Score': lose_score,
                'Margin': win_score - lose_score
            })

        df_summary = pd.DataFrame(matchup_summary)
        st.dataframe(
            df_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Winner Score": st.column_config.NumberColumn(format="%.2f"),
                "Loser Score": st.column_config.NumberColumn(format="%.2f"),
                "Margin": st.column_config.NumberColumn(format="%.2f")
            }
        )