# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 08:34:54 2016

@author: John
"""
import csv 
from gurobipy import * 

H = {}
myFile = open('Opponents Season 2016.csv','rt')
myReader = csv.reader(myFile)    
for row in myReader:
    if row[0] != 'Away Team':
        
        if row[1] in H:
            H[row[1]].append(row[0])
        else:
            H[row[1]] = [row[0]]

myFile.close()


A = {}
myFile = open('Opponents Season 2016.csv','rt')
myReader = csv.reader(myFile) 
for row in myReader:
    if row[0] != 'Away Team':
        
        if row[0] in A:
            A[row[0]].append(row[1])
        else:
            A[row[0]] = [row[1]]
        

myFile.close()

S = {}
myFile= open('Slots.csv')
myReader = csv.reader(myFile)
for row in myReader:
    for cell in row:
        if len(cell)!=0 and cell!=row[0]:
            if int(row[0]) in S:
                S[int(row[0])].append(cell)
            else:
                S[int(row[0])]=[cell]

del(row,cell)
myFile.close()

T = ['DAL', 'NYG', 'PHI','WAS','CHI', 'DET', 'GB','MIN','ATL','CAR','NO','TB',
     'ARZ','LAR','SF','SEA','BUF','MIA','NE','NYJ','BAL','CIN','CLE','PIT',
     'HOU','IND','JAC','TEN','DEN','KC','OAK','SD']

     
DIVISION = {'NFC':{'EAST':['DAL', 'NYG', 'PHI','WAS'],
                   'NORTH':['CHI', 'DET', 'GB','MIN'],
                   'SOUTH':['ATL', 'CAR','NO','TB'],
                   'WEST':['ARZ','LAR','SF','SEA']
                   },
            'AFC':{'EAST': ['BUF','MIA','NE','NYJ'],
                   'NORTH': ['BAL','CIN','CLE','PIT'],
                   'SOUTH': ['HOU','IND','JAC','TEN'],
                   'WEST': ['DEN','KC','OAK','SD']            
                   }
            }
CONFERENCE = {'NFC':['DAL', 'NYG', 'PHI','WAS','CHI', 'DET', 'GB','MIN','ATL','CAR','NO','TB','ARZ','LAR','SF','SEA'],
              'AFC':['BUF','MIA','NE','NYJ','BAL','CIN','CLE','PIT','HOU','IND','JAC','TEN','DEN','KC','OAK','SD']
            }
            
myModel = Model()
myModel.modelSense = GRB.MINIMIZE
myModel.update()
            
##OBJECTIVE FUNCTION##
myGames = {}
for h in T:
    for a in H[h]:
        for w in range(1,18):
            for s in S[w]:
                myGames[a,h,s,w] = myModel.addVar(obj =1, vtype=GRB.BINARY, 
                                    name='games_%s_%s_%s_%s' % (a,h,s,w))

for a in T:
    for w in range(4,12):
        myGames[a,'BYE','SUNB_NFL',w] = myModel.addVar(obj =1, vtype=GRB.BINARY, 
                                        name='games_%s_%s_%s_%s' % (a,h,s,w))
                                        
myModel.update()                                        
########################################################################################################################

## CONSTRAINTS
myConstr = {}

#constraint 1: every game played once 
for h in T: #iterate over all 32 teams (a,h)
    for a in H[h]: #each away team
        constrName = '1_game_once_%s_%s' % (a,h)
        myConstr[constrName] = myModel.addConstr(quicksum(myGames[a,h,s,w]
                                        for w in range (1,18) for s in S[w]) == 1,
                                        name = constrName)
myModel.update()  
                                                                          
#constraint 2: teams play one game each week (takes care  of everything but bye games)
for t in T:
    for w in [1,2,3,12,13,14,15,16,17]:
        constrName = '1_in_w%s_by_%s' % (w,t)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,t,s,w] for a in H[t] for s in S[w]) 
                            + quicksum(myGames[t,h,s,w] for h in A[t] for s in S[w]) == 1, 
                            name=constrName)
myModel.update()
        
#constraint 3: teams play one game each week (takes care of bye games)
for t in T:
    for w in range(4,12):
        constrName = '1_bye_in_w%s_by_%s' %(w,t)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,t,s,w] for a in H[t] for s in S[w] if s != 'SUNB_NFL') 
        + quicksum(myGames[t,h,s,w] for h in A[t] for s in S[w] if s != 'SUNB_NFL') 
        + myGames[t, 'BYE', 'SUNB_NFL', w] == 1, name=constrName)
myModel.update()
        
#constraint 4:No more than 6 bye games in a given a week
for w in range(4,12):
    constrName = '4_Bye_game_by_%s_in_w%s' % (t,w)
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[t,'BYE','SUNB_NFL',w] for t in T)<=6, name=constrName)

w = None
myModel.update()

#contraint 5: No team that had an early bye game (week 4) in 2015 can have an early bye game (week 4) in 2016
constrName = 'TEN,NE do not play in week 4'
myConstr[constrName]=myModel.addConstr(myGames['NE','BYE','SUNB_NFL',4] + myGames['TEN','BYE','SUNB_NFL',4]==0,
name=constrName)
myModel.update()

#constraint 6: Exactly 1 Thursday game every week upto week 16, week 17 has no thursday games
Thursday = ['THUN_NBC' , 'THUN_NFL' , 'THUN_NFL' , 'THUE_FOX' ,'THUL_CBS', 'THUN_NBC' , 'THUN_CBS'  ]
for w in range(1,17):
    for s in S[w]:
        if s in Thursday:
            constrName='6_one_Thursady_in_w%s' %(w)
            myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h] ) ==1 ,name=constrName)
myModel.update()

#constraint 7:There are two Saturday Night Games in Week 15 (one SatE and one SatL)
for s in ['SATE_NFL','SATL_NFL']:
    constrName='2_Games_on_Sat_s%s' %(s)
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,15] for h in T for a in H[h]) == 1,name=constrName)
myModel.update()

#constraint 8: There is only one “double header” game in weeks 1 through 16 (and two in week 17)
#Week 1:16
for w in range(1,17):
    for s in ['SUNDH_CBS','SUNDH_FOX']:
        constrName= '1_DH_in_w%s%s' %(w,s)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h]) == 1, name=constrName)
myModel.update()
 
#Week 17   
constrName='2_DH_in_17'
myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,17] for h in T for a in H[h] for s in ['SUNDH_CBS','SUNDH_FOX']) == 2,name=constrName)
myModel.update()

#constraint 9: There is exactly one Sunday Night Game in weeks 1 through 16 (no Sunday Night Game in week 17)
#Week 1:16
for w in range(1,17):
    constrName='1_SundayNight_in_w%s' %w
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,'SUNN_NBC',w] for h in T for a in H[h]) == 1,name=constrName)
myModel.update()

#constraint 10 Part 1: There are two Monday night games in week 1
WC=['SD', 'SF', 'SEA', 'OAK', 'LAR']

constrName='2_Mondays_in_w1'
myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,1]for h in T for a in H[h] for s in ['MON1_ESPN','MON2_ESPN']) == 2,name=constrName)
myModel.update()

#constraint 10 Part 2: The late Monday Night Game must be hosted by a West Coast Team (SD, SF, SEA, OAK, LAR)
 #List of west coast teams

for w in range(1,17):
    if s in S[w]:
        constrName='%s_slot_w%s' %(s,w)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,'MON2_ESPN',w] for h in WC for a in H[h]) == 1, name=constrName)
myModel.update()

#constraint 10 Part 3: There in exactly one Monday night game in weeks 2 through 16 (no Sunday Night Game in week 17))
# Week 2:16
for w in range(2,17):
    constrName='1_Monday_in_w%s' %(w)
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,'MON1_ESPN',w] for h in T for a in H[h]) ==1 , name=constrName)
myModel.update()

#constraint 11: West Coast (SD, SF, SEA, OAK, LAR) and Mountain Teams (DEN, ARZ) cannot play at home in the early Sunday time slot
MT=['DEN','ARZ']
WCMT=WC+MT

for w in range(1,18):
    constrName='WstCst_MtTm_cannot_SUNE_w%s' %(w)
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in WCMT for a in H[h] for s in ['SUNE_CBS','SUNE_FOX'])==0,name=constrName)
myModel.update()
    
#constraint 12_Home_Games: No team plays 4 consecutive home/away games in a season (treat a BYE game as an away game)
for w in range(1,15):
    for h in H:
       constrName ='no_more_than_4_consecutive_games_in_w%s_at_h%s' %(w,h)
       myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+4) for s in S[w1]) <= 3, name = constrName)
myModel.update()

#constraint 12_Away_Games:
for w in range(1,15):
    for a in A:
       constrName ='no_more_than_4_consecutive_games_w%s_at_a%s' %(w,a)
       myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for h in A[a] for w1 in range(w, w+4) for s in S[w1]) <= 3, name = constrName)
myModel.update()

#constraint 13a_Home_Games: No team plays 3 consecutive home/away games during the weeks 1, 2, 3, 4, 5 and 15, 16, 17 (treat a BYE game as an away game)
for w in range(1,4):
    for h in H:
        constrName ='no_more_than_4_consecutive_games_1_5_w%s_at_h%s' %(w,h)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+3) for s in S[w1]) <= 2, name = constrName)    
myModel.update()

#Constraint 13a_Away_Games:
for w in range(1,4):
    for a in A:
        constrName ='no_more_than_4_consecutive_games_1_5_w%s_at_a%s' %(w,a)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for h in A[a] for w1 in range(w, w+3) for s in S[w1]) <= 2, name = constrName) 
myModel.update()
        
#constraint 13b_Home_Games:
for h in H:
    constrName ='no_more_than_4_consecutive_games_15_18_w15_%s' %h
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for a in H[h] for w in range(15, 18) for s in S[w]) <= 2, name = constrName)
    #need to add bye games
myModel.update()

#constraint 13b_Away_Games:
for a in A:
    constrName ='no_more_than_4_consecutive_games_15_18_w15_%s' %a
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in A[a] for w in range(15, 18) for s in S[w]) <= 2, name = constrName)
    #need to add bye games
myModel.update()

#constraint 14_Home_Games: Each team must play at least 2 home/away games every 6 weeks
for w in range(1,13):
    for h in H:
        constrName ='at_least_2games_per6weeks_w%s_at_h%s' %(w,h)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+6) for s in S[w1]) >= 2, name = constrName)
myModel.update()

#constraint 14_Away_Games
for w in range(1,13):
    for a in A:
        constrName ='at_least_2games_per6weeks_w%s_at_a%s' %(w,a)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for h in A[a] for w1 in range(w, w+6) for s in S[w1]) >= 2, name = constrName)
myModel.update()
#constraint 15: Each team must play at least 4 home/away games every 10 weeks
for w in range(1,8): #adding 10 weeks goes beyond week 17
    for h in H:
        constrName ='at_least_4homeaway_every10weeks_w%s_h%s' %(w,h)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+11) for s in S[w1]) >= 4, name = constrName)
myModel.update()

myModel.optimize()
name="NFL_HW1"
myModel.write(name+'.lp')
