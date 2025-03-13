import pandas as pd
import itertools

def load_data():
    drivers_df = pd.read_csv('data/f1_fantasy_drivers.csv')
    teams_df = pd.read_csv('data/f1_fantasy_teams.csv')
    
    drivers_df['driver'] = drivers_df['driver'].str.replace('_', ' ').str.title()
    teams_df['team'] = teams_df['team'].str.replace('_', ' ').str.title()
    
    return drivers_df, teams_df

def find_all_valid_combinations(drivers_df, teams_df, max_cost=100):
    # Create copies and rename columns
    drivers_df = drivers_df.copy()
    teams_df = teams_df.copy()
    drivers_df = drivers_df.rename(columns={'points_2024': 'points'})
    teams_df = teams_df.rename(columns={'points_2024': 'points'})
    
    # Generate all possible combinations
    driver_combinations = list(itertools.combinations(drivers_df.itertuples(index=False), 5))
    team_combinations = list(itertools.combinations(teams_df.itertuples(index=False), 2))
    
    valid_combinations = []
    min_points = float('inf')
    max_points = 0
    min_combo = None
    max_combo = None
    
    print("Processing combinations...")
    total_combos = len(driver_combinations) * len(team_combinations)
    processed = 0
    
    for driver_combo in driver_combinations:
        for team_combo in team_combinations:
            processed += 1
            if processed % 100000 == 0:
                print(f"Processed {processed:,} of {total_combos:,} combinations")
                
            total_cost = sum(driver.cost for driver in driver_combo) + sum(team.cost for team in team_combo)
            
            if total_cost <= max_cost:
                total_points = (
                    sum(driver.points for driver in driver_combo) +
                    sum(team.points for team in team_combo)
                )
                
                valid_combinations.append((driver_combo, team_combo, total_points, total_cost))
                
                if total_points < min_points:
                    min_points = total_points
                    min_combo = (driver_combo, team_combo, total_cost)
                
                if total_points > max_points:
                    max_points = total_points
                    max_combo = (driver_combo, team_combo, total_cost)
    
    return len(valid_combinations), min_combo, max_combo

def print_combo_details(combo, combo_type):
    drivers, teams, cost = combo
    total_points = (
        sum(driver.points for driver in drivers) +
        sum(team.points for team in teams)
    )
    
    print(f"\n{combo_type} Points Combination:")
    print(f"Total Points: {total_points:.1f}")
    print(f"Total Cost: {cost:.1f}M")
    print("\nDrivers:")
    for driver in drivers:
        print(f"- {driver.driver}: {driver.points:.1f} points, {driver.cost:.1f}M")
    print("\nTeams:")
    for team in teams:
        print(f"- {team.team}: {team.points:.1f} points, {team.cost:.1f}M")

def main():
    drivers_df, teams_df = load_data()
    
    print("Calculating all valid combinations...")
    total_valid, min_combo, max_combo = find_all_valid_combinations(drivers_df, teams_df)
    
    print(f"\nTotal number of valid combinations: {total_valid:,}")
    
    print_combo_details(min_combo, "Lowest")
    print_combo_details(max_combo, "Highest")

if __name__ == "__main__":
    main()