import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import itertools

# Load data
@st.cache_data
def load_data():
    drivers_df = pd.read_csv('data/f1_fantasy_drivers.csv')
    teams_df = pd.read_csv('data/f1_fantasy_teams.csv')
    
    # Title case for driver names
    drivers_df['driver'] = drivers_df['driver'].str.replace('_', ' ').str.title()
    
    # Title case for team names
    teams_df['team'] = teams_df['team'].str.replace('_', ' ').str.title()
    
    return drivers_df, teams_df

def find_best_combinations(drivers_df, teams_df, selected_drivers=None, selected_teams=None, max_cost=100, top_n=5):
    # Create copies and rename columns
    drivers_df = drivers_df.copy()
    teams_df = teams_df.copy()
    drivers_df = drivers_df.rename(columns={'points_2024': 'points'})
    teams_df = teams_df.rename(columns={'points_2024': 'points'})
    
    # Calculate used budget from original dataframes
    used_budget = 0
    if selected_drivers:
        used_budget += drivers_df[drivers_df['driver'].isin(selected_drivers)]['cost'].sum()
    if selected_teams:
        used_budget += teams_df[teams_df['team'].isin(selected_teams)]['cost'].sum()
    remaining_budget = max_cost - used_budget
    
    # Calculate points from selected drivers and teams
    selected_points = 0
    if selected_drivers:
        selected_points += drivers_df[drivers_df['driver'].isin(selected_drivers)]['points'].sum()
    if selected_teams:
        selected_points += teams_df[teams_df['team'].isin(selected_teams)]['points'].sum()
    
    # Filter out already selected items
    if selected_drivers:
        drivers_df = drivers_df[~drivers_df['driver'].isin(selected_drivers)]
    if selected_teams:
        teams_df = teams_df[~teams_df['team'].isin(selected_teams)]
    
    # Calculate remaining slots
    remaining_drivers = 5 - (len(selected_drivers) if selected_drivers else 0)
    remaining_teams = 2 - (len(selected_teams) if selected_teams else 0)

    driver_combinations = list(itertools.combinations(drivers_df.itertuples(index=False), remaining_drivers))
    team_combinations = list(itertools.combinations(teams_df.itertuples(index=False), remaining_teams))

    all_combinations = []
    
    for driver_combo in driver_combinations:
        for team_combo in team_combinations:
            total_cost = sum(driver.cost for driver in driver_combo) + sum(team.cost for team in team_combo)
            if total_cost <= remaining_budget:
                # Calculate points including both selected and new items
                total_points = (
                    selected_points +  # Points from pre-selected items
                    sum(driver.points for driver in driver_combo) +  # Points from new drivers
                    sum(team.points for team in team_combo)  # Points from new teams
                )
                
                all_combinations.append((driver_combo, team_combo, total_points, total_cost))

    if not all_combinations:
        return []  # Return empty list if no valid combinations found

    all_combinations.sort(key=lambda x: x[2], reverse=True)
    return all_combinations[:top_n]

def count_valid_combinations(drivers_df, teams_df, selected_drivers=None, selected_teams=None, max_cost=100):
    # Create copies and rename columns
    drivers_df = drivers_df.copy()
    teams_df = teams_df.copy()
    
    # Calculate used budget from original dataframes
    used_budget = 0
    if selected_drivers:
        used_budget += drivers_df[drivers_df['driver'].isin(selected_drivers)]['cost'].sum()
    if selected_teams:
        used_budget += teams_df[teams_df['team'].isin(selected_teams)]['cost'].sum()
    remaining_budget = max_cost - used_budget
    
    # Filter out already selected items
    if selected_drivers:
        drivers_df = drivers_df[~drivers_df['driver'].isin(selected_drivers)]
    if selected_teams:
        teams_df = teams_df[~teams_df['team'].isin(selected_teams)]
    
    # Calculate remaining slots
    remaining_drivers = 5 - (len(selected_drivers) if selected_drivers else 0)
    remaining_teams = 2 - (len(selected_teams) if selected_teams else 0)
    
    valid_count = 0
    
    # Generate combinations
    driver_combinations = itertools.combinations(drivers_df.itertuples(index=False), remaining_drivers)
    team_combinations = list(itertools.combinations(teams_df.itertuples(index=False), remaining_teams))
    
    # Count valid combinations
    for driver_combo in driver_combinations:
        driver_cost = sum(driver.cost for driver in driver_combo)
        if driver_cost > remaining_budget:
            continue
            
        for team_combo in team_combinations:
            total_cost = driver_cost + sum(team.cost for team in team_combo)
            if total_cost <= remaining_budget:
                valid_count += 1
    
    return valid_count

def estimate_rank(points, min_points=25, max_points=1749, total_combinations=297307):
    """
    Estimate the rank of a combination based on its points.
    """
    # Linear mapping from points to rank (higher points = lower rank number)
    points_range = max_points - min_points
    rank = int((max_points - points) / points_range * total_combinations) + 1
    return rank

def main():
    st.title("Formulab")
    st.header("F1 Fantasy Team Builder")
    st.markdown("""
    There are 697,680 possible combinations of 5 drivers and 2 teams. Of those, 297,307 respect F1 Fantasy's 100M cost cap. With such a large solution space, finding a satisfactory combination can be a challenge. This tool is intended to provide some assistance with that.
    
    The following is entirely based on 2024 season points for drivers and teams. Past performance is of course not necessarily indicative of future results, so take everything with a grain of salt. For reference:
    - The \"most optimal\" combination, with 1749 points, is Sainz, Alonso, Ocon, Bearman, and Hulkenberg + Mclaren and Ferrari.
    - The \"least optimal\" combination, with 25 points, is Antonelli, Lawson, Doohan, Hadjar, and Bortoleto + Williams and Kick Sauber.
    """)
    
    drivers_df, teams_df = load_data()
    
    # Initialize session state for selections
    if 'selected_drivers' not in st.session_state:
        st.session_state.selected_drivers = []
    if 'selected_teams' not in st.session_state:
        st.session_state.selected_teams = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Select Drivers (5)")
        available_drivers = [d for d in drivers_df['driver'].tolist() 
                           if d not in st.session_state.selected_drivers]
        
        if len(st.session_state.selected_drivers) < 5:
            new_driver = st.selectbox("Add a driver", 
                                    options=[''] + available_drivers,
                                    key='driver_select')
            if new_driver:
                st.session_state.selected_drivers.append(new_driver)
                st.rerun()
    
    with col2:
        st.subheader("Select Teams (2)")
        available_teams = [t for t in teams_df['team'].tolist() 
                         if t not in st.session_state.selected_teams]
        
        if len(st.session_state.selected_teams) < 2:
            new_team = st.selectbox("Add a team", 
                                  options=[''] + available_teams,
                                  key='team_select')
            if new_team:
                st.session_state.selected_teams.append(new_team)
                st.rerun()
    
    # Display current selections and allow removal
    st.subheader("Current Selections")
    col3, spacer, col4 = st.columns([1, 0.1, 1])
    
    # Calculate total points and cost for contribution percentages
    total_points = (
        drivers_df[drivers_df['driver'].isin(st.session_state.selected_drivers)]['points_2024'].sum() +
        teams_df[teams_df['team'].isin(st.session_state.selected_teams)]['points_2024'].sum()
    )
    
    total_cost = (
        drivers_df[drivers_df['driver'].isin(st.session_state.selected_drivers)]['cost'].sum() +
        teams_df[teams_df['team'].isin(st.session_state.selected_teams)]['cost'].sum()
    )
    
    # Calculate total value ratio
    value_ratio = total_points / total_cost if total_cost > 0 else 0
    
    # Display total stats before individual selections
    st.markdown(f"""
    **Total Stats:**
    Points: {int(total_points)}
    Cost: {total_cost:.1f}M/100M
    Value: {value_ratio:.2f}
    """)
    
    with col3:
        st.write("Selected Drivers:")
        for driver in st.session_state.selected_drivers:
            driver_info = drivers_df[drivers_df['driver'] == driver].iloc[0]
            points = driver_info['points_2024']
            cost = driver_info['cost']
            value_ratio = points / cost
            contribution = (points / total_points * 100) if total_points > 0 else 0
            
            # Create a container for the entire card
            container = st.container()
            col1, col2 = container.columns([0.9, 0.1])
            
            with col1:
                st.markdown(
                    f"**{driver}**  \n"
                    f"Points: {int(points)}  \n"
                    f"Cost: {cost:.1f}M  \n"
                    f"Value: {value_ratio:.2f}  \n"
                    f"Contribution: {contribution:.1f}%"
                )
            with col2:
                if st.button("❌", key=f"remove_driver_{driver}"):
                    st.session_state.selected_drivers.remove(driver)
                    st.rerun()
    
    with col4:
        st.write("Selected Teams:")
        for team in st.session_state.selected_teams:
            team_info = teams_df[teams_df['team'] == team].iloc[0]
            points = team_info['points_2024']
            cost = team_info['cost']
            value_ratio = points / cost
            contribution = (points / total_points * 100) if total_points > 0 else 0
            
            # Create a container for the entire card
            container = st.container()
            col1, col2 = container.columns([0.9, 0.1])
            
            with col1:
                st.markdown(
                    f"**{team}**  \n"
                    f"Points: {int(points)}  \n"
                    f"Cost: {cost:.1f}M  \n"
                    f"Value: {value_ratio:.2f}  \n"
                    f"Contribution: {contribution:.1f}%"
                )
            with col2:
                if st.button("❌", key=f"remove_team_{team}"):
                    st.session_state.selected_teams.remove(team)
                    st.rerun()
    
    # Display total valid combinations with current selections
    if st.session_state.selected_drivers or st.session_state.selected_teams:
        with st.spinner('Calculating valid combinations...'):
            valid_combos = count_valid_combinations(
                drivers_df,
                teams_df,
                st.session_state.selected_drivers,
                st.session_state.selected_teams
            )
            st.info(f"There are {valid_combos:,} valid combinations possible with your current selections.")

    # Find and display optimal combinations
    if st.session_state.selected_drivers or st.session_state.selected_teams:
        st.subheader("Optimal Combinations with Current Selections")
        
        with st.spinner('Calculating optimal combinations...'):
            best_combos = find_best_combinations(
                drivers_df, 
                teams_df,
                st.session_state.selected_drivers,
                st.session_state.selected_teams,
                top_n=5
            )
        
        if not best_combos:
            st.warning("No valid combinations found with the current selections and budget constraints.")
        else:
            for i, (drivers, teams, points, cost) in enumerate(best_combos, 1):
                # Create lists of all drivers and teams (current + recommended)
                all_drivers = st.session_state.selected_drivers + [d.driver for d in drivers]
                all_teams = st.session_state.selected_teams + [t.team for t in teams]
                
                # Format driver and team strings with bold for selected ones
                driver_labels = [f"**{d}**" if d in st.session_state.selected_drivers else d for d in all_drivers]
                team_labels = [f"**{t}**" if t in st.session_state.selected_teams else t for t in all_teams]
                
                # Calculate value ratio for the combination
                total_combo_cost = total_cost + cost
                value_ratio = points / total_combo_cost if total_combo_cost > 0 else 0
                
                expander_label = (
                    f"Combination {i} (~{estimate_rank(points):,}/297,307) | Points: {int(points)} | "
                    f"Cost: {total_combo_cost:.1f}M | Value: {value_ratio:.2f}\n\n"
                    f"Drivers: {', '.join(driver_labels)}\n\n"
                    f"Teams: {', '.join(team_labels)}"
                )
                
                with st.expander(expander_label):
                    # Calculate total points for this combination (including current selections)
                    combo_total_points = 0
                    # Add points from current selections
                    for driver in st.session_state.selected_drivers:
                        driver_info = drivers_df[drivers_df['driver'] == driver].iloc[0]
                        combo_total_points += driver_info['points_2024']
                    for team in st.session_state.selected_teams:
                        team_info = teams_df[teams_df['team'] == team].iloc[0]
                        combo_total_points += team_info['points_2024']
                    # Add points from recommended additions
                    combo_total_points += sum(driver.points for driver in drivers)
                    combo_total_points += sum(team.points for team in teams)
                    
                    st.write("Current Selections:")
                    if st.session_state.selected_drivers:
                        st.write("&nbsp;&nbsp;&nbsp;&nbsp;Drivers:")
                        for driver in st.session_state.selected_drivers:
                            driver_info = drivers_df[drivers_df['driver'] == driver].iloc[0]
                            d_points = driver_info['points_2024']
                            d_cost = driver_info['cost']
                            value_ratio = d_points / d_cost
                            contribution = (d_points / combo_total_points * 100) if combo_total_points > 0 else 0
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;&nbsp;{driver} (Points: {int(d_points)}, Cost: {d_cost:.1f}M, Value: {value_ratio:.2f}, Contribution: {contribution:.1f}%)")
                    if st.session_state.selected_teams:
                        st.write("&nbsp;&nbsp;&nbsp;&nbsp;Teams:")
                        for team in st.session_state.selected_teams:
                            team_info = teams_df[teams_df['team'] == team].iloc[0]
                            t_points = team_info['points_2024']
                            t_cost = team_info['cost']
                            value_ratio = t_points / t_cost
                            contribution = (t_points / combo_total_points * 100) if combo_total_points > 0 else 0
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;&nbsp;{team} (Points: {int(t_points)}, Cost: {t_cost:.1f}M, Value: {value_ratio:.2f}, Contribution: {contribution:.1f}%)")
                    
                    st.write("\nRecommended Additions:")
                    if drivers:
                        st.write("&nbsp;&nbsp;&nbsp;&nbsp;Drivers:")
                        for driver in drivers:
                            value_ratio = driver.points / driver.cost
                            contribution = (driver.points / combo_total_points * 100) if combo_total_points > 0 else 0
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;&nbsp;{driver.driver} (Points: {int(driver.points)}, Cost: {driver.cost:.1f}M, Value: {value_ratio:.2f}, Contribution: {contribution:.1f}%)")
                    if teams:
                        st.write("&nbsp;&nbsp;&nbsp;&nbsp;Teams:")
                        for team in teams:
                            value_ratio = team.points / team.cost
                            contribution = (team.points / combo_total_points * 100) if combo_total_points > 0 else 0
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;&nbsp;{team.team} (Points: {int(team.points)}, Cost: {team.cost:.1f}M, Value: {value_ratio:.2f}, Contribution: {contribution:.1f}%)")

if __name__ == "__main__":
    main()
