# google-sheets-elo-system
In this very basic elo tracking system google sheets and python are used to create a simple solution to store, update and show data on matches, elo and ranking. The [elo system](https://en.wikipedia.org/wiki/Elo_rating_system) originates from chess where games are played 1v1. In this version the system is expanded to support teams by taking the average elo of the players and treating the team as a single player for the calculation. Furthermore, the support for scores is added to allow further differentiation as to how good a win was as opposed to binary win or loss. The traditional method is still supported though by simply setting the score as 1:0.

## Dependencies
- A Google account
- [Python 3.x](https://www.python.org/downloads/) with the following packages:
  - [pandas](https://pandas.pydata.org/) for interacting with datatables
  - [gspread](https://github.com/burnash/gspread) for connecting with google sheets
  - [gspread_dataframe](https://pypi.org/project/gspread-dataframe/) for turning google sheets into pandas dataframes
  - [oauth2client](https://github.com/googleapis/oauth2client) for authentication

## Using the elo system
In this section the basic setup to use this system is explained.

### Setting up Google Sheets
Create a new google sheet following this [template](https://docs.google.com/spreadsheets/d/12GHAyL_vlRE2LlCm-D4fuKdobR6QmnYo0UCDBYdp2sE/edit?usp=sharing).
The **Matches** worksheet will be used to enter the games that were played. Games can be played in teams of up to two players. Players 1 and 2 are the first team and players 3 and 4 are the second team. If only one player is in a team, write the same name twice. If you want support for more players, feel free to extend the code. It is intended for team 1 to be the team that makes the first move, this is however not strictly necessary to keep track of. In the score columns the final scores should be noted. The only requirement is that both teams have some number as their score and the higher score is considered the winner. Any range of positive numbers is supported. If the score doesn't matter you can simply always use 1:0 to indicate a win. The score is taken into consideration when calculating the rating change. For example a game with a score of 10:0 will result in a larger rating change than a game with a score of 10:9.

The **Ranking** worksheet will later contain the results of the computation.

### Setting up API access
You will need to set up authentication and authorization to read and write in your google sheet. Google explains [how to do this](https://developers.google.com/workspace/guides/auth-overview). You will need to create a service account and grant that account access rights from within google sheets. The scopes used are: 
- `https://spreadsheets.google.com/feeds`
- `https://www.googleapis.com/auth/drive`

### Run the python script
Add some matches to the matches worksheet and run the python script.

`> python matches.py`

The ranking sheet should now be updated with a sorted list of players with a number of stats.
- ELO: the number used to determine the rank
- Game Count: how many games that player has played, useful for filtering out players with few games
- Win Rate: games won divided by games played
- Good With, Bad With, Good Against, Bad Against: pairings of players which have the highest or lowest win rates respectively

There will also be another worksheet called **Rank Changes**, which contains the elo of each player after each match. This is mostly interesting for debugging purposes.

## Technical Stuff
Currently whenever the script is run to update the ranking, the calculation is done from the beginning for all matches. This ensures that there are never precision issues due to storing inaccurate numbers, but if you start having very many matches, the performance will inevitably begin to deteriorate. The elo calculation can also be done completely iteratively though, so if you feel like adding this functionality, feel free to make a pull request.

## License
The software is provided under the [MIT License](https://github.com/Eddykasp/google-sheets-elo-system/blob/main/LICENSE).