import arcade
import game_core
import threading
import time
import os
import pygame
import numpy


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
    def bfs(self, move_grid, cur_r, cur_c, target):
        visited = numpy.zeros_like(move_grid)
        direction = numpy.zeros_like(move_grid)
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
    def ai_function(self):
        # To send a key stroke to the game, use self.game.on_key_press() method
        self.bfs(self.move_grid, self.tanuki_r, self.tanuki_c, 8)
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
            time.sleep(.05)
            self.ai_function()

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
