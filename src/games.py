import datetime
import copy
import random, operator
import urllib2
import json
from BeautifulSoup import BeautifulSoup,Tag
import datetime

def ordinalize(number):
    if 4 <= number <= 20 or 24 <= number <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][number % 10 - 1]
        
    return "%s%s" % (number, suffix)

page = urllib2.urlopen("http://www.nhl.com/ice/schedulebyseason.htm")
soup = BeautifulSoup(page)

table = soup.find("table",{"class":"data schedTbl"})
table_body = table.find('tbody')

games = []

for row in table_body.findAll('tr'):
    game = {}
    col = row.findAll('td')
    date = col[0].find('div', {'class': 'skedStartDateSite'}).contents[0]
    date = datetime.datetime.strptime(date, '%a %b %d, %Y').date()
    
    home = col[2].find('a')
    home = str(home['rel'])
    
    away = col[1].find('a')
    away = str(away['rel'])
    
    games.append({'home': home, 'away': away, 'date': date})
    
page = urllib2.urlopen("http://www.nhl.com/ice/standings.htm?type=con")
soup = BeautifulSoup(page)
tables = soup.findAll("table",{"class":"data standings Conference"})

east_table = tables[0]
west_table = tables[1]

TEAM_DIVISION_MAP = {}

def get_standings(table):
    table_body = table.find('tbody')
    CONF_STANDINGS = {}
    
    for row in table_body.findAll('tr'):
        col = row.findAll('td')
        if col[0]['colspan'] != '17':
            team = col[1].find('a')
            team = str(team['rel'])
            
            TEAM_DIVISION_MAP[team] = str(col[2].contents[0])
            
            points = int(col[7].contents[0])
            
            CONF_STANDINGS[team] = points
    
    return CONF_STANDINGS

def print_seqs(seqs):
    for gm in seqs:
        if gm['result'] == 'WIN':
            print "%(home)s beats %(away)s on %(date)s" % gm
        elif gm['result'] == 'OTWIN':
            print "%(home)s beats %(away)s in overtime on %(date)s" % gm
        elif gm['result'] == 'OTLOSE':
            print "%(away)s beats %(home)s in overtime on %(date)s" % gm
        else:
            print "%(away)s beats %(home)s on %(date)s" % gm
            
STANDINGS_EAST = get_standings(east_table)
STANDINGS_WEST = get_standings(west_table)

OPTIONS = [
    ('WIN', 38), ('LOSE', 38), ('OTWIN', 12), ('OTLOSE', 12)
]

sims = 1000000
completed_sims = 0
in_playoffs = 0
out_playoffs = 0
my_team = 'TOR'

best_position = 999
best_points = 0
best_seqs = []
best_order = None

positions = [0] * 15

weighted_choice = lambda s : random.choice(sum(([v]*wt for v,wt in s),[]))

for x in range(sims):
    try:
        STANDINGS = {}
        STANDINGS.update(STANDINGS_EAST)
        STANDINGS.update(STANDINGS_WEST)
        
        sim_games = []
        
        for game in games:
            #result = random.choice(OPTIONS)
            result = weighted_choice(OPTIONS)
            gm = copy.copy(game)
                
            if result == 'WIN':
                STANDINGS[game['home']] += 2
            elif result == 'LOSE':
                STANDINGS[game['away']] += 2
            elif result == 'OTWIN':
                STANDINGS[game['home']] += 2
                STANDINGS[game['away']] += 1
            elif result == 'OTLOSE':
                STANDINGS[game['home']] += 1
                STANDINGS[game['away']] += 2
                
            gm['result'] = result
                
            sim_games.append(gm)
        
        
        NEW_STANDINGS_EAST = {i: j for i, j in STANDINGS.iteritems() if i in STANDINGS_EAST.keys()}
        sorted_e = sorted(NEW_STANDINGS_EAST.iteritems(), key=operator.itemgetter(1), reverse=True)
        
        ATL = set()
        NE = set()
        SE = set()
        
        for team, points in NEW_STANDINGS_EAST.iteritems():
            if TEAM_DIVISION_MAP[team] == 'ATL':
                ATL.add((team, points))
            elif TEAM_DIVISION_MAP[team] == 'NE':
                NE.add((team, points))
            elif TEAM_DIVISION_MAP[team] == 'SE':
                SE.add((team, points))
                
        sorted_atl = sorted(ATL, key=operator.itemgetter(1), reverse=True)
        sorted_ne = sorted(NE, key=operator.itemgetter(1), reverse=True)
        sorted_se = sorted(SE, key=operator.itemgetter(1), reverse=True)
        
        sorted_e = []
        sorted_e.append(sorted_atl.pop(0))
        sorted_e.append(sorted_ne.pop(0))
        sorted_e.append(sorted_se.pop(0))
        
        sorted_e = sorted(sorted_e, key=operator.itemgetter(1), reverse=True)
        the_rest = sorted(sorted_atl + sorted_ne + sorted_se, key=operator.itemgetter(1), reverse=True)
        sorted_e = sorted_e + the_rest
        
        teams_e = [x[0] for x in sorted_e]
        points_e = [x[1] for x in sorted_e]
    
        position = teams_e.index(my_team)
        points = points_e[position]
    
        if position < best_position:
            best_position = position
            best_points = points
            best_seqs = sim_games
            best_order = teams_e
            
        if position <= best_position and points > best_points:
            best_seqs = sim_games
            best_order = teams_e
            best_points = points
            
            print 'New best found! %s could attain %s place with %s points -> %s' % (my_team, ordinalize(position + 1), points, ', '.join(teams_e))
            
        if my_team in teams_e[:8]:
            in_playoffs += 1
        else:
            out_playoffs += 1
            
        positions[position] += 1
            
        #NEW_STANDINGS_WEST = {i: j for i, j in STANDINGS.iteritems() if i in STANDINGS_WEST.keys()}
        #sorted_w = sorted(NEW_STANDINGS_WEST.iteritems(), key=operator.itemgetter(1), reverse=True)
        #print sorted_w
        
        completed_sims += 1
        
        if completed_sims % 1000 == 0:
            print 'Have run %s simulations...' % completed_sims
    except KeyboardInterrupt:
        break
    
print_seqs(best_seqs)

wins = 0
ot_wins = 0
loses = 0
ot_loses = 0
played_games = 0

for gm in best_seqs:
    
    if gm['home'] == my_team:
        played_games += 1
        if gm['result'] == 'WIN':
            wins += 1
        if gm['result'] == 'OTWIN':
            ot_wins += 1
        if gm['result'] == 'LOSE':
            loses += 1
        if gm['result'] == 'OTLOSE':
            ot_loses += 1
    elif gm['away'] == my_team:
        played_games += 1
        if gm['result'] == 'LOSE':
            wins += 1
        if gm['result'] == 'OTLOSE':
            ot_wins += 1
        if gm['result'] == 'WIN':
            loses += 1
        if gm['result'] == 'OTWIN':
            ot_loses += 1
            
print
print '*' * 80
print
    
print "Probability of making playoffs: %s%%" % str(100* float(in_playoffs) / float(completed_sims))
for i, count in enumerate(positions):
    probability = 100 * float(count) / float(completed_sims)
    print '%s: %s%%\t |%s' % (ordinalize(i + 1), probability, '=' * 2 * int(round(probability, 0)))
    if i == 7:
        print '-' * 50 + " The #fail line"

print
print "Best found simulated finish: %s in conference with %s points" % (ordinalize(best_order.index(my_team) + 1), best_points), ', '.join(best_order)
print "Best found simulated finish: %s wins, %s OT wins, %s OT losses, and %s losses (out of %s remaining games)" % (wins, ot_wins, ot_loses, loses, played_games)
