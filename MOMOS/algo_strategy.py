import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from concurrent.futures import ProcessPoolExecutor

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

import numpy as np
import multiprocessing

def compute_damage(args):
    """Compute total damage for a given spawn location."""


    location, game_state = args


    path = game_state.find_path_to_edge(location)
    damage = 0
    if path:
        for path_location in path:
            for attacker in game_state.get_attackers(path_location, 0):
                if attacker.unit_type == TURRET:
                    damage += attacker.damage_i
    
    return [location, damage]

def least_damage_spawn_location_parallel(game_state, locations):
    """Finds the spawn location with the least damage using parallel processing."""
    with multiprocessing.Pool(processes=8) as pool:  # Adjust based on available cores
        results = pool.map(compute_damage, [(loc, game_state) for loc in locations])

    # Find the location with the minimum total damage
    best_location = min(results, key=lambda x: x[1])
    
    return best_location




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
        self.last_spawning_loc = [13, 0]
        self.enemy_HP_last = -1
        self.I_am_dome = False

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
        self.starter_strategy(game_state)
        
        game_state.submit_turn()


    def attempt_spwan_remove(self, game_state, unit, location):
        if game_state.attempt_spawn(unit, location):
            game_state.attempt_remove(location)
            return True
        return False


    def set_supports(self, game_state):
        locations = [[1,12],[2,11]]
        for location in locations:
            game_state.attempt_spawn(SUPPORT, location)
            game_state.attempt_upgrade(location)
    
    def set_supports1(self, game_state):
        locations = [[3,10]]
        for location in locations:
            game_state.attempt_spawn(SUPPORT, location)
            if game_state.turn_number > 0:
                game_state.attempt_upgrade(location)



    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout.
        We will place turrets and walls as part of our initial setup.
        For offense, we will use scouts every two turns to try and score quickly.
        """

        if self.I_am_dome:
            l = [[13,0],[14,0]]
            a,b = self.least_damage_spawn_location(game_state, l)
            if a == [13,0]:
                self.sucidal_scouts(game_state)
            else:
                self.sucidal_scouts1(game_state)
            
        elif game_state.turn_number < 10:
            self.send_scouts(game_state)

        elif game_state.turn_number < 15:                
            if game_state.turn_number % 2 == 1:
                self.send_scouts(game_state)
        elif game_state.turn_number < 30:
                
            if game_state.turn_number % 3 == 1:
                self.send_scouts(game_state)
        else:
            if game_state.turn_number % 4 == 1:
                self.send_scouts(game_state)


        
    
        self.build_reactive_defense(game_state)
        self.set_supports(game_state)
        self.set_supports1(game_state)
        self.build_defences(game_state)


        #difference of my and opponent health
        if (game_state.enemy_health - game_state.my_health > 8 and game_state.my_health < 16 ) or game_state.enemy_health < 6 or game_state.my_health < 11:
            self.remove_all(game_state)
            self.I_am_dome = True
        elif game_state.my_health - game_state.enemy_health > 7 and self.I_am_dome:
            self.I_am_dome = False
            self.remove_all(game_state)
        

    def layer1(self, game_state):

        unit_locations = [[TURRET, 13,12], [TURRET, 22,12], [TURRET, 23,12], [TURRET, 14,12], [TURRET, 3,12]]
        
        unit_locations1 = [[TURRET, 1,13],[TURRET, 0,13],[TURRET, 2,12],[TURRET, 3,11],[TURRET, 4,10]]
        for unit in unit_locations1:
            x, y = unit[1:]
            if game_state.get_resource(MP) < game_state.type_cost(TURRET)[MP]:
                break
            if game_state.turn_number > 0 and len(game_state.game_map[x, y]) == 0:
                self.reinforce_location(game_state, [x, y])
            game_state.attempt_spawn(unit[0], [x, y])

        for unit in unit_locations:
            x, y = unit[1:]
            if game_state.get_resource(MP) < game_state.type_cost(TURRET)[MP]:
                break
            if game_state.turn_number > 0 and len(game_state.game_map[x, y]) == 0:
                self.reinforce_location(game_state, [x, y])
            self.attempt_spwan_remove(game_state, unit[0], [x, y])

        # wall_locations = [[13,13],[4,13],[5,13],[22,13],[23,13],[14,13]] 

        # game_state.attempt_spawn(WALL, wall_locations)
        #game_state.attempt_upgrade(wall_locations)
        
    def build_reactive_defense(self, game_state):
        l = self.scored_on_locations[::-1]
        for location in l:
            if game_state.get_resource(MP) < game_state.type_cost(TURRET)[MP]:
                return
            self.reinforce_location(game_state, location)



    def build_defences(self, game_state):
        """

        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
 
        initial_tower_locations = [[3,12], [24,12],[10,12], [17,12],[4,12],[23,12]]
        initial_walls_locations = [[2, 13], [25, 13], [4, 12], [23, 12]]
        upgrade_locations = [ [4, 15],[23, 15], [4, 12], [23, 12]]

        self.layer1(game_state)
        # self.restall_low_health(game_state)

    def restall_low_health(self, game_state):
        low_health_threshold = 0.7
        for i in range(28):
            for j in range(28):
                loc = [i, j]
                if game_state.game_map.in_arena_bounds(loc):
                    for unit in game_state.game_map[i, j]:
                        if unit.health < unit.max_health * low_health_threshold and unit.unit_type == TURRET:
                            game_state.attempt_remove(loc)
                            self.reinforce_location(game_state, loc)


    def remove_all(self, game_state):
        for i in range(28):
            for j in range(28):
                loc = [i, j]
                game_state.attempt_remove(loc)

    def sucidal_scouts(self, game_state):
        l = [[1,12],[2,11],[3,10],[4,9],[5,8],[6,7],[7,6],[8,5],[9,4],[10,3],[11,2],[12,1],[13,0]]

        game_state.attempt_spawn(SUPPORT, l)
        game_state.attempt_upgrade(l)
        x = game_state.attempt_spawn(SCOUT, [14,0], 1000)
        if x:
            self.last_spawning_loc = [14, 0]
        x = game_state.attempt_spawn(SCOUT, [15,1], 1000)
        if x:
            self.last_spawning_loc = [15, 1]

    def sucidal_scouts1(self, game_state):
        l = [[14,0],[15,1],[16,2],[17,3],[18,4],[19,5],[20,6],[21,7],[22,8],[23,9],[24,10],[25,11],[26,12],[27,13]]

        game_state.attempt_spawn(SUPPORT, l)
        game_state.attempt_upgrade(l)
        x = game_state.attempt_spawn(SCOUT, [13,0], 1000)
        if x:
            self.last_spawning_loc = [13, 0]
        x = game_state.attempt_spawn(SCOUT, [12,1], 1000)
        if x:
            self.last_spawning_loc = [12, 1]
        
        



    def reinforce_location(self, game_state, loc):
        illegal_locs = [[1,12],[26,12]]
        i, j = loc
        

        if 2 < i < 14:
            i +=2
        elif i < 25:
            i-=2

        if j < 5:
            j=5
        elif j < 10:
            j+=2

        neigh = [[i,j+2],[i+2,j]]
        if i > 13:
            neigh = [[i,j+2],[i-2,j]]
        if 9 <= i <= 17:
            neigh.append([i, j-1])
        
        neigh.append([i, j])
        
        path = game_state.find_path_to_edge(self.last_spawning_loc)

        if path:
            for n in neigh:
                if game_state.get_resource(MP) < game_state.type_cost(TURRET)[MP]:
                    break
                if n in path:
                    continue
                game_state.attempt_spawn(TURRET, n)
            # game_state.attempt_spawn(TURRET,n)
        


    # custom method
    def send_scouts(self, game_state):
        """
        Send out scouts at random locations to defend our base from enemy moving units.
        """

        scout_spawn_location_options =[[7,6], [8,5], [9,4],[14,0],[15,1], [16,2], [17,3]]
        scout_spawn_location_options = scout_spawn_location_options[::-1]
        best_location, _ = self.least_damage_spawn_location(
            game_state, scout_spawn_location_options)
        
        if not best_location:
            x = game_state.attempt_spawn(SCOUT, [13, 0], 60)
            if x:
                self.last_spawning_loc = [13, 0]
            return

        x,y = best_location

        # neigh = [[x+1,y-1],[x+1,y],[x-1,y-1],[x-1,y],[x,y-1]]
        # for n in neigh:
        #     if game_state.game_map.in_arena_bounds(n):
        #         game_state.attempt_spawn(SUPPORT, n, 1)
        #         game_state.attempt_remove(n)

        x = game_state.attempt_spawn(SCOUT, best_location, 1000)
        if x:
            self.last_spawning_loc = best_location  







    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.


        EXPENSIVE METHOD
        """
        # return least_damage_spawn_location_parallel(game_state, location_options)
        damages = []
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
            if damage == 0:
                return location, damage

        if not damages:
            return None, None
        
        return location_options[damages.index(min(damages))], min(damages)
    

    def reset_with_temporary_supports(self, game_state):
        """
        Removes all existing deployments, allocates all resources to supports,
        and immediately removes those supports to prepare for complete reallocation
        in the next turn.
        
        Returns:
            Dictionary with operation statistics
        """
        # Step 1: Identify and remove all existing structures
        existing_structures = []
        for x in range(game_state.ARENA_SIZE):
            for y in range(game_state.HALF_ARENA):
                location = [x, y]
                if (game_state.game_map.in_arena_bounds(location) and 
                        game_state.contains_stationary_unit(location)):
                    existing_structures.append(location)
        
        removed_count = game_state.attempt_remove(existing_structures)
        
        # Step 2: Calculate how many supports we can build
        support_cost = game_state.type_cost(SUPPORT)
        sp_available = game_state.get_resource(SP)
        num_supports = math.floor(sp_available / support_cost[SP])
        
        # Step 3: Find valid locations for supports (prioritize back rows)
        support_locations = []
        for y in range(game_state.HALF_ARENA-1, 0, -1):  # Start from back row
            for x in range(game_state.ARENA_SIZE):
                location = [x, y]
                if (game_state.game_map.in_arena_bounds(location) and 
                        game_state.can_spawn(SUPPORT, location)):
                    support_locations.append(location)
                    if len(support_locations) >= num_supports:
                        break
            if len(support_locations) >= num_supports:
                break
        
        # Step 4: Deploy supports and immediately remove them
        deployed_supports = []
        for location in support_locations[:num_supports]:
            success = game_state.attempt_spawn(SUPPORT, location)
            if success:
                deployed_supports.append(location)
                # Queue this support for immediate removal
                game_state.attempt_remove(location)
        
        gamelib.debug_write(f"Reset board: Removed {removed_count} structures, " 
                        f"deployed and removed {len(deployed_supports)} supports")
        
        return {
            "structures_removed": removed_count,
            "supports_deployed_and_removed": len(deployed_supports)
        }


    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
    
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