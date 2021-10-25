import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gspread_dataframe as gd
import math

#####################################################
# CONFIG STUFF                                      #
#####################################################
# Filename of file containing the credentials for   #
# accessing google services                         #
credentials_file = 'REPLACE WITH ACTUAL FILE NAME'  #
# Name of the google sheet that should be used      #
google_sheets_name = 'REPLACE WITH ACTUAL FILE NAME'#
#####################################################

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name(
         credentials_file, scope)

K = 20

def flipNegative(x):
    if (x < 0):
        return 2
    else:
        return x

# This is necessary when using google sheets where commas are used to 
# represent decimal points
def convertNumber(x):
    try:
        result = str(round(x, 2)).replace(".", ",")
        return result
    except:
        return x

def expectedScore(eloA, eloB):
    return 1 / (1+10**((eloA - eloB)/400))

def eloChange(k, old_elo, expectedV, win):
    res = k * (win - expectedV)
    return res

def kFunction(x):
    if x > 100:
        return K
    return 1/(math.e**(x-5)) + K

class Match:
    def __init__(self, p1, p2, p3, p4, scores):
        self.players = [[p1, p2], [p3, p4]]
        
        if int(scores[0]) > int(scores[1]):
            self.winner = 0
        elif int(scores[1]) > int(scores[0]):
            self.winner = 1
        else:
            self.winner = -1
        # score is score of team 0
        normalisation_factor = 10 - int(scores[self.winner])
        scores[0] = float(scores[0]) + normalisation_factor
        scores[1] = float(scores[1]) + normalisation_factor
        self.score = float(scores[0]) / (float(scores[0]) + float(scores[1]))

def loadMatches(filename):
    gc = gspread.authorize(credentials)
    sh = gc.open(filename)
    wks = sh.worksheet("Matches")
    data = wks.get_all_values()
    headers = data.pop(0)
    df = pd.DataFrame(data, columns=headers)

    match_list = []

    for _, row in df.iterrows():
        players = [row['Player 1'],
                   row['Player 2'],
                   row['Player 3'],
                   row['Player 4']]
        scores = [
            row['Score 1'],
            row['Score 2']
        ]
        
        match_list.append(MatchV2(players[0], players[1], players[2], players[3], scores))
    return match_list

def computeStats(match_list, sheet_name):
    rank_changes = {}
    ranking = {}
    game_count = {}
    win_count = {}
    
    wins_with = {}
    games_with = {}

    wins_against = {}
    games_against = {}

    for match in match_list:

        # initialise player rankings or load existing elo
        elo = {}
        for team in match.players:
            for player in team:
                if player not in ranking:
                    ranking[player] = 1200
                    game_count[player] = 0
                    win_count[player] = 0

                    wins_with[player] = {}
                    games_with[player] = {}

                    wins_against[player] = {}
                    games_against[player] = {}
                elo[player] = ranking[player]
        
        # game counting phase
        for i in range(len(match.players)):
            team = match.players[i]
            others = match.players[(i+1)%2]
            if team[0] == team[1]:
                game_count[team[0]] += 1

                # game with self
                if team[0] not in games_with[team[0]]:
                    games_with[team[0]][team[0]] = 1
                else:
                    games_with[team[0]][team[0]] += 1
                
                # game against opponents
                if others[0] != others[1]:
                    if others[0] not in games_against[team[0]]:
                        games_against[team[0]][others[0]] = 1
                    else:
                        games_against[team[0]][others[0]] += 1
                
                if others[1] not in games_against[team[0]]:
                    games_against[team[0]][others[1]] = 1
                else:
                    games_against[team[0]][others[1]] += 1

            else:
                game_count[team[0]] += 1
                game_count[team[1]] += 1

                # game with each other
                if team[1] not in games_with[team[0]]:
                    games_with[team[0]][team[1]] = 1
                else:
                    games_with[team[0]][team[1]] += 1
                
                if team[0] not in games_with[team[1]]:
                    games_with[team[1]][team[0]] = 1
                else:
                    games_with[team[1]][team[0]] += 1

                # game against opponents
                if others[0] != others[1]:
                    if others[0] not in games_against[team[0]]:
                        games_against[team[0]][others[0]] = 1
                    else:
                        games_against[team[0]][others[0]] += 1

                    if others[0] not in games_against[team[1]]:
                        games_against[team[1]][others[0]] = 1
                    else:
                        games_against[team[1]][others[0]] += 1
                
                if others[1] not in games_against[team[0]]:
                    games_against[team[0]][others[1]] = 1
                else:
                    games_against[team[0]][others[1]] += 1

                if others[1] not in games_against[team[1]]:
                    games_against[team[1]][others[1]] = 1
                else:
                    games_against[team[1]][others[1]] += 1
        
        # elo expected scores
        team_elo = [
            (elo[match.players[0][0]] + elo[match.players[0][1]])/2,
            (elo[match.players[1][0]] + elo[match.players[1][1]])/2
        ]

        expected = [
            expectedScore(team_elo[1], team_elo[0]),
            expectedScore(team_elo[0], team_elo[1])
        ]

        # win counting
        if match.winner != -1:
            team = match.players[match.winner]
            others = match.players[(match.winner+1)%2]

            if team[0] == team[1]:
                win_count[team[0]] += 1

                # win with self
                if team[0] not in wins_with[team[0]]:
                    wins_with[team[0]][team[0]] = 1
                else:
                    wins_with[team[0]][team[0]] += 1

                # win against opponents
                if others[0] != others[1]:
                    if others[0] not in wins_against[team[0]]:
                        wins_against[team[0]][others[0]] = 1
                    else:
                        wins_against[team[0]][others[0]] += 1

                if others[1] not in wins_against[team[0]]:
                    wins_against[team[0]][others[1]] = 1
                else:
                    wins_against[team[0]][others[1]] += 1

            else:
                win_count[team[0]] += 1
                win_count[team[1]] += 1

                # win with each other
                if team[1] not in wins_with[team[0]]:
                    wins_with[team[0]][team[1]] = 1
                else:
                    wins_with[team[0]][team[1]] += 1

                if team[0] not in wins_with[team[1]]:
                    wins_with[team[1]][team[0]] = 1
                else:
                    wins_with[team[1]][team[0]] += 1

                # win against opponents
                if others[0] != others[1]:
                    if others[0] not in wins_against[team[0]]:
                        wins_against[team[0]][others[0]] = 1
                    else:
                        wins_against[team[0]][others[0]] += 1

                    if others[0] not in wins_against[team[1]]:
                        wins_against[team[1]][others[0]] = 1
                    else:
                        wins_against[team[1]][others[0]] += 1
                
                if others[1] not in wins_against[team[0]]:
                    wins_against[team[0]][others[1]] = 1
                else:
                    wins_against[team[0]][others[1]] += 1

                if others[1] not in wins_against[team[1]]:
                    wins_against[team[1]][others[1]] = 1
                else:
                    wins_against[team[1]][others[1]] += 1

        avg_games = 0
        for team in match.players:
            for player in team:
                avg_games += game_count[player]
        avg_games /= 4

        k = kFunction(avg_games)

        delta = [
            eloChange(k, team_elo[0], expected[0], match.score),
            eloChange(k, team_elo[1], expected[1], 1 - match.score)
        ]

        # update elo values
        for i in range(len(match.players)):
            ranking[match.players[i][0]] += delta[i]
            ranking[match.players[i][1]] += delta[i]

        # append to rank change lists
        for player in ranking:
            if player not in rank_changes:
                rank_changes[player] = []
            rank_changes[player].append(ranking[player])

    # calculate interplayer winrates
    winrate_with = {}
    winrate_against = {}

    for player in ranking:
        winrate_with[player] = {}
        winrate_against[player] = {}
        
        for player2 in ranking:
            if player2 not in wins_with[player]:
                wins_w = 0
            else:
                wins_w = wins_with[player][player2]
                
            if player2 not in wins_against[player]:
                wins_a = 0
            else:
                wins_a = wins_against[player][player2]

            if player2 in games_with[player]:
                winrate_with[player][player2] = wins_w / games_with[player][player2]
            else:
                winrate_with[player][player2] = -1

            if player2 in games_against[player]:
                winrate_against[player][player2] = wins_a / games_against[player][player2]
            else:
                winrate_against[player][player2] = -1
            
    wins_with_df = pd.DataFrame(winrate_with)
    wins_against_df = pd.DataFrame(winrate_against)
    
    rank_list = list(reversed(sorted(ranking.items(), key=lambda kv: kv[1])))
    rank_list = list(map(lambda kv: (kv[0], int(round(kv[1]))), rank_list))

    best_wins_with = []
    best_wins_against = []
    worst_wins_with = []
    worst_wins_against = []

    for (k,_) in rank_list:
        best_wins_with.append(wins_with_df[k].idxmax())
        best_wins_against.append(wins_against_df[k].idxmax())

    altered_with = wins_with_df.applymap(lambda x: flipNegative(x))
    altered_against = wins_against_df.applymap(lambda x: flipNegative(x))

    for (k,_) in rank_list:
        worst_wins_with.append(altered_with[k].idxmin())
        worst_wins_against.append(altered_against[k].idxmin())
        
    count_list = []
    for (k,_) in rank_list:
        count_list.append(game_count[k])

    win_list = []
    for (k,_) in rank_list:
        win_list.append(str(round(win_count[k]/game_count[k], 2)).replace(".", ","))
    
    # update spreadsheet
    gc = gspread.authorize(credentials)
    sh = gc.open(sheet_name)

    out_wks = sh.worksheet("Ranking")
    rank_df = pd.DataFrame(rank_list)

    rank_df.columns = ["Name", "ELO"]

    rank_df.insert(2, "Game Count", count_list)
    rank_df.insert(3, "Win Rate", win_list)
    rank_df.insert(4, "Good With", best_wins_with)
    rank_df.insert(5, "Bad With", worst_wins_with)
    rank_df.insert(6, "Good Against", best_wins_against)
    rank_df.insert(7, "Bad Against", worst_wins_against)
    
    gd.set_with_dataframe(out_wks, rank_df)

    # export rank_changes
    with open("rank_changes.csv", 'w') as file:
        for player in rank_changes:
            file.write(player)
            for item in rank_changes[player]:
                file.write(", " + str(item))
            file.write("\n")

    rank_changes_df = pd.read_csv("rank_changes.csv").transpose()
    rank_changes_df = rank_changes_df.applymap(lambda x: convertNumber(x))
    gd.set_with_dataframe(sh.worksheet("Rank Changes"), rank_changes_df)

 

if __name__ == "__main__":
    match_list = loadMatches(google_sheets_name)
    computeStats(match_list, google_sheets_name)
