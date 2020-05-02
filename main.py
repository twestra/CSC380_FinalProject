import arcade
import game_core
import threading
import time
import os
import pygame
import numpy as np
import copy
from pprint import pprint


class Agent(threading.Thread):

    def __init__(self, threadID, name, counter, show_grid_info=True):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.show_grid_info = show_grid_info

        self.game = []
        self.move_grid = []
        self.kill_grid = []
        self.isGameClear = False
        self.isGameOver = False
        self.current_stage = 0
        self.time_limit = 0
        self.total_score = 0
        self.total_time = 0
        self.total_life = 0
        self.tanuki_r = 0
        self.tanuki_c = 0
        
    #############################################################
    #      YOUR SUPER COOL ARTIFICIAL INTELLIGENCE HERE!!!      #
    #############################################################
    #variables used in our functions
        #initialize previous_move_grid to -1
        self.previous_move_grid = [[-1 for x in range(20)] for y in range(12)]
        self.policy_grid = [[0 for x in range(20)]for y in range(12)]
        self.value_grid = [[0 for x in range(20)] for y in range(12)]
        self.reward_grid = [[0 for x in range(20)] for y in range(12)]
        self.Q_grid = [[[0 for z in range(6)]for x in range (20)] for y in range(12)]
        #T is amount of iterations we'll do at most
        self.T = 20
        #This is the chance our input will fail; assume the move made will be random
        self.noise = 0
        #Decay
        self.decay = .95
        #Epsilon is the smallest number before we say that we have converged
        self.epsilon = .001
        #Living Reward
        self.livingreward = -.01
    
    def bfs(self, move_grid, cur_r, cur_c, target):
        visited = np.zeros_like(move_grid)
        direction = np.zeros_like(move_grid)
        queue = []
        path = []
        startpos = (cur_r, cur_c)
        if cur_r < 0 or cur_c < 0 or cur_r > 11 or cur_c > 19:
            return
        # target -> found the goal! start backtrack
        # 0 -> always move left
        # 1 -> move only left and right (cannot go to 0)
        # 6 -> move only up or down (cannot go to 4)
        # See homework description for details.
        #print(f"({cur_r:02d},{cur_c:02d}) = {move_grid[cur_r][cur_c]:d}")
        queue.append((cur_r, cur_c))
        while(move_grid[cur_r][cur_c] != target):
            #first, we dequeue the node we are exploring
            queue.pop(0)
            
            #now check if the node has already been explored. If yes, we can skip exploring its children
            if visited[cur_r][cur_c] != 1:
                #print("Explore row:", cur_r, " and column:", cur_c, ". Direction is", direction[cur_r][cur_c])
                visited[cur_r][cur_c] = 1

                
                if move_grid[cur_r][cur_c] == 0:
                    #queue the node directly to the left, and say that node came from left instruction
                    queue.append((cur_r, cur_c-1))
                    if(visited[cur_r][cur_c-1] == 0):
                        direction[cur_r][cur_c-1] = 1
                elif move_grid[cur_r][cur_c] == 1:
                    #move to the right, and say that node came from right instruction
                    if ((move_grid[cur_r][cur_c+1] != 0) and (move_grid[cur_r+1][cur_c+1] == (4 or 6))):
                        queue.append((cur_r, cur_c+1))
                        if(visited[cur_r][cur_c+1] == 0):
                            direction[cur_r][cur_c+1] = 3
                    #move to the left, and say that node came from left instruction
                    if ((move_grid[cur_r][cur_c-1] != 0) and (move_grid[cur_r+1][cur_c-1] == (4 or 6))):
                        queue.append((cur_r, cur_c-1))
                        if(visited[cur_r][cur_c-1] == 0):
                            direction[cur_r][cur_c-1] = 1
                    #move down, and say that node came from down instruction
                    if ((move_grid[cur_r+1][cur_c] == 6)):
                        queue.append((cur_r+1, cur_c))
                        if(visited[cur_r+1][cur_c] == 0):
                            direction[cur_r+1][cur_c] = 4
                elif move_grid[cur_r][cur_c] == 6:
                    #move up, and say that the node came from up instruction
                    queue.append((cur_r-1, cur_c))
                    if(visited[cur_r-1][cur_c] == 0):
                        direction[cur_r-1][cur_c] = 2
                    
                    #move down
                    if(move_grid[cur_r+1][cur_c] == 6):
                        queue.append((cur_r+1, cur_c))
                        if(visited[cur_r+1][cur_c] == 0):
                            direction[cur_r+1][cur_c] = 4
                    #move left
                    if(move_grid[cur_r+1][cur_c-1] == 4):
                        queue.append((cur_r, cur_c-1))
                        if(visited[cur_r][cur_c-1] == 0):
                            direction[cur_r][cur_c-1] = 1
                    #move right
                    if(move_grid[cur_r+1][cur_c+1] ==4):
                        queue.append((cur_r, cur_c+1))
                        if(visited[cur_r][cur_c+1] == 0):
                            direction[cur_r][cur_c+1] = 3
            
            #now we update the current position, by accessing the current values of the next node to be explored
            cur_r = queue[0][0]
            cur_c = queue[0][1]

        #now we go back and add the path to the goal
        while(cur_r != startpos[0] or cur_c != startpos[1]):
            path.insert(0, direction[cur_r][cur_c])
            if path[0] == 1:
                cur_c = cur_c+1
            if path[0] == 2:
                cur_r = cur_r+1
            if path[0] == 3:
                cur_c = cur_c-1
            if path[0] == 4:
                cur_r = cur_r-1
        
        #now decode and print contents of path
        step = path[0]
        if step == 1:
            self.game.on_key_press(arcade.key.LEFT)
        if step == 2:
            self.game.on_key_press(arcade.key.UP)
        if step == 3:
            self.game.on_key_press(arcade.key.RIGHT)
        if step == 4:
            self.game.on_key_press(arcade.key.DOWN)
    #Here, we are returning the values at the states defined by the six state transition functions. The value is either -1 for inaccessible states or the value of the state
    def calc_Poss_Values(self, row, column):
        r = row
        c = column
        
        #Initialize all to negative one
        moveUp = moveRight = moveDown = moveLeft = moveJumpRight = moveJumpLeft = -1
        
        #make sure we are in bounds
        if r<12 and r>=0 and c<20 and c>= 0:
            
            #Up
            #Can only move up if we are on ladder
            if r>0 and self.move_grid[r][c] == 6:
                moveUp = self.value_grid[r-1][c]
            #Right
            #We can't move right when 1.To the right is the last column and 2. When we are on the ladder
            if c<18 and (self.move_grid[r][c] != 6 or (self.move_grid[r+1][c] in (2, 3, 4, 5, 6))):
                moveRight = self.value_grid[r][c+1]
            #Down
            #Can only move down when there is a ladder below us
            if r<11 and self.move_grid[r+1][c]==6:
                moveDown = self.value_grid[r+1][c]
            #Left
            #We can't move left when we are in the leftmost column or on the ladder
            if c>0 and (self.move_grid[r][c] != 6 or (self.move_grid[r+1][c] in (2, 3, 4, 5, 6))):
                moveLeft = self.value_grid[r][c-1]
            #Jump Right
            if c<17 and (self.move_grid[r][c] != 6 or (self.move_grid[r+1][c] in (2, 3, 4, 5, 6))):
                moveJumpRight = self.value_grid[r][c+2]
            #Jump Left
            if c>1 and (self.move_grid[r][c] != 6 or (self.move_grid[r+1][c] in (2, 3, 4, 5, 6))):
                moveJumpLeft = self.value_grid[r][c-2]
        return moveUp, moveRight, moveDown, moveLeft, moveJumpRight, moveJumpLeft
        
    def calc_Q(self):
        for r in range(12):
            for c in range(20):
            
                #Find all adjacent values based on the actions we can take. If one of the values is -1 it means we can't move there
                moveUp, moveRight, moveDown, moveLeft, moveJumpRight, moveJumpLeft = self.calc_Poss_Values(r, c)
                
                #Probability we make the correct move
                probC = 1 - self.noise
                #Probability of noise for any given direction
                probW = self.noise / 5.0
        
            #First check if the cell is inaccesible, if yes just ignore
                if self.previous_move_grid[r][c] == 0:
                    self.Q_grid[r][c] = [0, 0, 0, 0, 0, 0]
                    self.value_grid[r][c] = 0
                    continue
                #Second check if it's a terminal state
                elif self.previous_move_grid[r][c] == 2:
                    for i in range(6):
                        self.Q_grid[r][c][i] = self.reward_grid[r][c]
                    self.value_grid[r][c] = self.reward_grid[r][c]
                    continue
                #Now, Do Q values for all moveable cells
                else:
                    #0 = North
                    self.Q_grid[r][c][0] = 0.0
                    if moveUp != -1:
                        self.Q_grid[r][c][0] += (probC * (self.decay * moveUp))
                    elif moveUp == -1:
                        self.Q_grid[r][c][0] += self.livingreward
                    if moveRight != -1:
                        self.Q_grid[r][c][0] += (probW * (self.decay * moveRight))
                    if moveDown != -1:
                        self.Q_grid[r][c][0] += (probW * (self.decay * moveDown))
                    if moveLeft != -1:
                        self.Q_grid[r][c][0] += (probW * (self.decay * moveLeft))
                    if moveJumpRight != -1:
                        self.Q_grid[r][c][0] += (probW * (self.decay * moveJumpRight))
                    if moveJumpLeft != -1:
                        self.Q_grid[r][c][0] += (probW * (self.decay * moveJumpLeft))
                    
                    #1 = Right
                    self.Q_grid[r][c][1] = 0.0
                    if moveUp != -1:
                        self.Q_grid[r][c][1] += (probW * (self.decay * moveUp))
                    if moveRight != -1:
                        self.Q_grid[r][c][1] += (probC * (self.decay * moveRight))
                    elif moveRight == -1:
                        self.Q_grid[r][c][1] += self.livingreward
                    if moveDown != -1:
                        self.Q_grid[r][c][1] += (probW * (self.decay * moveDown))
                    if moveLeft != -1:
                        self.Q_grid[r][c][1] += (probW * (self.decay * moveLeft))
                    if moveJumpRight != -1:
                        self.Q_grid[r][c][1] += (probW * (self.decay * moveJumpRight))
                    if moveJumpLeft != -1:
                        self.Q_grid[r][c][1] += (probW * (self.decay * moveJumpLeft))
                        
                    #2 = Down
                    self.Q_grid[r][c][2] = 0.0
                    if moveUp != -1:
                        self.Q_grid[r][c][2] += (probW * (self.decay * moveUp))
                    if moveRight != -1:
                        self.Q_grid[r][c][2] += (probW * (self.decay * moveRight))
                    if moveDown != -1:
                        self.Q_grid[r][c][2] += (probC * (self.decay * moveDown))
                    elif moveDown == -1:
                         self.Q_grid[r][c][2] += self.livingreward
                    if moveLeft != -1:
                        self.Q_grid[r][c][2] += (probW * (self.decay * moveLeft))
                    if moveJumpRight != -1:
                        self.Q_grid[r][c][2] += (probW * (self.decay * moveJumpRight))
                    if moveJumpLeft != -1:
                        self.Q_grid[r][c][2] += (probW * (self.decay * moveJumpLeft))
                    
                    #3 = Left
                    self.Q_grid[r][c][3] = 0.0
                    if moveUp != -1:
                        self.Q_grid[r][c][3] += (probW * (self.decay * moveUp))
                    if moveRight != -1:
                        self.Q_grid[r][c][3] += (probW * (self.decay * moveRight))
                    if moveDown != -1:
                        self.Q_grid[r][c][3] += (probW * (self.decay * moveDown))
                    if moveLeft != -1:
                        self.Q_grid[r][c][3] += (probC * (self.decay * moveLeft))
                    elif moveLeft == -1:
                        self.Q_grid[r][c][3] += self.livingreward
                    if moveJumpRight != -1:
                        self.Q_grid[r][c][3] += (probW * (self.decay * moveJumpRight))
                    if moveJumpLeft != -1:
                        self.Q_grid[r][c][3] += (probW * (self.decay * moveJumpLeft))
                    
                    #4 = JumpRight
                    self.Q_grid[r][c][4] = 0.0
                    if moveUp != -1:
                        self.Q_grid[r][c][4] += (probW * (self.decay * moveUp))
                    if moveRight != -1:
                        self.Q_grid[r][c][4] += (probW * (self.decay * moveRight))
                    if moveDown != -1:
                        self.Q_grid[r][c][4] += (probW * (self.decay * moveDown))
                    if moveLeft != -1:
                        self.Q_grid[r][c][4] += (probW * (self.decay * moveLeft))
                    if moveJumpRight != -1:
                        self.Q_grid[r][c][4] += (probC * (self.decay * moveJumpRight))
                    elif moveJumpRight == -1:
                        self.Q_grid[r][c][4] += self.livingreward
                    if moveJumpLeft != -1:
                        self.Q_grid[r][c][4] += (probW * (self.decay * moveJumpLeft))
                    
                    #5 = JumpLeft
                    self.Q_grid[r][c][5] = 0.0
                    if moveUp != -1:
                        self.Q_grid[r][c][5] += (probW * (self.decay * moveUp))
                    if moveRight != -1:
                        self.Q_grid[r][c][5] += (probW * (self.decay * moveRight))
                    if moveDown != -1:
                        self.Q_grid[r][c][5] += (probW * (self.decay * moveDown))
                    if moveLeft != -1:
                        self.Q_grid[r][c][5] += (probW * (self.decay * moveLeft))
                    if moveJumpRight != -1:
                        self.Q_grid[r][c][5] += (probW * (self.decay * moveJumpRight))
                    if moveJumpLeft != -1:
                        self.Q_grid[r][c][5] += (probC * (self.decay * moveJumpLeft))
                    elif moveJumpLeft == -1:
                         self.Q_grid[r][c][5] +=self.livingreward
        pass
    def calc_PolicyEvaluation(self):
        for t in range (self.T):
            v_old = copy.deepcopy(self.value_grid)
            for r in range(12):
                for c in range(20):
                
                #Find all adjacent values based on the actions we can take. If one of the values is -1 it means we can't move there
                    moveUp, moveRight, moveDown, moveLeft, moveJumpRight, moveJumpLeft = self.calc_Poss_Values(r, c)

                    #Probability we make the correct move
                    probC = 1 - self.noise
                    #Probability of noise for any given direction
                    probW = self.noise / 5.0
                  
                
                #First check if the cell is inaccesible, if yes just ignore
                    if self.previous_move_grid[r][c] == 0:
                        self.Q_grid[r][c] = [0, 0, 0, 0, 0, 0]
                        self.value_grid[r][c] = 0
                        continue
                        
                    #Second check if it's a terminal state
                    elif self.previous_move_grid[r][c] == 2:
                        for i in range(6):
                            self.Q_grid[r][c][i] = self.reward_grid[r][c]
                        self.value_grid[r][c] = self.reward_grid[r][c]
                        continue
                    
                    #Now, Do Q values for all moveable cells
                    else:
                    #0 = North
                    
                        if self.policy_grid[r][c] == 0:
                            self.value_grid[r][c]= 0.0
                            if moveUp != -1:
                                self.value_grid[r][c] += (probC * (self.decay * moveUp))
                            elif moveUp == -1:
                                self.value_grid[r][c] += self.livingreward
                            if moveRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveRight))
                            if moveDown != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveDown))
                            if moveLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveLeft))
                            if moveJumpRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpRight))
                            if moveJumpLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpLeft))
                        
                        #1 = Right
                        elif self.policy_grid[r][c] == 1:
                            self.value_grid[r][c] = 0.0
                            if moveUp != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveUp))
                            if moveRight != -1:
                                self.value_grid[r][c] += (probC * (self.decay * moveRight))
                            elif moveRight == -1:
                                self.value_grid[r][c] += self.livingreward
                            if moveDown != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveDown))
                            if moveLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveLeft))
                            if moveJumpRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpRight))
                            if moveJumpLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpLeft))
                            
                        #2 = Down
                        elif self.policy_grid[r][c] == 2:
                            self.value_grid[r][c] = 0.0
                            if moveUp != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveUp))
                            if moveRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveRight))
                            if moveDown != -1:
                                self.value_grid[r][c] += (probC * (self.decay * moveDown))
                            elif moveDown == -1:
                                self.value_grid[r][c] += self.livingreward
                            if moveLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveLeft))
                            if moveJumpRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpRight))
                            if moveJumpLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpLeft))
                        
                        #3 = Left
                        elif self.policy_grid[r][c] == 3:
                            self.value_grid[r][c] = 0.0
                            if moveUp != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveUp))
                            if moveRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveRight))
                            if moveDown != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveDown))
                            if moveLeft != -1:
                                self.value_grid[r][c] += (probC * (self.decay * moveLeft))
                            elif moveLeft == -1:
                                self.value_grid[r][c] += self.livingreward
                            if moveJumpRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpRight))
                            if moveJumpLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpLeft))
                        
                        #4 = JumpRight
                        elif self.policy_grid[r][c] == 4:
                            self.value_grid[r][c] = 0.0
                            if moveUp != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveUp))
                            if moveRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveRight))
                            if moveDown != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveDown))
                            if moveLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveLeft))
                            if moveJumpRight != -1:
                                self.value_grid[r][c] += (probC * (self.decay * moveJumpRight))
                            elif moveJumpRight == -1:
                                self.value_grid[r][c] += self.livingreward
                            if moveJumpLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpLeft))
                        
                        #5 = JumpLeft
                        elif self.policy_grid[r][c] == 5:
                            self.value_grid[r][c] = 0.0
                            if moveUp != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveUp))
                            if moveRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveRight))
                            if moveDown != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveDown))
                            if moveLeft != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveLeft))
                            if moveJumpRight != -1:
                                self.value_grid[r][c] += (probW * (self.decay * moveJumpRight))
                            if moveJumpLeft != -1:
                                self.value_grid[r][c] += (probC * (self.decay * moveJumpLeft))
                            elif moveJumpLeft == -1:
                                self.value_grid[r][c] += self.livingreward
            if np.sum(np.abs(np.subtract(v_old, self.value_grid))) < self.epsilon:
                break
        pass
    def calc_PolicyImprovement(self):
        equal = True
        #copy old policy for comparison
        p_old = copy.deepcopy(self.policy_grid)
        
        #find q values for all states
        self.calc_Q()
        
        #now update policy based on highest q value for each state, and compare to see if policy has changed
        for r in range(12):
            for c in range(20):
                self.policy_grid[r][c] = self.Q_grid[r][c].index(max(self.Q_grid[r][c]))
                if (self.policy_grid[r][c] != p_old[r][c]):
                    equal = False
        return equal
    
    def doPolicyIteration(self):
        for t in range(self.T):
            self.calc_PolicyEvaluation()
            if(self.calc_PolicyImprovement()):
                break
        pass
    #We use this method to update the grid we are going to be iterating on
    def update_mdpGrid(self):
        #make our move grid for this round
        #0 means  we can't move there, 1 means we can move there, 2 means we die there or have reward there
        G = [[-1 for x in range(20)] for y in range(12)]
        dirtygrid = [[True for x in range(20)] for y in range(12)]
        
        for r in range(12):
            for c in range(20):
                if(G[r][c] == -1):
                    if(self.move_grid[r][c] in (2, 3, 4, 5)):
                        #i.e. if the spot is a platform, we can't be there
                        G[r][c] = 0
                        self.reward_grid[r][c] = 0
                    if(self.move_grid[r][c] == (6)):
                        G[r][c] = 1
                    if self.move_grid[r][c] == 1:
                        if c == 19:
                            #we can't access the last column in the grid
                            G[r][c] = 0
                            self.reward_grid[r][c] = 0
                        if r<11: #don't want to access out of bounds by accident
                            if (self.move_grid[r+1][c] not in (2, 3, 4, 5, 6)):
                                #we can't access spaces that don't have a platform below them(we can sometimes but we will overwrite this later)
                                G[r][c] = 0
                                self.reward_grid[r][c] = 0
                            else:
                                G[r][c] = 1
                                self.reward_grid[r][c] = 0
                    if (self.move_grid[r][c] in (8, 9, 10)):
                        #this is a reward state
                        if self.game.plat_grid[r][c].isActive:
                            G[r][c] = 2
                            if self.move_grid[r][c] == 8:
                                self.reward_grid[r][c] = 1
                            elif self.move_grid[r][c] == 9:
                                self.reward_grid[r][c] = 3
                            elif self.move_grid[r][c] == 10:
                                self.reward_grid[r][c] = 6
                        else:
                            G[r][c] = 1
                            self.reward_grid[r][c] = 0
                    #This is for the snakes
                    if self.move_grid[r][c] == 11:
                        G[r][c] = 1
                        self.reward_grid[r][c] = 0
#                    if self.kill_grid[r][c]:
#                        #if we are going to die in this spot it's a terminal spot
#                        G[r][c] = 2
#                        #################SUBJECT TO CHANGE###########################
#                        if self.move_grid[r][c] == 7:
#                            self.reward_grid[r][c] = -10
#                        #############################################################
#                        else:
#                            if c>0:
#                                self.reward_grid[r][c-1] = -5
#                                G[r][c-1] == 2
#                            if c<19:
#                                self.reward_grid[r][c+1] = -5
#                                G[r][c+1] = 2
#                            self.reward_grid[r][c] = -10
                    if self.move_grid[r][c] == 7:
                        G[r][c] = 2
                        self.reward_grid[r][c] = -5
                    for enemy in self.game.enemy_list:
                        if(enemy.isActive):
                            row, column = enemy.get_gridRC()
                            G[row][column] = 2
                            self.reward_grid[row][column] = -10
                            if enemy.isGoingLeft and c>0:
                                if self.tanuki_c != column-1 or self.tanuki_r != row:
                                    G[row][column-1] = 2
                                    self.reward_grid[row][column-1] = -.5
                            elif not enemy.isGoingLeft and c<19:
                                if self.tanuki_c != column+1 or self.tanuki_r != row:
                                    G[row][column+1] = 2
                                    self.reward_grid[row][column+1] = -.5
                    if self.move_grid[r][c] == 1:
                        #is this spot below also air?
                        if r<11: #don't want to access out of bounds by accident
                            if (self.move_grid[r+1][c] not in (2, 3, 4, 5, 6)):
                                #is there a platform within walking or jumping distance (can we somehow move to this position and fall)
                                # Do checks for out of bounds, and then assign a terminal state to death spots
                                if c > 0:
                                    if (self.move_grid[r+1][c-1] in (2, 3, 4, 5)):
                                        G[r][c] = 2
                                        self.reward_grid[r][c] = -5
                                    if c>1:
                                        if (self.move_grid[r+1][c-2] in (2, 3, 4, 5)):
                                            G[r][c] = 2
                                            self.reward_grid[r][c] = -5
                                if c<19:
                                    if (self.move_grid[r+1][c+1] in (2, 3, 4, 5)):
                                        G[r][c] = 2
                                        self.reward_grid[r][c] = -5
                                    if c<18:
                                        if (self.move_grid[r+1][c+2] in (2, 3, 4, 5)):
                                            G[r][c] = 2
                                            self.reward_grid[r][c] = -5

        
        #Now we need to check againt previous move grid and make our dirty grid, and also update the previous_move grid with our current
        for r in range(12):
            for c in range(20):
                if G[r][c] == self.previous_move_grid[r][c]:
                    dirtygrid[r][c] = True
                else:
                    dirtygrid[r][c] = False
                self.previous_move_grid[r][c] = G[r][c]
        
        #Now update our value grid. Idea is that we only need to change values that have changed between updates, minimizing policy convergence time.
        for r in range(12):
            for c in range(20):
                #if not dirtygrid[r][c]:
                #If cell is a terminal, then new value is just reward.
                if G[r][c] == 2:
                    self.value_grid[r][c] = self.reward_grid[r][c]
                #If cell is inaccesible, then new value is zero
                elif G[r][c] == 0:
                    self.value_grid[r][c] = 0
                #In the case that the cell has become moveable, we should update the value to 0
                elif G[r][c] == 1:
                    self.value_grid[r][c] = 0
        #Now we can do policy iteration
#        print("Move grid for this round")
#        print(np.matrix(self.move_grid))
#        print("Previous move grid(updated):")
#        print(np.matrix(self.previous_move_grid))
#        print("G Grid:")
#        print(np.matrix(G))
#        print("Dirty Grid:")
#        print(np.matrix(dirtygrid))
#        print("Reward Grid: ")
#        print(np.matrix(self.reward_grid))
#        print("Value Grid: ")
#        print(np.matrix(self.value_grid))
    
    
    def performStep(self):
        r = self.tanuki_r
        c = self.tanuki_c
        step = self.policy_grid[r][c]
        
        #Go up. We may have to press twice depending on our direction
        if step == 0:
            if not self.game.tanuki.isGoingUpDown:
                self.game.on_key_press(arcade.key.UP)
            self.game.on_key_press(arcade.key.UP)
        #Go right. We may have to press twice depending on our direction
        if step == 1:
            if (self.game.tanuki.isGoingLeft or self.game.tanuki.isGoingUpDown):
                self.game.on_key_press(arcade.key.RIGHT)
            self.game.on_key_press(arcade.key.RIGHT)
        #Go down, we may have to press twice....
        if step == 2:
            if not self.game.tanuki.isGoingUpDown:
                self.game.on_key_press(arcade.key.DOWN)
            self.game.on_key_press(arcade.key.DOWN)
        #Go left ...
        if step == 3:
            if not self.game.tanuki.isGoingLeft:
                self.game.on_key_press(arcade.key.LEFT)
            self.game.on_key_press(arcade.key.LEFT)
        #JumpRight ...
        if step == 4:
            if (self.game.tanuki.isGoingLeft or self.game.tanuki.isGoingUpDown):
                self.game.on_key_press(arcade.key.RIGHT)
            self.game.on_key_press(arcade.key.SPACE)
        #JumpLeft ...
        if step == 5:
            #print("Step is 5")
            if (not self.game.tanuki.isGoingLeft) or self.game.tanuki.isGoingUpDown:
                self.game.on_key_press(arcade.key.LEFT)
            self.game.on_key_press(arcade.key.SPACE)
        pass
    
    
    def ai_function(self):
        # To send a key stroke to the game, use self.game.on_key_press() method
        #self.bfs(self.move_grid, self.tanuki_r, self.tanuki_c, 8)
        start_time = time.time()
        self.update_mdpGrid()
        self.doPolicyIteration()
        print("Policy Grid:")
        pprint(self.policy_grid)
        print("Value Grid:")
        for x in range(12):
            print("")
            for y in range(20):
                print("{:.2f}".format(self.value_grid[x][y]), end = ", ")
        print("Q-Value Grid:")
        for x in range(12):
            print("")
            for y in range(20):
                print("[", end = "")
                for z in range(6):
                    print("{:.2f}".format(self.Q_grid[x][y][z]), end = ", ")
                print("], ", end = "")
#            print
        self.performStep()
        total_time = time.time() - start_time
        #print(f"Total time is: {total_time}")
        return

    def run(self):
        print("Starting " + self.name)

        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (50+320, 50)
#        if self.show_grid_info:
        pygame.init()
#        else:
#            pygame = []

        # Prepare grid information display (can be turned off if performance issue exists)
        if self.show_grid_info:
            screen_size = [200, 120]
            backscreen_size = [40, 12]

            screen = pygame.display.set_mode(screen_size)
            backscreen = pygame.Surface(backscreen_size)
            arr = pygame.PixelArray(backscreen)
        else:
            time.sleep(0.5)  # wait briefly so that main game can get ready

        # roughly every 50 milliseconds, retrieve game state (average human response time for visual stimuli = 25 ms)
        go = True
        while go and (self.game is not []):
            # Dispatch events from pygame window event queue
            if self.show_grid_info:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        go = False
                        break

            # RETRIEVE CURRENT GAME STATE
            self.move_grid, self.kill_grid, \
                self.isGameClear, self.isGameOver, self.current_stage, self.time_limit, \
                self.total_score, self.total_time, self.total_life, self.tanuki_r, self.tanuki_c \
                = self.game.get_game_state()
            
            self.ai_function()
            time.sleep(.05)
            #print(self.kill_grid)
            # Display grid information (can be turned off if performance issue exists)
            if self.show_grid_info:
                for row in range(12):
                    for col in range(20):
                        c = self.move_grid[row][col] * 255 / 12
                        arr[col, row] = (c, c, c)
                    for col in range(20, 40):
                        if self.kill_grid[row][col-20]:
                            arr[col, row] = (255, 0, 0)
                        else:
                            arr[col, row] = (255, 255, 255)

                pygame.transform.scale(backscreen, screen_size, screen)
                pygame.display.flip()

            # We must allow enough CPU time for the main game application
            # Polling interval can be reduced if you don't display the grid information
            time.sleep(0.05)

        print("Exiting " + self.name)


def main():
    ag = Agent(1, "My Agent", 1, True)
    ag.start()

    ag.game = game_core.GameMain()
    ag.game.set_location(50, 50)

    # Uncomment below for recording
    # ag.game.isRecording = True
    # ag.game.replay('replay.rpy')  # You can specify replay file name or it will be generated using timestamp

    # Uncomment below to replay recorded play
    # ag.game.isReplaying = True
    # ag.game.replay('replay.rpy')

    ag.game.reset()
    arcade.run()


if __name__ == "__main__":
    main()
