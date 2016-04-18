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
constrName='2_Games_on_Sat'
myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,'SATE_NFL',15] * myGames[a,h,'SATL_NFL',15] for h in T for a in H[h]) == 1,name=constrName)
myModel.update()

#constraint 8: There is only one “double header” game in weeks 1 through 16 (and two in week 17)
#Week 1:16
for w in range(1,17):
    constrName= '1_DH_in_w%s' %w
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h] for s in ['SUNDH_CBS','SUNDH_FOX']) == 1, name=constrName)
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
constrName='2_Mondays_in_w1'
myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,1]for h in T for a in H[h] for s in ['MON1_ESPN','MON2_ESPN']) == 2,name=constrName)
myModel.update()

#constraint 10 Part 2: The late Monday Night Game must be hosted by a West Coast Team (SD, SF, SEA, OAK, LAR)
WC=['SD', 'SF', 'SEA', 'OAK', 'LAR'] #List of west coast teams
Mondays=['MON1_ESPN','MON2_ESPN']

for w in range(1,17):
    for s in Mondays:
        if s in S[w]:
            constrName='%s_slot_w%s' %(s,w)
            myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in WC for a in H[h]) == 1, name=constrName)
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
    constrName='WstCst_MtTm_cannot_SUNE'
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in WCMT for a in H[h] for s in ['SUNE_CBS','SUNE_FOX'])==0,name=constrName)
myModel.update()
    
#constraint 12: No team plays 4 consecutive home/away games in a season (treat a BYE game as an away game)
for w in range(1,14):
    for h in H:
       constrName ='no_more_than_4_consecutive_games_w%s' %(w)
       myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+4) for s in S[w1]) <= 3, name = constrName)
myModel.update()

#need to add bye games in the for loop 
#check constraints 12 and 13 again to see if these constraints for away games
#check constraints 12 and 13 again to see if these constraints for away games

#constraint 13a: No team plays 3 consecutive home/away games during the weeks 1, 2, 3, 4, 5 and 15, 16, 17 (treat a BYE game as an away game)
for w in range(1,6):
    for h in H:
        constrName ='no_more_than_4_consecutive_games_1_5_w%s' %(w)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+3) for s in S[w1]) <= 2, name = constrName)
    ##need to add bye games in the for loop 
myModel.update()
        
#constraint 13b:
for h in H:
    constrName ='no_more_than_4_consecutive_games_15_18_w15'
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for a in H[h] for w in range(15, 18) for s in S[w]) <= 2, name = constrName)
    #need to add bye games
myModel.update()

#constraint 14: Each team must play at least 2 home/away games every 6 weeks
for w in range(1,13):
    for h in H:
        constrName ='at_least_2games_per6weeks_w%s' %(w)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+6) for s in S[w1]) >= 2, name = constrName)
myModel.update()

#constraint 15: Each team must play at least 4 home/away games every 10 weeks
for w in range(1,8): #adding 10 weeks goes beyond week 17
    for h in H:
        constrName ='at_least_4homeaway_every10weeks_w%s' %(w)
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w1] for a in H[h] for w1 in range(w, w+10) for s in S[w1]) >= 4, name = constrName)
myModel.update()

#myModel.optimize()
#name="NFL_HW1"
#myModel.write(name+'.lp')


###############################################################################
#Constraint 16:Superbowl champion from 2015 opens the season at home on Thursday night of Week 1
for h in H:
    for a in H[h]:
        for s in S[1]:
                if s[:4] == "THUN" and h!= 'DEN':
                        myModel.remove(myGames[a,h,s,1])
                        del myGames[a,h,s,1]
myModel.update




#To be edited: Emad says: No , no need for editing.
#Constraint 17: DAL and DET play at home on Thanksgiving day during the afternoon
    # FOX gets DAL; CBS gets DET
    # DET gets Early game, DAL gets Late game
for h in H:
    for a in H[h]:
        for s in S[12]:
            if any ([s=='THUE_CBS' and h!='DET' , s=='THUL_FOX' and h!='DAL'])  : 
                myModel.remove(myGames[a,h,s,12])
                del myGames[a,h,s,12]
myModel.update

#Constraint 18 is redundant. Cuz there is only 1 thursday night game played on both weeks and by default they are hosted on NBC
#Constraint 18: NBC gets Thursday Night Games Week 1 and Week 12 (Thanksgiving)
for h in H:
    for a in H[h]:
        for w in [1,12]:
            for s in S[w]:
                if (s [:4] == 'THUN') and (s[len(s)-3:] != 'NBC'): # If the slot is thursday night and the NBC is not hosting. Remove it.
                        myModel.remove(myGames[a,h,s,w])
                        del myGames[a,h,s,w]
myModel.update       

#Constraint 19 : CBS gets Thursday Night Games Weeks 2 though 9
for h in H:
    for a in H[h]:
        for w in range (2,10):
            for s in S[w]:
                if (s[:4] == "THUN") and (s[len(s)-3:] != "CBS"): #If there is a THUN  game and not on CBS, remove it.
                    myModel.remove(myGames[a,h,s,w])
                    del myGames[a,h,s,w]
myModel.update       
              
#Constraint 20: NFL gets Thursday Night Games Weeks 10, 11, 13-16 (and Saturday night games)
for h in H:
    for a in H[h]:
        for w in [10, 11, 13,14,15,16]:
            for s in S[w]:
                if  any ([s[:4] == "THUN" , s[:4] =="SATN"]) and (s[len(s)-3:] != "NFL"):
                    myModel.remove(myGames[a,h,s,w])
                    del myGames[a,h,s,w]
myModel.update   

# Constraint 21:FOX/CBS each get at least 3 Early games on Sundays
for s in ['SUNE_CBS','SUNE_FOX']:
    constrName='Atleast_3_EGames_Sun'
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h] for w in range(1,18)) >= 3, name=constrName)
myModel.update()

# Constraint 22:
# Create Sunday list.
# if Type Error or unhashable, check slots list syntax
#Sundays
for chnl in ['FOX','CBS']:
    constrName='Atleast_5_Sun_Games'
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h] for w in range(1,18) for s in S[w] if s[:3]=='SUN' and s[len(s)-3:]==chnl) >= 5, name=constrName)
myModel.update()

#Constraint 23:
for chnl in ['FOX','CBS']:
    constrName='FOX&CBS_Get_8_DH'
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h] for w in range(1,17) for s in S[w] if s=='SUNDH_'+chnl) == 8, name=constrName)
myModel.update()

# Constraint 24:
for chnl in ['FOX','CBS']:
    constrName='1_DH_each_in_17'
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,17] for h in T for a in H[h] for s in S[17] if s[len(s)-3:]==chnl and s[3:5]=='DH') == 1, name=constrName)

# Constraint 25:
for i in range (1,17):    
    for chnl in ['FOX','CBS']:
        constrName='2_DH_in_row'
        myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h] for w in range(i,i+2) for s in S[w] if s[len(s)-3:]==chnl and s[3:5]=='DH') < 2, name=constrName)

# Constraint 26:  
for h in T:
    constrName='PrimeTime<=5'
    myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for a in H[h] for w in range(1,18) for s in S[w] if s[4:5] == 'N' and w!= 12)  <= 5 , name=constrName)

#Constraint 27 :
constrName='NBC<4'
myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for h in T for a in H[h] for w in range(1,18) for s in S[w] if s[len(s)-3:] == 'NBC')  <= 4 , name=constrName)

#Constrint 28: Teams playing an international game will have a home game the week before their international game
for h in T:
    for w in range (1,17):
        for next_week_slots in S[w+1]:
            if next_week_slots =='SUNI_NFL':
                constrName='Home_Before_Int'
                myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w] for a in H[h] for s in S[w])  == 1 , name=constrName)
                
                
#Constraint 29: Teams playing an international game will have their BYE game the week following the international game
for h in T:
    for w in range (1,17):
        for this_week_slots in S[w]:
            if this_week_slots =='SUNI_NFL':
                constrName='Bye_After_Int'
                myConstr[constrName]=myModel.addConstr(quicksum(myGames[a,h,s,w+1] for a in H[h] for s in S[w] if s == 'SUNB_NFL' )  == 1 , name=constrName)

      

#myModel.setParam('MIPFocus',1)
#myModel.optimize()
#name="NFL_HW1"
#myModel.write('NFL_HW1.lp')




'''
===============================TESTING ========================================
'''

# Constraint 16:
# Before Applying Constraint
('LAR', 'ARZ', 'THUN_NBC', 1) in myGames
Out[20]: True

# After Apllying it
('LAR', 'ARZ', 'THUN_NBC', 1) in myGames
Out[20]: False

('ATL', 'DEN', 'THUN_NBC', 1) in myGames
Out[23]: True

#Constraint 17
#Before appying constraint
('LAR','ARZ','THUE_CBS',12) in myGames
Out[26]: True
('LAR','ARZ','THUL_FOX',12) in myGames
Out[27]: True
#After applying it
('LAR','ARZ','THUE_CBS',12) in myGames
Out[29]: False
('LAR','ARZ','THUL_FOX',12) in myGames
Out[30]: False
#Error Catched
('CHI','DET','THUL_FOX',12) in myGames
Out[31]: True
#Error Fixed
('CHI','DET','THUL_FOX',12) in myGames
Out[37]: False
#Continue Testing
#Affirmitivie 
(H['DAL'] [1],'DAL','THUL_FOX',12) in myGames
Out[44]: True
(H['DET'] [1],'DET','THUE_CBS',12) in myGames
Out[46]: True
#Test Cases Passed

#Constraint 18
#Before applying
(H['ARZ'] [1],'ARZ','THUN_NBC',1) in myGames
Out[62]: False

for h in T:
    for a in H[h]:
        print (a,h,'THUN_NBC',1) in myGames , h
        
# Only DEN plays on THUN   according to constriant 1   
(H['DEN'] [1],'DEN','THUN_NBC',1) in myGames # True

#After Applying
(H['DEN'] [1],'DEN','THUN_NBC' , 1 ) in myGames
Out[58]: True

(H['ARZ'] [1],'ARZ','THUN_NBC',1) in myGames
Out[59]: False


#Constrint 19: CBS gets Thursday Night Games Weeks 2 though 9
testdict = {}
for h in T:
    for a in H[h]:
        for w in range (2,10):
            for s in S[w]:
                if s[:4] == "THUN": # If there is a Thursday night game (in any slot) in that week.
                    testdict[a,h,w] = [(a,h,s,w) in myGames ,a, h , w,s]
#All True : If there is a thursday game that week, there all possible team combination for late night thursday.
#Passed                   
               
# Constraint 20
testdict = {}              
for h in H:
   for a in H[h]:
       for w in [10, 11, 13,14,15,16]:
           for s in S[w]:
               if any ([s[:4] == "THUN" , s[:4] =="SATE" , s[:4] =="SATL"]) and (a,h,w,s) in myGames:
                   testdict [a,h,w,s] =  (a,h,w,s) in myGames
                   
                  