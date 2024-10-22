import gamelib
import random
import math
import warnings
from sys import maxsize
import json

#global enemyattack = []

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""




class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.enemyMP = []
        self.enemyMPallin = []
        self.turns = []
        self.enemyHP = []
        # Proud Attr
        self.last_spawning_loc = []
        self.enemy_HP_last = -1

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(
            game_state.turn_number))
        # Comment or remove this line to enable warnings.
        game_state.suppress_warnings(True)
        self.enemyHP.append(game_state.enemy_health)
        self.starter_strategy(game_state)
        self.enemy_HP_last = game_state.enemy_health
        
        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """
    def left_right(self, game_state):
        left_turret_locations = [(y, 14) for y in range(8)] + [(y, 15) for y in range(8)] + [(y, 16) for y in range(8)]
        right_turret_locations = [(y, 14) for y in range(20, 28)] + [(y, 15) for y in range(20, 28)] + [(y, 16) for y in range(20, 28)]
        
        # Check left half for upgraded turrets
        left_upgraded_turret_found = False
        for location in left_turret_locations:
            unit = game_state.contains_stationary_unit(location)
            if unit and unit.unit_type == TURRET and unit.upgraded:
                left_upgraded_turret_found = True
                break
        
        # Check right half for upgraded turrets
        right_upgraded_turret_found = False
        for location in right_turret_locations:
            unit = game_state.contains_stationary_unit(location)
            if unit and unit.unit_type == TURRET and unit.upgraded:
                right_upgraded_turret_found = True
                break

        if not left_upgraded_turret_found:
            game_state.attempt_spawn(DEMOLISHER, [2, 11], 1000)
            game_state.attempt_spawn(SUPPORT, [5,10], 1)
            game_state.attempt_upgrade([5,10])
        
        elif not right_upgraded_turret_found:
            game_state.attempt_spawn(DEMOLISHER, [25, 11], 1000)
            game_state.attempt_spawn(SUPPORT, [22,10], 1)
            game_state.attempt_upgrade([22,10])

        else:
            tup = self.least_damage_spawn_location(game_state, [[2, 11], [25,11]])
            if not tup: loc = [2, 11]
            else: loc = tup[0]
            if loc[0] == 2: x = 5
            else: x = 22
            game_state.attempt_spawn(DEMOLISHER, loc, 1000)
            game_state.attempt_spawn(SUPPORT, [x, 10], 1)
            game_state.attempt_upgrade([x, 10])



    def find_location(self, game_state):
        
        scout_spawn_location_options =[[3,10],[4,9], [5,8], [6,7], [7,6], [8,5], [9,4], [10,3], [11,2], [12,1], [13,0], [14,0],[15,1], [16,2], [17,3], [18,4], [19,5], [20,6], [21,7],[22,8],[23,9],[24,10]]
        
        tup = self.least_damage_spawn_location(
            game_state, scout_spawn_location_options)
        
        if not tup:
            self.send_scouts(game_state)
            return
        
        best_location, best_damage = tup
        
        if best_damage > 400:
            self.left_right(game_state)
        else:
            self.send_scouts(game_state)

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout.
        We will place turrets and walls as part of our initial setup.
        For offense, we will use scouts every two turns to try and score quickly.
        """
        # First, place basic defenses
        

        if game_state.turn_number < 2: pass
        elif game_state.turn_number == 2:
            self.left_right(game_state)
            
        elif game_state.turn_number < 10 :
            if game_state.turn_number % 3 == 1:
                self.send_scouts(game_state)
                # self.find_location(game_state)
        elif game_state.turn_number < 30:
            if game_state.turn_number % 3 == 1:
                self.send_scouts(game_state)
                # self.find_location(game_state)
        else:
            if game_state.turn_number % 4 == 1:
                self.send_scouts(game_state)
                # self.find_location(game_state)

        self.build_defences(game_state)
        self.build_reactive_defense(game_state)

    def layer1(self, game_state):

        unit_locations = [[TURRET, 13,13], [TURRET, 4,13],[TURRET, 5,13],[TURRET, 22,13], [TURRET, 23,13], [TURRET, 14,13]]
        for unit in unit_locations:
            x, y = unit[1:]
            if game_state.turn_number > 0 and len(game_state.game_map[x, y]) == 0:
                self.reinforce_location(game_state, [x, y])
            game_state.attempt_spawn(unit[0], unit[1:])
            game_state.attempt_upgrade(unit[1:])

        wall_locations = [[0,13],[27,13],[10,12],[9,12],[11,12], [16,12],[17,12],[18,12]]

        # game_state.attempt_spawn(WALL, wall_locations)
        
    def build_reactive_defense(self, game_state):
        for location in self.scored_on_locations:
            if location[0] < 14:
                self.reinforce_location(game_state, [4, 12])
                self.reinforce_location(game_state, [13, 13])
            else:
                self.reinforce_location(game_state, [23, 12])
                self.reinforce_location(game_state, [13, 13])


    def build_defences(self, game_state):
        """

        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
 
        initial_tower_locations = [[3,12], [24,12],[10,12], [17,12],[4,12],[23,12]]
        initial_walls_locations = [[2, 13], [25, 13], [4, 12], [23, 12]]
        upgrade_locations = [ [4, 15],[23, 15], [4, 12], [23, 12]]

        self.layer1(game_state)
        self.restall_low_health(game_state)

    def restall_low_health(self, game_state):
        low_health_threshold = 0.5
        for i in range(28):
            for j in range(28):
                loc = [i, j]
                if game_state.game_map.in_arena_bounds(loc):
                    for unit in game_state.game_map[i, j]:
                        if unit.health < unit.max_health * low_health_threshold and unit.unit_type == TURRET:
                            game_state.attempt_remove(loc)
                            self.reinforce_location(game_state, loc)

    def reinforce_location(self, game_state, loc):
        illegal_locs = [[0,13],[1,13],[26,13],[27,13]]
        i, j = loc
        neigh = [[i+1,j],[i-1,j]]
        if 9 <= i <= 17:
            neigh.append([i, j-1])
        for n in neigh:
            if n in illegal_locs: continue
            if game_state.game_map.in_arena_bounds(n):
                game_state.attempt_spawn(TURRET,n)
                game_state.attempt_upgrade(n)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(
            friendly_edges, game_state)

        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    # custom method
    def send_scouts(self, game_state):
        """
        Send out scouts at random locations to defend our base from enemy moving units.
        """

        scout_spawn_location_options =[[3,10],[4,9], [5,8], [6,7], [7,6], [8,5], [9,4], [10,3], [11,2], [12,1], [13,0], [14,0],[15,1], [16,2], [17,3], [18,4], [19,5], [20,6], [21,7],[22,8],[23,9],[24,10]]
        
        best_location, _ = self.least_damage_spawn_location(
            game_state, scout_spawn_location_options)
        
        if not best_location:
            game_state.attempt_spawn(DEMOLISHER, [24, 10], 4)
            game_state.attempt_spawn(SCOUT, [13, 0], 6)
            return

        x,y = best_location

        neigh = [[x+1,y-1],[x+1,y],[x-1,y-1],[x-1,y],[x,y-1]]
        for n in neigh:
            if game_state.game_map.in_arena_bounds(n):
                game_state.attempt_spawn(SUPPORT, n, 1)
                game_state.attempt_remove(n)

        game_state.attempt_spawn(SCOUT, best_location, 1000)

    def damage_estimated_from_spawn_location(self, game_state, location):
        gamelib.debug_write("location: {}".format(location))
        damage = 0
        path = game_state.find_path_to_edge(location)
        if path and any(path):
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * \
                    gamelib.GameUnit(TURRET, game_state.config).damage_i
        return damage

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        if not location_options or not any(location_options):
            return location_options

        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path and any(path):
                for path_location in path:
                    for attacker in game_state.get_attackers(path_location, 0):
                        if attacker.unit_type == TURRET:
                            damage += attacker.damage_i
            damages.append(damage)

        if not damages or not any(damages):
            return None
        
        return location_options[damages.index(min(damages))], min(damages)

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write(
                    "All locations: {}".format(self.scored_on_locations))


        
        

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()