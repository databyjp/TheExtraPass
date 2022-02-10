import pandas as pd
from nba_api.stats.endpoints import shotchartdetail
import json

response = shotchartdetail.ShotChartDetail(
    team_id=0,
    player_id=201935,
    season_nullable="2018-19",
    date_from_nullable=20181210,
    date_to_nullable=20181201,
    season_type_all_star="Regular Season",
)

content = json.loads(response.get_json())

# transform contents into dataframe
results = content["resultSets"][0]
headers = results["headers"]
rows = results["rowSet"]
df = pd.DataFrame(rows)
df.columns = headers
